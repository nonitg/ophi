"""Boolean solver over the requirement grammar. Same inputs -> byte-identical output.

`require_all` takes the worst status; `one_of` takes the best and, when nothing passes, reports the
cheapest near-miss rather than a list of failures. Escalations are evaluated first, in precedence
order, because a fired escalation can change what a leaf demands (PSR 3 in the requested tooth's
sextant -> that whole sextant must be charted).
"""

from __future__ import annotations

from colombus.cdm.models import ArtifactType, Case, PSRPayload
from colombus.dental import sextants
from colombus.engine import facts, leaves, recency
from colombus.engine.leaves import LeafContext
from colombus.engine.models import (
    SEVERITY, EscalationResult, EvidenceRef, LeafResult, RequirementResult, Shortfall, Status,
)
from colombus.rules.schema import (
    EFFORT_ORDER, Escalation, EscalationWhen, Fact, FindP, NotEscalated, OneOf, Option, Predicate,
    ProvidedByPacket, Requirement, RequireAll, RulePack,
)


def applies(req: Requirement, case: Case) -> bool:
    aw = req.applies_when
    if aw is None:
        return True
    if aw.tooth_has_endo_history is not None:
        if case.tooth_is_endo_treated() != aw.tooth_has_endo_history:
            return False
    if aw.treatment_has_lab_codes is not None and bool(case.treatment.lab_codes) != aw.treatment_has_lab_codes:
        return False
    return True


def evaluate_requirement(req: Requirement, case: Case, pack: RulePack) -> RequirementResult:
    if not applies(req, case):
        return RequirementResult(requirement_id=req.id, label=req.label, clause=req.clause, status=Status.NOT_APPLICABLE,
                                 applicable=False, explanation=f"{req.id}: does not apply to this case")
    ctx = LeafContext(case=case, criteria=pack.assertion_criteria, near_miss_why=req.gap.near_miss_why)
    esc_results, fired = _evaluate_escalations(req.escalations, case)
    for e, er in zip(req.escalations, esc_results):
        if er.fired and e.demand == "sextant_perio_charting" and er.scope:
            ctx.demanded_sextants = er.scope.get("sextants", [])

    res, via, risk, near = _solve(req.satisfied_by, ctx, fired, pack)
    expl = f"Rule {req.id} v{pack.version} — {req.clause.source} {req.clause.ref}: {res.detail}"
    near_title = None
    if near is not None and near.gap_title:
        near_title = near.gap_title.replace("{missing}", "; ".join(res.shortfall.missing) or "the missing charting")
    return RequirementResult(
        requirement_id=req.id, label=req.label, clause=req.clause, status=res.status, satisfied_via=via,
        evidence=res.matched, shortfall=res.shortfall, escalations_evaluated=esc_results, risk_reason=risk,
        explanation=expl, detail=res.detail, near_miss_option=near.id if near else None, near_miss_title=near_title,
        expires_on=res.expires_on,
    )


# --- solver -------------------------------------------------------------------------------------


Solved = tuple[LeafResult, str | None, str | None, "Option | None"]  # result, satisfied_via, risk_reason, near-miss option


def _solve(p: Predicate, ctx: LeafContext, fired: dict[str, EscalationResult], pack: RulePack) -> Solved:
    if isinstance(p, ProvidedByPacket):
        ref = EvidenceRef(artifact_id="packet:claim_form", type="claim_form", label="computer-generated treatment form (rendered by Colombus)",
                          extraction_method="packet")
        return LeafResult(status=Status.SATISFIED, matched=[ref], detail="rendered from the PMS treatment plan at packet assembly; staff submit it"), None, None, None
    if isinstance(p, FindP):
        return leaves.resolve(p.find, ctx), None, None, None
    if isinstance(p, Fact):
        return facts.resolve(p, ctx.case, pack), None, None, None
    if isinstance(p, NotEscalated):
        er = fired.get(p.not_escalated)
        if er is None:
            return LeafResult(status=Status.SATISFIED, detail=f"escalation {p.not_escalated} did not fire"), None, None, None
        return LeafResult(status=Status.UNSATISFIED, shortfall=Shortfall(detail=er.detail), detail=er.detail), None, None, None
    if isinstance(p, RequireAll):
        return _solve_all(p, ctx, fired, pack), None, None, None
    if isinstance(p, OneOf):
        return _solve_one_of(p, ctx, fired, pack)
    raise TypeError(f"unknown predicate {type(p)}")


def _solve_all(p: RequireAll, ctx: LeafContext, fired: dict[str, EscalationResult], pack: RulePack) -> LeafResult:
    parts = [_solve(q, ctx, fired, pack)[0] for q in p.require_all]
    worst = max(parts, key=lambda r: SEVERITY[r.status])
    sf = Shortfall()
    for r in parts:
        sf.missing += r.shortfall.missing
        sf.stale += r.shortfall.stale
        sf.undated += r.shortfall.undated
        sf.pending_confirmation += r.shortfall.pending_confirmation
        sf.missing_assertions += r.shortfall.missing_assertions
        sf.not_met_assertions += r.shortfall.not_met_assertions
        sf.incomplete = sf.incomplete or r.shortfall.incomplete
        sf.near_miss = sf.near_miss or r.shortfall.near_miss
    matched = [m for r in parts for m in r.matched]
    expires = min((r.expires_on for r in parts if r.expires_on), default=None)
    failing = [r.detail for r in parts if SEVERITY[r.status] >= SEVERITY[Status.AT_RISK] and r.detail]
    detail = _join_details(failing if failing else [r.detail for r in parts if r.detail])
    return LeafResult(status=worst.status, matched=matched, shortfall=sf, expires_on=expires, detail=detail)


