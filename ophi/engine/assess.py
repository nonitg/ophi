"""Assess one case against one rule pack. Deterministic apart from `assessed_at`."""

from __future__ import annotations

import hashlib
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from ophi.cdm.models import Case
from ophi.engine.evaluate import evaluate_requirement
from ophi.engine.models import (
    SEVERITY, Action, Assessment, Deadline, RequirementResult, RulesetRef, ScheduleResult, Shortfall, Status, Verdict, Workload,
)
from ophi.rules.schema import EFFORT_ORDER, Requirement, RulePack

if TYPE_CHECKING:
    from ophi.outcomes.weights import Weights

ENGINE_VERSION = "0.1.0"

NOTES = [
    "Ophi checks documentation completeness against the cited CDCP rules. It makes no statement about how the payer will decide.",
    "Sun Life processes preauthorizations first-come, first-processed; a resubmission enters the queue as a new request (Health Canada CDCP preauthorization guidance). Avoid duplicate submissions for the same case.",
    "Health Canada reported that more than 95% of preauthorizations were processed within 7 days as of 2026-05-31 (CDCP statistics).",
]


def assess(case: Case, pack: RulePack, weights: Weights | None = None, skipped: frozenset[str] = frozenset()) -> Assessment:
    """`skipped`: requirement ids whose chart gaps a test run treats as fixed (see `_skip`)."""
    t0 = time.perf_counter()
    sched = check_schedule(case, pack)
    if sched.disposition in ("not_required", "excluded"):
        # No crown preauthorization rule applies; evaluating the crown requirements would invent gaps.
        results = [RequirementResult(requirement_id=r.id, label=r.label, clause=r.clause, status=Status.NOT_APPLICABLE,
                                     applicable=False, explanation=f"{r.id}: not evaluated — {sched.detail}") for r in pack.requirements]
    else:
        results = [evaluate_requirement(r, case, pack) for r in pack.requirements]
    results = [_skip(r) if r.requirement_id in skipped else r for r in results]
    verdict = decide(sched, results)
    if weights and weights.pack_version != pack.version:
        weights = None  # lift measured against another pack's requirements says nothing about this one
    actions = rank_actions(results, pack, sched, case, weights.lift if weights else {})
    deadlines = sorted(
        (Deadline(artifact_id=e.artifact_id, label=e.label, expires_on=e.expires_on, requirement_id=r.requirement_id)
         for r in results if r.status in (Status.SATISFIED, Status.AT_RISK) for e in r.evidence if e.expires_on),
        key=lambda d: (d.expires_on, d.requirement_id, d.artifact_id))
    applicable = [r for r in results if r.applicable]
    satisfied = [r for r in applicable if r.status == Status.SATISFIED and not r.skipped]
    elapsed = int((time.perf_counter() - t0) * 1000)

    weights_hash = weights.content_hash if weights else None
    digest = hashlib.sha256((case.model_dump_json() + (pack.content_hash or "") + (weights_hash or "") + ",".join(sorted(skipped))).encode()).hexdigest()[:16]
    return Assessment(
        assessment_id=f"asm_{digest}",
        case_id=case.case_id,
        ruleset=RulesetRef(id=pack.id, version=pack.version, content_hash=pack.content_hash or "", effective_from=pack.effective_from,
                           weights_hash=weights_hash),
        assessed_at=datetime.now(UTC),
        submission_date_assumed=case.as_of,
        engine_version=ENGINE_VERSION,
        schedule=sched,
        verdict=verdict,
        completeness={"satisfied": len(satisfied), "applicable": len(applicable)},
        requirements=results,
        actions=actions,
        deadlines=deadlines,
        notes=list(NOTES),
        workload=Workload(
            artifacts_scanned=len(case.artifacts) + len(case.procedure_history),
            requirements_evaluated=len(applicable),
            subsystems_read=sorted({s.value for s in case.assurance}),
            elapsed_ms=elapsed,
        ),
    )


