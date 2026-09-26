"""A charted case -> the export shape past requests come in (`cdcp-preauth-export/2`), so a case the clinic
hasn't sent yet reaches Laya through the same `training_set.request_text` it was fine-tuned on.

Every field the clinic sends (`training_set.SENT`) is built, so the fixer can featurize it too. Ophi's drafted
narrative is left out: training requests carry the clinic's own short narrative or none, and a long one would
crowd the note out of 512 tokens.
"""

from __future__ import annotations

from dateutil.relativedelta import relativedelta

from ophi.cdm.models import ArtifactType, Case, ChartArtifact, NotePayload, PerioChartPayload, PSRPayload, RadiographPayload
from ophi.dental import notation
from ophi.dental.sextants import sextant_of

AGE_BANDS = [(0, "0-17"), (18, "18-64"), (65, "65-69"), (70, "70-74"), (75, "75-86"), (87, "87+")]


def to_export(case: Case) -> dict:
    tooth, as_of = case.requested_tooth, case.as_of
    t = case.treatment
    plan = _latest(case.artifacts_of(ArtifactType.TX_PLAN))
    return {
        "submission_channel": "cdanet_eclaim",  # Ophi's packets go out through the PMS
        "submitted_date": as_of.isoformat(),
        "member": {"member_id": case.patient.patient_id, "age_band": _age_band(case)},
        "provider": {"provider_id": t.provider.licence or t.provider.name},
        "services": [{"procedure_code": t.code, "tooth": str(tooth), "lab_codes": list(t.lab_codes)}],
        "attachments": _attachments(case),
        "perio_summary": _perio_summary(case),
        "treatment_plan": {"pending": [{"code": c, "tooth": tooth if c == t.code else _tooth_for(case, c, "planned")} for c in plan.payload.pending_codes],
                           "completed": [{"code": c, "tooth": _tooth_for(case, c, "completed")} for c in plan.payload.completed_codes]} if plan else None,
        "prior_history": {"same_code_last_5y": _same_code_within(case, years=5), "same_tooth_crown_months_ago": _prior_crown_months(case),
                          "previous_preauth_ids": []},
        "clinical_notes": _note_text(case),
        "narrative": None,
    }


def _latest(arts: list[ChartArtifact]) -> ChartArtifact | None:
    dated = [a for a in arts if a.captured_at]
    return max(dated, key=lambda a: a.captured_at) if dated else (arts[-1] if arts else None)


def _age_band(case: Case) -> str:
    dob = case.patient.dob
    age = relativedelta(case.as_of, dob).years if dob else 18
    return next(band for low, band in reversed(AGE_BANDS) if age >= low)


def _attachments(case: Case) -> list[dict]:
    tooth = case.requested_tooth
    films = [(a, a.payload) for a in case.artifacts_of(ArtifactType.RADIOGRAPH) if a.captured_at]
    out = []
    pa = _latest([a for a, p in films if isinstance(p, RadiographPayload) and p.view.value == "PA" and tooth in p.teeth_fdi])
    if pa:
        out.append({"type": "periapical_radiograph", "count": 1, "captured_date": pa.captured_at.isoformat()})
    # A bitewing pair is only as current as its older side.
    sides = {}
    for a, p in films:
        if p.view.value == "BW":
            key = p.laterality.value if p.laterality else a.artifact_id
            if key not in sides or a.captured_at > sides[key].captured_at:
                sides[key] = a
    if sides:
        out.append({"type": "bitewing_radiographs", "count": min(len(sides), 2),
                    "captured_date": min(a.captured_at for a in sides.values()).isoformat()})
    perio = _latest(case.artifacts_of(ArtifactType.PERIO_CHART, ArtifactType.PSR))
    if perio and perio.captured_at:
        out.append({"type": "periodontal_charting", "count": 1, "captured_date": perio.captured_at.isoformat()})
    note = _latest(case.artifacts_of(ArtifactType.CLINICAL_NOTE))
    if note:
        out.append({"type": "clinical_notes", "count": 1, "captured_date": (note.captured_at or case.as_of).isoformat()})
    return out


def _perio_summary(case: Case) -> dict | None:
    """'complete' is a six-site chart of every present tooth, as in the crown exports; anything less reads as
    PSR only. With no PSR on file, each sextant's code is implied by its deepest pocket (PSR bands: 4 over
    5.5 mm, 3 from 3.5 mm). Bleeding and calculus aren't charted, so a shallow sextant reads as 2."""
    tooth = case.requested_tooth
    chart = _latest(case.artifacts_of(ArtifactType.PERIO_CHART))
    psr = _latest(case.artifacts_of(ArtifactType.PSR))
    if not chart and not psr:
        return None
    pl = chart.payload if chart else None
    assert pl is None or isinstance(pl, PerioChartPayload)
    present = len(case.dentition.present_teeth(notation.ALL_FDI_PERMANENT))
    complete = pl is not None and pl.point_count >= present * 6
    if psr:
        assert isinstance(psr.payload, PSRPayload)
        scores = {s: v for s, v in psr.payload.scores.items() if v is not None}
    else:
        deepest: dict[str, int] = {}
        for t in pl.teeth:
            depths = [d for d in t.depths_mm if d is not None]
            if depths:
                s = sextant_of(t.tooth_fdi)
                deepest[s] = max(deepest.get(s, 0), *depths)
        scores = {s: 4 if d >= 6 else 3 if d >= 4 else 2 for s, d in deepest.items()}
    mine = next((t for t in pl.teeth if t.tooth_fdi == tooth), None) if complete else None
    return {
        "chart_type": "complete" if complete else "psr_only",
        "captured_date": (chart if complete else (psr or chart)).captured_at.isoformat(),
        "psr": scores,
        "tooth_sites_mm": [d for d in mine.depths_mm if d is not None] if mine else [],
        "bop_at_tooth": any(mine.bleeding) if mine and mine.bleeding else False,
        "furcation_class": mine.furcation if mine and mine.furcation else None,
    }


def _prior_crown_months(case: Case) -> int | None:
    done = [h.performed_on for h in case.procedure_history
            if h.status == "completed" and h.tooth_fdi == case.requested_tooth and h.code.startswith("27")]
    if not done:
        return None
    gap = relativedelta(case.as_of, max(done))
    return gap.years * 12 + gap.months


def _tooth_for(case: Case, code: str, status: str) -> int | None:
    """A plan lists codes only; the chart's history says which tooth (a root canal on the crown tooth matters)."""
    rows = [h for h in case.procedure_history if h.status == status and h.code == code]
    return max(rows, key=lambda h: h.performed_on).tooth_fdi if rows else None


def _same_code_within(case: Case, years: int) -> bool:
    since = case.as_of - relativedelta(years=years)
    return any(h.status == "completed" and h.code == case.treatment.code and h.performed_on >= since for h in case.procedure_history)


def _note_text(case: Case) -> str:
    """The notes about the requested tooth, oldest first; with none, the chart's latest three."""
    notes = sorted((a for a in case.artifacts_of(ArtifactType.CLINICAL_NOTE) if isinstance(a.payload, NotePayload)),
                   key=lambda a: a.captured_at or case.as_of)
    about = [a for a in notes if case.requested_tooth in a.payload.teeth_fdi] or notes[-3:]
    return " ".join(a.payload.text.strip() for a in about) or "(no notes)"
