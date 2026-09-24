"""Resolve `find` leaves against the case's artifact set. Deterministic; prefers `indeterminate` over
`satisfied` whenever the source cannot vouch for what it did not return."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ophi.cdm.models import (
    ArtifactType, AssertionPayload, Availability, Case, ChartArtifact, ExtractedDetailPayload,
    NotePayload, PSRPayload, PerioChartPayload, RadiographPayload, RadiographView, Section, TxPlanPayload,
)
from ophi.dental import notation, sextants
from ophi.engine import recency
from ophi.engine.models import SEVERITY, EvidenceRef, LeafResult, Shortfall, StaleItem, Status
from ophi.rules.schema import AssertionCriterion, Find

SECTION_OF: dict[ArtifactType, Section] = {
    ArtifactType.RADIOGRAPH: Section.IMAGING,
    ArtifactType.PHOTO: Section.IMAGING,
    ArtifactType.PERIO_CHART: Section.PERIO,
    ArtifactType.PSR: Section.PERIO,
    ArtifactType.PERIO_MEASUREMENTS: Section.PERIO,
    ArtifactType.CLINICAL_NOTE: Section.NOTES,
    ArtifactType.TX_PLAN_DETAILS: Section.NOTES,
    ArtifactType.TX_PLAN: Section.PLANNED,
}


@dataclass
class LeafContext:
    case: Case
    criteria: dict[str, AssertionCriterion]
    near_miss_why: str | None = None  # the requirement's own near-miss sentence, from the pack
    demanded_sextants: list[str] = field(default_factory=list)  # set by a fired escalation


def label_of(a: ChartArtifact) -> str:
    p = a.payload
    if isinstance(p, RadiographPayload):
        if p.view == RadiographView.BW:
            side = p.laterality.value if p.laterality else ("/".join(sorted({notation.side(t) for t in p.teeth_fdi})) or "")
            return f"{side} BW".strip()
        if len(p.teeth_fdi) <= 2 and p.teeth_fdi:
            return f"{p.view.value} of " + ", ".join(f"#{t}" for t in p.teeth_fdi)
        return p.view.value
    if isinstance(p, PerioChartPayload):
        return f"perio chart ({p.point_count} sites)"
    if isinstance(p, PSRPayload):
        return "PSR " + " ".join(f"{s}={v if v is not None else '–'}" for s, v in sorted(p.scores.items()))
    if isinstance(p, NotePayload):
        return f"clinical note{' — ' + p.note_type if p.note_type else ''}"
    if isinstance(p, ExtractedDetailPayload):
        return f"{p.claim} (from {p.source_artifact_id})"
    if isinstance(p, AssertionPayload):
        return f"assertion {p.criterion_id}: {p.value}"
    return a.type.value


def evidence_ref(a: ChartArtifact, as_of: date, months: int | None) -> EvidenceRef:
    r = recency.check(a.captured_at, as_of, months) if months else None
    p = a.payload
    return EvidenceRef(
        artifact_id=a.artifact_id, type=a.type.value, label=label_of(a), captured_at=a.captured_at,
        age_days=r.age_days if r else None, expires_on=r.expires_on if r else None,
        extraction_method=a.provenance.extraction_method, teeth_fdi=a.teeth_fdi,
        confirmed=not a.is_unconfirmed_extraction,
        quote=p.quote if isinstance(p, ExtractedDetailPayload) else None,
    )


def resolve(f: Find, ctx: LeafContext) -> LeafResult:
    if f.artifact_type == ArtifactType.CLINICIAN_ASSERTION:
        return _resolve_assertion(f, ctx)
    if f.artifact_type == ArtifactType.PERIO_CHART and f.completeness == "complete":
        return _resolve_complete_perio(f, ctx)
    if f.artifact_type == ArtifactType.PSR:
        return _resolve_psr(f, ctx)
    if f.artifact_type == ArtifactType.PERIO_MEASUREMENTS:
        return _resolve_perio_measurements(f, ctx)
    if f.artifact_type == ArtifactType.RADIOGRAPH and f.laterality:
        return _resolve_bilateral(f, ctx)
    return _resolve_generic(f, ctx)


# --- helpers ------------------------------------------------------------------------------------


def _absent(f: Find, ctx: LeafContext, what: str, near_miss: str | None = None) -> LeafResult:
    """No candidate matched: absent-confirmed is a gap; unknown source visibility is indeterminate."""
    section = SECTION_OF.get(f.artifact_type)
    sa = ctx.case.assurance_for(section) if section else None
    sf = Shortfall(missing=[what], near_miss=near_miss)
    if sa and sa.availability in (Availability.UNKNOWN, Availability.DEGRADED):
        sf.detail = f"driver reports {section.value} as {sa.availability.value}" + (f": {sa.reason}" if sa.reason else "")
        return LeafResult(status=Status.INDETERMINATE, shortfall=sf,
                          detail=f"no {what} found, and the source cannot confirm the section is complete ({sa.availability.value}). Absent and unseen are different conclusions.")
    return LeafResult(status=Status.UNSATISFIED, shortfall=sf, detail=f"no {what} on record" + (f". {near_miss}" if near_miss else ""))


def _usable(a: ChartArtifact) -> bool:
    p = a.payload
    if isinstance(p, ExtractedDetailPayload) and p.rejected:
        return False
    if isinstance(p, PerioChartPayload) and not p.certified:
        return False
    if isinstance(p, NotePayload) and not p.signed_off:
        return False
    return True


def _pick_by_recency(cands: list[ChartArtifact], f: Find, ctx: LeafContext, what: str) -> LeafResult:
    """From candidates already filtered on everything but date, choose the freshest usable one."""
    as_of = ctx.case.as_of
    months = f.recency.months if f.recency else None
    if not months:
        best = sorted(cands, key=lambda a: (a.captured_at or date.min), reverse=True)[0]
        return _finish(best, f, ctx, what, None)

    within, at_risk, stale, undated = [], [], [], []
    for a in cands:
        r = recency.check(a.captured_at, as_of, months)
        {"within": within, "at_risk": at_risk, "stale": stale, "indeterminate": undated}[r.status].append((a, r))
    if within:
        a, r = max(within, key=lambda ar: ar[0].captured_at)  # type: ignore[arg-type]
        return _finish(a, f, ctx, what, r)
    if at_risk:
        a, r = max(at_risk, key=lambda ar: ar[0].captured_at)  # type: ignore[arg-type]
        res = _finish(a, f, ctx, what, r)
        if res.status == Status.SATISFIED:
            res.status = Status.AT_RISK
        res.detail = r.detail
        return res
    sf = Shortfall(
        stale=[StaleItem(artifact_id=a.artifact_id, label=label_of(a), captured_at=a.captured_at, age_days=r.age_days, over_by_days=r.over_by_days)  # type: ignore[arg-type]
               for a, r in sorted(stale, key=lambda ar: ar[0].captured_at, reverse=True)],  # type: ignore[arg-type,return-value]
        undated=[label_of(a) for a, _ in undated],
    )
    if undated and not stale:
        return LeafResult(status=Status.INDETERMINATE, shortfall=sf,
                          detail=f"{what} on record but without a capture date; recency cannot be established (never inferred from the import date)")
    newest = sf.stale[0]
    return LeafResult(status=Status.UNSATISFIED, shortfall=sf,
                      detail=f"most recent {what} is dated {newest.captured_at}, {newest.age_days} days before {as_of}; {months}-month bound exceeded by {newest.over_by_days} day{'' if newest.over_by_days == 1 else 's'}")


def _finish(a: ChartArtifact, f: Find, ctx: LeafContext, what: str, r: recency.RecencyResult | None) -> LeafResult:
    ref = evidence_ref(a, ctx.case.as_of, f.recency.months if f.recency else None)
    if a.is_unconfirmed_extraction:
        return LeafResult(status=Status.PENDING_CONFIRMATION, matched=[ref],
                          shortfall=Shortfall(pending_confirmation=[ref.label]),
                          detail=f"{what} proposed from free text ({a.provenance.extraction_method}); a human must confirm before this counts")
    detail = r.detail if r else f"{label_of(a)} on record"
    return LeafResult(status=Status.SATISFIED, matched=[ref], expires_on=r.expires_on if r else None, detail=detail)


def _radiographs(ctx: LeafContext, view: RadiographView | None) -> list[ChartArtifact]:
    out = []
    for a in ctx.case.artifacts_of(ArtifactType.RADIOGRAPH):
        p = a.payload
        assert isinstance(p, RadiographPayload)
        if view is None or p.view == view:
            out.append(a)
    return out


# --- leaf kinds ---------------------------------------------------------------------------------


def _resolve_generic(f: Find, ctx: LeafContext) -> LeafResult:
    tooth = ctx.case.requested_tooth
    cands = [a for a in ctx.case.artifacts_of(f.artifact_type) if _usable(a)]
    if f.artifact_type == ArtifactType.TX_PLAN:
        # Footnote 1 wants the plan that covers this treatment, not any plan on file.
        code = ctx.case.treatment.code
        named = [a for a in cands if isinstance(a.payload, TxPlanPayload) and code in a.payload.pending_codes]
        if cands and not named:
            return LeafResult(status=Status.UNSATISFIED, shortfall=Shortfall(missing=[f"treatment plan naming {code}"]),
                              detail=f"a treatment plan is on record but none lists {code} as pending")
        cands = named
    if f.view:
        cands = [a for a in cands if isinstance(a.payload, RadiographPayload) and a.payload.view == f.view]
    what = f"{f.view.value if f.view else f.artifact_type.value.replace('_', ' ')}"
    near_miss = None
    if f.for_tooth == "requested":
        by_tooth = [a for a in cands if tooth in a.teeth_fdi]
        what = f"{what} of #{tooth}"
        if not by_tooth and f.artifact_type == ArtifactType.RADIOGRAPH and f.view == RadiographView.PA:
            near_miss = _bitewing_near_miss(ctx, tooth)
        cands = by_tooth
    if not cands:
        return _absent(f, ctx, what, near_miss)
    return _pick_by_recency(cands, f, ctx, what)


def _bitewing_near_miss(ctx: LeafContext, tooth: int) -> str | None:
    """The demo sentence: a bitewing exists for the tooth but it does not image the apex."""
    bws = [a for a in _radiographs(ctx, RadiographView.BW) if tooth in a.teeth_fdi and a.captured_at]
    if not bws:
        return None
    bw = max(bws, key=lambda a: a.captured_at)  # type: ignore[arg-type,return-value]
    if not ctx.near_miss_why:
        return None
    return ctx.near_miss_why.replace("{bw_date}", str(bw.captured_at)).replace("{tooth}", str(tooth))


def _resolve_bilateral(f: Find, ctx: LeafContext) -> LeafResult:
    """Right AND left views, each within recency. Reports exactly which side is missing or stale."""
    cands = [a for a in _radiographs(ctx, f.view) if _usable(a)]
    if not cands:
        return _absent(f, ctx, f"{f.view.value} radiographs (right and left)")
    sides: dict[str, list[ChartArtifact]] = {"right": [], "left": []}
    for a in cands:
        p = a.payload
        assert isinstance(p, RadiographPayload)
        lat = p.laterality.value if p.laterality else None
        if lat in ("right", "both"):
            sides["right"].append(a)
        if lat in ("left", "both"):
            sides["left"].append(a)
        if lat is None and p.teeth_fdi:  # derive side from imaged teeth when the source did not say
            for s in {notation.side(t) for t in p.teeth_fdi}:
                sides[s].append(a)

    results: dict[str, LeafResult] = {}
    for s in f.laterality or []:
        results[s] = _pick_by_recency(sides[s], f, ctx, f"{f.view.value}-{s}") if sides[s] else \
            LeafResult(status=Status.UNSATISFIED, shortfall=Shortfall(missing=[f"{f.view.value}-{s}"]), detail=f"no {s} {f.view.value} on record")

    matched = [m for r in results.values() for m in r.matched]
    sf = Shortfall()
    for r in results.values():
        sf.missing += r.shortfall.missing
        sf.stale += r.shortfall.stale
        sf.undated += r.shortfall.undated
    worst = max(results.values(), key=lambda r: SEVERITY[r.status])
    expires = min((r.expires_on for r in results.values() if r.expires_on), default=None)
    parts = [f"{s}: {r.detail}" for s, r in results.items()]
    return LeafResult(status=worst.status, matched=matched, shortfall=sf, expires_on=expires, detail="; ".join(parts))


def _resolve_complete_perio(f: Find, ctx: LeafContext) -> LeafResult:
    case = ctx.case
    present = set(case.dentition.present_teeth(notation.ALL_FDI_PERMANENT))
    charts = [a for a in case.artifacts_of(ArtifactType.PERIO_CHART) if _usable(a)]
    if not charts:
        return _absent(f, ctx, "periodontal chart")

    complete, incomplete = [], []
    for a in charts:
        p = a.payload
        assert isinstance(p, PerioChartPayload)
        six_site = {t.tooth_fdi for t in p.teeth if t.sites_measured == 6}
        missing = sorted(present - six_site)
        (complete if not missing else incomplete).append((a, missing, p))
    if complete:
        return _pick_by_recency([a for a, _, _ in complete], f, ctx, "complete periodontal chart")

    a, missing, p = max(incomplete, key=lambda t: t[0].captured_at or date.min)
    sites_mode = max((t.sites_measured for t in p.teeth), default=0)
    sf = Shortfall(incomplete={"artifact_id": a.artifact_id, "captured_at": str(a.captured_at), "point_count": p.point_count,
                               "sites_per_tooth": sites_mode, "teeth_without_6_sites": missing,
                               "requested_tooth_charted": case.requested_tooth in six_site_of(p)})
    if sites_mode < 6:
        detail = (f"perio chart dated {a.captured_at} records {sites_mode} sites per tooth ({p.point_count} points); "
                  f"CDCP requires 6 measurements per tooth on all present teeth")
    else:
        detail = (f"perio chart dated {a.captured_at} is missing 6-site measurements for {len(missing)} present teeth "
                  f"({', '.join(f'#{t}' for t in missing[:8])}{'…' if len(missing) > 8 else ''})")
    return LeafResult(status=Status.UNSATISFIED, matched=[evidence_ref(a, case.as_of, f.recency.months if f.recency else None)],
                      shortfall=sf, detail=detail)


def six_site_of(p: PerioChartPayload) -> set[int]:
    return {t.tooth_fdi for t in p.teeth if t.sites_measured == 6}


def _resolve_psr(f: Find, ctx: LeafContext) -> LeafResult:
    cands = [a for a in ctx.case.artifacts_of(ArtifactType.PSR) if _usable(a)]
    if not cands:
        return _absent(f, ctx, "PSR")
    if f.coverage == "all_sextants":
        full = []
        for a in cands:
            p = a.payload
            assert isinstance(p, PSRPayload)
            missing = [s for s in sextants.ALL_SEXTANTS if p.scores.get(s) is None]
            if not missing:
                full.append(a)
            else:
                partial_note = f"PSR dated {a.captured_at} lacks scores for {', '.join(missing)}"
        if not full:
            return LeafResult(status=Status.UNSATISFIED, shortfall=Shortfall(missing=["PSR for every sextant"], detail=partial_note), detail=partial_note)
        cands = full
    return _pick_by_recency(cands, f, ctx, "PSR (all sextants)")


def _resolve_perio_measurements(f: Find, ctx: LeafContext) -> LeafResult:
    """Six-site measurements for the requested tooth (and, if an escalation demanded it, its sextant),
    taken from any perio chart or partial charting on record."""
    case = ctx.case
    need = {case.requested_tooth}
    for s in ctx.demanded_sextants:
        need |= set(case.dentition.present_teeth(sextants.teeth_in(s)))
    charts = [a for a in case.artifacts_of(ArtifactType.PERIO_CHART, ArtifactType.PERIO_MEASUREMENTS) if _usable(a)]
    if not charts:
        return _absent(f, ctx, f"6-site measurements for #{case.requested_tooth}")
    good = []
    for a in charts:
        p = a.payload
        if isinstance(p, PerioChartPayload) and all(p.sites_for(t) >= (f.sites_per_tooth or 6) for t in need):
            good.append(a)
    what = f"6-site measurements for #{case.requested_tooth}" + (f" and sextant {', '.join(ctx.demanded_sextants)}" if ctx.demanded_sextants else "")
    if not good:
        return LeafResult(status=Status.UNSATISFIED, shortfall=Shortfall(missing=[what]), detail=f"no charting with {what} on record")
    return _pick_by_recency(good, f, ctx, what)


def _resolve_assertion(f: Find, ctx: LeafContext) -> LeafResult:
    crit = ctx.criteria[f.criterion]  # type: ignore[index]
    hits = [a for a in ctx.case.artifacts_of(ArtifactType.CLINICIAN_ASSERTION)
            if isinstance(a.payload, AssertionPayload) and a.payload.criterion_id == f.criterion]
    if not hits:
        return LeafResult(status=Status.INDETERMINATE, shortfall=Shortfall(missing_assertions=[f.criterion]),  # type: ignore[list-item]
                          detail=f"awaiting the treating dentist's confirmation: {crit.label}")
    a = max(hits, key=lambda x: x.payload.asserted_at)  # type: ignore[attr-defined]
    p = a.payload
    assert isinstance(p, AssertionPayload)
    ref = evidence_ref(a, ctx.case.as_of, None)
    ref.captured_at = p.asserted_at.date()
    who = f"{p.asserted_by} on {p.asserted_at.date()}"
    if p.value == "not_met":
        return LeafResult(status=Status.UNSATISFIED, matched=[ref], shortfall=Shortfall(not_met_assertions=[f.criterion]),  # type: ignore[list-item]
                          detail=f"{who} recorded that this criterion is not met: {crit.label}")
    verb = "recorded as not applicable" if p.value == "not_applicable" else "confirmed"
    return LeafResult(status=Status.SATISFIED, matched=[ref], detail=f"{who} {verb}: {crit.label}")