def _skip(r: RequirementResult) -> RequirementResult:
    """Test runs only: treat the chart gap as fixed, with no evidence to ship. The dentist's own criteria still
    wait for the dentist, and a criterion they recorded as not met stands."""
    sf = r.shortfall
    if not r.applicable or r.status in (Status.SATISFIED, Status.AT_RISK) or sf.not_met_assertions:
        return r
    if sf.missing_assertions:
        return r.model_copy(update={"status": Status.INDETERMINATE, "skipped": True, "evidence": [],
                                    "shortfall": Shortfall(missing_assertions=sf.missing_assertions)})
    return r.model_copy(update={"status": Status.SATISFIED, "skipped": True, "evidence": [], "shortfall": Shortfall(),
                                "satisfied_via": None, "risk_reason": None})


def check_schedule(case: Case, pack: RulePack) -> ScheduleResult:
    code = case.treatment.code
    s = pack.schedule
    for fam in s.excluded_families:
        if code.startswith(fam.prefix):
            return ScheduleResult(disposition="excluded", preauth_required=None, clause=fam.clause,
                                  detail=f"{code} falls under '{fam.label}', listed in {fam.clause.ref} as an exclusion. Exclusions are not open to reconsideration.")
    if code in s.preauth_always:
        return ScheduleResult(disposition="preauth_required", preauth_required=True,
                              detail=f"{code} is in Schedule B ({s.family_label}) on the {pack.jurisdiction.province} {pack.jurisdiction.provider_type.upper()} {pack.jurisdiction.grid_year} grid; preauthorization is always required.")
    if code.startswith(s.family_prefix):
        return ScheduleResult(disposition="not_in_schedule_b", preauth_required=None,
                              detail=f"{code} is a {s.family_label.lower()} code but is not in the Schedule B crown list ({', '.join(s.preauth_always)}) on the {pack.jurisdiction.grid_year} grid. The grid is the authority: confirm the code before submitting.")
    return ScheduleResult(disposition="not_required", preauth_required=False,
                          detail=f"{code} is outside this pack's scope ({s.family_label}); no preauthorization rule in this pack applies.")


def decide(sched: ScheduleResult, results: list[RequirementResult]) -> Verdict:
    if sched.disposition == "excluded":
        return Verdict.EXCLUDED_AS_CODED
    if sched.disposition == "not_required":
        return Verdict.PREAUTH_NOT_REQUIRED
    statuses = {r.status for r in results if r.applicable}
    if Status.UNSATISFIED in statuses:
        return Verdict.BLOCKED
    if Status.INDETERMINATE in statuses or Status.PENDING_CONFIRMATION in statuses or sched.disposition == "not_in_schedule_b":
        return Verdict.NEEDS_INPUT
    if Status.AT_RISK in statuses:
        return Verdict.READY_WITH_RISKS
    return Verdict.READY_TO_SUBMIT


def rank_actions(results: list[RequirementResult], pack: RulePack, sched: ScheduleResult, case: Case,
                 lift: dict[str, float] | None = None) -> list[Action]:
    """Deterministic order: blocking first; within blocking, evidence that is actually missing or stale
    (unsatisfied) before things a human only has to confirm (indeterminate / pending); then the action
    that unblocks most; then cheapest effort; then the gap most associated with past denials (`lift`);
    then requirement id as the final tiebreak so identical runs never reorder."""
    lift = lift or {}
    raw: list[tuple[int, int, int, int, float, str, Action]] = []
    if sched.disposition == "not_required":
        return []  # the crown requirements are informational only
    if sched.disposition == "excluded":
        return [Action(rank=1, blocking=True, effort="clinical", action_type="excluded_code",
                       title="Procedure code falls under a listed CDCP exclusion", why=sched.detail, unblocks=["schedule"])]
    if sched.disposition == "not_in_schedule_b":
        a = Action(rank=0, blocking=True, effort="confirm_in_app", action_type="confirm_code",
                   title="Confirm the procedure code against the CDCP grid", why=sched.detail, unblocks=["schedule"])
        raw.append((0, 0, -1, EFFORT_ORDER["confirm_in_app"], 0.0, "0_schedule", a))
    for r in results:
        if not r.applicable or r.status == Status.SATISFIED:
            continue
        req = pack.requirement(r.requirement_id)
        a = _action_for(r, req, case)
        raw.append((0 if a.blocking else 1, -SEVERITY[r.status], -len(a.unblocks), EFFORT_ORDER.get(a.effort, 99),
                    -lift.get(r.requirement_id, 0.0), r.requirement_id, a))
    raw.sort(key=lambda t: t[:6])
    out = []
    for i, t in enumerate(raw, start=1):
        t[6].rank = i
        out.append(t[6])
    return out


