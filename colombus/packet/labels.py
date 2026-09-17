"""Human-readable labels for artifacts, shared by the narrative, the index, and the preview.

Labels are built from the artifact itself, never from engine `detail` strings, which contain
computed dates (window boundaries) that do not exist in the chart and would fail grounding.
"""

from __future__ import annotations

from datetime import date

from colombus.cdm.models import (
    ArtifactType, Case, ChartArtifact, ExtractedDetailPayload, NotePayload, PerioChartPayload, PSRPayload,
    RadiographPayload, RadiographView, TxPlanPayload,
)
from colombus.engine.models import EvidenceRef

VIEW_NAMES: dict[RadiographView, str] = {
    RadiographView.PA: "periapical radiograph",
    RadiographView.BW: "bitewing radiograph",
    RadiographView.PANO: "panoramic radiograph",
    RadiographView.OCCLUSAL: "occlusal radiograph",
    RadiographView.CBCT: "CBCT volume",
    RadiographView.OTHER: "radiograph",
}


def fmt_date(d: date | None) -> str:
    return d.isoformat() if d else "undated"


def teeth_list(teeth: list[int]) -> str:
    return ", ".join(f"#{t}" for t in teeth)


def radiograph_label(a: ChartArtifact) -> str:
    p = a.payload
    assert isinstance(p, RadiographPayload)
    name = VIEW_NAMES[p.view]
    if p.view == RadiographView.PA and len(p.teeth_fdi) == 1:
        return f"{name} of #{p.teeth_fdi[0]}"
    side = f", {p.laterality.value}" if p.laterality else ""
    teeth = f" ({teeth_list(p.teeth_fdi)})" if p.teeth_fdi else ""
    return f"{name}{side}{teeth}"


def radiograph_descriptor(a: ChartArtifact) -> str:
    """Filename-safe descriptor, e.g. `PA-36`, `BW-right`. Never carries identity."""
    p = a.payload
    assert isinstance(p, RadiographPayload)
    if p.view == RadiographView.PA and len(p.teeth_fdi) == 1:
        return f"PA-{p.teeth_fdi[0]}"
    if p.laterality:
        return f"{p.view.value}-{p.laterality.value}"
    return p.view.value


def artifact_label(a: ChartArtifact) -> str:
    p = a.payload
    if isinstance(p, RadiographPayload):
        return radiograph_label(a)
    if isinstance(p, PerioChartPayload):
        who = f", examiner {p.examiner}" if p.examiner else ""
        return f"periodontal chart, {p.point_count} sites{who}"
    if isinstance(p, PSRPayload):
        return "PSR scores for sextants S1-S6"
    if isinstance(p, TxPlanPayload):
        return f"treatment plan {a.artifact_id}"
    if isinstance(p, NotePayload):
        who = f", {p.author}" if p.author else ""
        return f"clinical note{who}"
    if isinstance(p, ExtractedDetailPayload):
        return f"treatment plan details quoted from clinical note {p.source_artifact_id}"
    if a.type == ArtifactType.CLAIM_FORM:
        return "computer-generated treatment form"
    return a.type.value.replace("_", " ")


def artifact_label_dated(a: ChartArtifact) -> str:
    return f"{artifact_label(a)}, captured {fmt_date(a.captured_at)}"


def evidence_label(e: EvidenceRef, case: Case) -> str:
    if e.artifact_id == "packet:claim_form":
        return "computer-generated treatment form (file 01 of this packet)"
    a = case.artifact(e.artifact_id)
    return artifact_label_dated(a) if a else e.label