AWAITING = "awaiting the treating dentist's confirmation: "


def _join_details(details: list[str]) -> str:
    """Seven 'awaiting confirmation' leaves read as one line, not seven."""
    awaiting = [d[len(AWAITING):] for d in details if d.startswith(AWAITING)]
    other = [d for d in details if not d.startswith(AWAITING)]
    if len(awaiting) > 1:
        other.append(f"awaiting the treating dentist's confirmation on {len(awaiting)} criteria: {'; '.join(awaiting)}")
    elif awaiting:
        other.append(AWAITING + awaiting[0])
    return "; ".join(other)


def _solve_one_of(p: OneOf, ctx: LeafContext, fired: dict[str, EscalationResult], pack: RulePack) -> Solved:
    results = []
    for opt in p.one_of:
        r = _solve(opt.predicate(), ctx, fired, pack)[0]
        if r.status == Status.SATISFIED and opt.confers_status == "at_risk":
            r.status = Status.AT_RISK
        results.append((opt, r))
    # Best option wins; ties broken by declaration order (deterministic).
    best_opt, best = min(results, key=lambda t: (SEVERITY[t[1].status], p.one_of.index(t[0])))
    if best.status in (Status.SATISFIED, Status.AT_RISK, Status.PENDING_CONFIRMATION):
        return best, best_opt.id, (best_opt.risk_reason if best.status == Status.AT_RISK else None), None
    # Nothing passes: report the cheapest, closest near-miss, but keep the union of what was tried.
    # A fired escalation that demands one of these options has already chosen the path (footnote 7:
    # PSR 4, or 3 in two sextants, closes the PSR path) — cost must not steer staff back onto it.
    demanded = {er.demanded for er in fired.values()} & {o.id for o in p.one_of}
    pool = [(o, r) for o, r in results if o.id in demanded] if demanded else results
    # A path with evidence already on record (a 4-point chart, a PSR) is a near-miss; a path with
    # nothing toward it is a from-scratch alternative. Prefer near-misses, then effort, then distance.
    cheapest_opt, cheapest = min(pool, key=lambda t: (0 if t[1].matched else 1, EFFORT_ORDER[t[0].remediation_cost],
                                                       t[1].shortfall.distance, p.one_of.index(t[0])))
    cheapest.detail = f"{cheapest_opt.label}: {cheapest.detail}" + "".join(
        f" | {o.label}: {r.detail}" for o, r in results if o is not cheapest_opt and r.detail)
    if any(r.status == Status.INDETERMINATE for _, r in results) and cheapest.status == Status.UNSATISFIED:
        # A sibling option could not be decided; do not call the whole requirement a confirmed gap.
        cheapest.status = Status.INDETERMINATE
    return cheapest, None, None, cheapest_opt


# --- escalations --------------------------------------------------------------------------------


def _evaluate_escalations(escs: list[Escalation], case: Case) -> tuple[list[EscalationResult], dict[str, EscalationResult]]:
    scores = _latest_psr_scores(case)
    results, fired = [], {}
    for e in sorted(escs, key=lambda e: -e.precedence):
        if scores is None:
            results.append(EscalationResult(id=e.id, fired=False, detail="no PSR within 12 months to evaluate"))
            continue
        hit, matched = _when(e.when, scores, case.requested_tooth)
        if hit:
            scope = {"sextants": matched}
            detail = e.message.format(matched=", ".join(f"{s}={scores[s]}" for s in matched))
            er = EscalationResult(id=e.id, fired=True, detail=detail, demanded=e.demand, scope=scope)
            fired[e.id] = er
        else:
            mx = max((v for v in scores.values() if v is not None), default=None)
            er = EscalationResult(id=e.id, fired=False, detail=f"Not triggered. Max PSR {mx}; scores {', '.join(f'{s}={v}' for s, v in sorted(scores.items()))}.")
        results.append(er)
    return results, fired


def _latest_psr_scores(case: Case) -> dict[str, int | None] | None:
    psrs = [a for a in case.artifacts_of(ArtifactType.PSR) if a.captured_at
            and recency.check(a.captured_at, case.as_of, 12).status in ("within", "at_risk")]
    if not psrs:
        return None
    a = max(psrs, key=lambda x: x.captured_at)  # type: ignore[arg-type,return-value]
    assert isinstance(a.payload, PSRPayload)
    return a.payload.scores


def _when(w: EscalationWhen, scores: dict[str, int | None], tooth: int) -> tuple[bool, list[str]]:
    if w.any:
        for sub in w.any:
            hit, m = _when(sub, scores, tooth)
            if hit:
                return True, m
        return False, []
    target = [sextants.sextant_of(tooth)] if w.in_sextant_of_requested_tooth else sextants.ALL_SEXTANTS
    matched = []
    for s in target:
        v = scores.get(s)
        if v is None:
            continue
        if w.psr_score_gte is not None and v >= w.psr_score_gte:
            matched.append(s)
        elif w.psr_score_eq is not None and v == w.psr_score_eq:
            matched.append(s)
    return len(matched) >= w.min_sextants, matched