def _fill(text: str, case: Case) -> str:
    return text.replace("{tooth}", str(case.requested_tooth))


def _sentence(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _plural(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def _action_for(r: RequirementResult, req: Requirement, case: Case) -> Action:
    sf = r.shortfall
    if r.status == Status.AT_RISK:
        return Action(rank=0, blocking=False, effort=req.gap.effort, action_type="review_risk",
                      title=f"Review risk: {req.label}", why=r.risk_reason or _sentence(r.detail) or req.gap.why or "", unblocks=[r.requirement_id])
    if r.status == Status.PENDING_CONFIRMATION:
        return Action(rank=0, blocking=True, effort="confirm_in_app", action_type="confirm_extraction",
                      title=f"Confirm: {sf.pending_confirmation[0]}" if sf.pending_confirmation else "Confirm proposed evidence",
                      why="Proposed from the note text; the engine only counts evidence a human has confirmed.", unblocks=[r.requirement_id])
    if sf.not_met_assertions:
        return Action(rank=0, blocking=True, effort="clinical", action_type="criterion_not_met",
                      title=f"Dentist recorded a criterion as not met: {req.label}",
                      why=_sentence(r.detail), unblocks=[r.requirement_id])
    only_assertions_missing = sf.missing_assertions and not (sf.missing or sf.stale or sf.undated or sf.incomplete)
    if only_assertions_missing:
        n = len(sf.missing_assertions)
        title = f"Dentist to confirm {_plural(n, 'criterion', 'criteria')}: {req.label}" if n > 1 else f"Dentist to confirm: {req.label}"
        return Action(rank=0, blocking=True, effort="confirm_in_app", action_type="assert", title=title,
                      why=req.gap.why or "", unblocks=[r.requirement_id])
    if r.status == Status.INDETERMINATE:
        why = _sentence(r.detail)
        if sf.detail and sf.detail.startswith("driver reports"):
            title = f"Check the imaging software: {req.label[0].lower() + req.label[1:]}"
            return Action(rank=0, blocking=True, effort="reuse_existing", action_type="check_source", title=title,
                          why=why, unblocks=[r.requirement_id])
        if sf.undated:
            return Action(rank=0, blocking=True, effort="confirm_in_app", action_type="establish_date",
                          title=f"Establish the capture date of the {sf.undated[0]}", why=why, unblocks=[r.requirement_id])
        return Action(rank=0, blocking=True, effort="confirm_in_app", action_type="resolve_unknown",
                      title=f"Cannot verify: {req.label}", why=why, unblocks=[r.requirement_id])
    title = _fill(r.near_miss_title or req.gap.title, case)
    why = req.gap.why or ""
    if sf.near_miss:
        why = sf.near_miss
    elif sf.stale:
        s = sf.stale[0]
        why = f"The most recent {s.label} is dated {s.captured_at}, {_plural(s.age_days, 'day', 'days')} before submission ({_plural(s.over_by_days, 'day', 'days')} past the 12-month bound). " + why
    elif sf.incomplete and sf.incomplete.get("sites_per_tooth", 6) < 6:
        why = f"The perio chart dated {sf.incomplete['captured_at']} records {sf.incomplete['sites_per_tooth']} sites per tooth; CDCP requires 6 measurements per tooth. " + why
    elif sf.detail and not sf.missing:
        why = f"{_sentence(r.detail)}. " + why
    elif sf.missing and sf.missing_assertions:
        # The fact that failed is the action; the dentist's pending answers are a separate action.
        why = f"{r.detail.split('; awaiting')[0]}. " + why
    return Action(rank=0, blocking=True, effort=req.gap.effort, action_type=req.gap.action_type, title=title, why=_sentence(why),
                  unblocks=[r.requirement_id], needs_patient=req.gap.needs_patient)
