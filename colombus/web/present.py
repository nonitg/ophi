"""View-model helpers: turn service/engine objects into the shapes the templates render.

No judgement lives here. Verdicts, statuses and gaps come from the engine; this module only labels,
formats and groups them. Copy law: labels describe documentation completeness, never payer behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from colombus.assertions import criteria
from colombus.cdm.models import (
    ArtifactType, AssertionPayload, Availability, Case, ChartArtifact, ExtractedDetailPayload, NotePayload,
    PerioChartPayload, PSRPayload, RadiographPayload,
)
from colombus.dental import notation, sextants
from colombus.engine.models import Action, Status, Verdict
from colombus.rules.schema import AssertionCriterion, RulePack
from colombus.service import CaseView

# --- actors ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Actor:
    key: str
    name: str
    role: str
    licence: str | None

    @property
    def is_dentist(self) -> bool:
        return self.role == "dentist"

    @property
    def label(self) -> str:
        return f"{self.name} ({self.role}, {self.licence})" if self.licence else f"{self.name} ({self.role})"


ACTORS: dict[str, Actor] = {
    "dentist": Actor("dentist", "Dr. Priya Lau", "dentist", "ON-48213"),
    "coordinator": Actor("coordinator", "Kim Osei", "treatment coordinator", None),
}
DEFAULT_ACTOR = "coordinator"

# --- labels ---------------------------------------------------------------------------------------

VERDICT_LABEL: dict[Verdict, str] = {
    Verdict.BLOCKED: "Blocked — documentation gaps",
    Verdict.NEEDS_INPUT: "Needs input",
    Verdict.READY_WITH_RISKS: "Complete — with noted risks",
    Verdict.READY_TO_SUBMIT: "Complete — ready for sign-off",
    Verdict.EXCLUDED_AS_CODED: "Listed exclusion as coded",
    Verdict.PREAUTH_NOT_REQUIRED: "No preauthorization rule applies",
}
VERDICT_SHORT: dict[Verdict, str] = {
    Verdict.BLOCKED: "Blocked",
    Verdict.NEEDS_INPUT: "Needs input",
    Verdict.READY_WITH_RISKS: "Complete, risks",
    Verdict.READY_TO_SUBMIT: "Complete",
    Verdict.EXCLUDED_AS_CODED: "Exclusion",
    Verdict.PREAUTH_NOT_REQUIRED: "No preauth",
}
VERDICT_CLASS: dict[Verdict, str] = {
    Verdict.BLOCKED: "blocked",
    Verdict.NEEDS_INPUT: "needs",
    Verdict.READY_WITH_RISKS: "risks",
    Verdict.READY_TO_SUBMIT: "ready",
    Verdict.EXCLUDED_AS_CODED: "blocked",
    Verdict.PREAUTH_NOT_REQUIRED: "muted",
}
STATUS_LABEL: dict[Status, str] = {
    Status.SATISFIED: "Satisfied",
    Status.AT_RISK: "Satisfied, with risk",
    Status.PENDING_CONFIRMATION: "Awaiting confirmation",
    Status.UNSATISFIED: "Unsatisfied",
    Status.INDETERMINATE: "Awaiting dentist",
    Status.NOT_APPLICABLE: "Not applicable",
}
STATUS_CLASS: dict[Status, str] = {
    Status.SATISFIED: "ok",
    Status.AT_RISK: "risk",
    Status.PENDING_CONFIRMATION: "pending",
    Status.UNSATISFIED: "bad",
    Status.INDETERMINATE: "ask",
    Status.NOT_APPLICABLE: "na",
}
READY_VERDICTS = (Verdict.READY_TO_SUBMIT, Verdict.READY_WITH_RISKS)

# --- formatting -----------------------------------------------------------------------------------


def money(dollars: float | None) -> str:
    if dollars is None:
        return "—"
    return f"${dollars:,.0f}" if float(dollars).is_integer() else f"${dollars:,.2f}"


def short_date(d: date | None) -> str:
    return d.strftime("%b %-d") if d else "—"


def days_until(d: date | None, today: date) -> int | None:
    return (d - today).days if d else None


def week_label(today: date) -> str:
    monday = today.fromordinal(today.toordinal() - today.weekday())
    friday = monday.fromordinal(monday.toordinal() + 4)
    if monday.month == friday.month:
        return f"Week of {monday.strftime('%b %-d')}–{friday.day}"
    return f"Week of {monday.strftime('%b %-d')} – {friday.strftime('%b %-d')}"


def tooth_name(fdi: int) -> str:
    return notation.describe(fdi)


def source_title(pack: RulePack, key: str) -> str:
    s = pack.sources.get(key)
    return s.title if s else key


# --- queue ----------------------------------------------------------------------------------------


def top_blocking_actions(view: CaseView, n: int = 2) -> list[dict]:
    """The two sub-lines under a queue row. For stale evidence, the concrete last-seen date beats prose."""
    out = []
    for a in view.assessment.actions:
        if not a.blocking:
            continue
        hint = None
        for rid in a.unblocks:
            r = view.assessment.requirement(rid)
            if r is None:
                continue
            if r.shortfall.stale:
                s = r.shortfall.stale[0]
                hint = f"last {s.captured_at.isoformat()}, {round(s.age_days / 30.44)} mo"
            elif r.shortfall.incomplete and r.shortfall.incomplete.get("sites_per_tooth", 6) < 6:
                hint = f"{r.shortfall.incomplete['sites_per_tooth']}-point chart dated {r.shortfall.incomplete.get('captured_at')}"
        out.append({"title": a.title, "hint": hint})
        if len(out) == n:
            break
    return out


def queue_summary(views: list[CaseView]) -> dict:
    open_views = [v for v in views if not v.signed]
    at_risk = [v for v in open_views if v.assessment.verdict != Verdict.READY_TO_SUBMIT]
    needs_attention = [v for v in open_views if v.assessment.blocking_count]
    today = max((v.case.as_of for v in views), default=date.today())
    subsystems = {s for v in views for s in v.minutes_estimate["subsystems_read"]}
    return {
        "clinic": views[0].case.clinic if views else "Fictional Dental Centre",
        "open_count": len(open_views),
        "dollars_at_risk": sum(v.dollars_at_risk for v in at_risk),
        "needs_attention": len(needs_attention),
        "week": week_label(today),
        "today": today,
        "artifacts_scanned": sum(v.minutes_estimate["artifacts_scanned"] for v in views),
        "subsystems": len(subsystems),
        "manual_minutes": views[0].minutes_estimate["manual_minutes"] if views else 25,
    }


# --- case review ----------------------------------------------------------------------------------


def requirement_detail(r) -> str:
    """The engine repeats 'awaiting the treating dentist's confirmation' per criterion; the assertions block
    already lists them, so collapse that case to a count. Anything else renders verbatim."""
    sf = r.shortfall
    if sf.missing_assertions and not (sf.missing or sf.stale or sf.undated or sf.incomplete or sf.pending_confirmation):
        n = len(sf.missing_assertions)
        return f"Awaiting the treating dentist's confirmation of {n} {'criterion' if n == 1 else 'criteria'} — see Clinician Assertions below."
    return r.detail


def pending_proposal_for(view: CaseView, action: Action) -> ChartArtifact | None:
    """The unconfirmed proposal a `confirm_extraction` action is asking about."""
    for rid in action.unblocks:
        r = view.assessment.requirement(rid)
        if r is None:
            continue
        for e in r.evidence:
            if not e.confirmed:
                p = next((p for p in view.proposals if p.artifact_id == e.artifact_id), None)
                if p is not None:
                    return p
    return None


def proposal_state(p: ChartArtifact) -> str:
    pl = p.payload
    assert isinstance(pl, ExtractedDetailPayload)
    if pl.rejected:
        return "rejected"
    return "confirmed" if pl.confirmed_by else "pending"


def _mode_sites(payload: PerioChartPayload) -> int:
    counts = [t.sites_measured for t in payload.teeth if t.sites_measured]
    return max(set(counts), key=counts.count) if counts else 0


def evidence_panel(view: CaseView) -> dict:
    """Group the chart for the right-hand column. Recency facts come from the assessment, not recomputed."""
    case = view.base_case
    a = view.assessment
    tooth = case.requested_tooth
    expires = {e.artifact_id: e.expires_on for r in a.requirements for e in r.evidence if e.expires_on}
    stale = {s.artifact_id: s for r in a.requirements for s in r.shortfall.stale}

    radiographs = []
    for art in case.artifacts_of(ArtifactType.RADIOGRAPH):
        pl = art.payload
        assert isinstance(pl, RadiographPayload)
        radiographs.append({
            "id": art.artifact_id, "view": pl.view.value, "teeth": pl.teeth_fdi, "laterality": pl.laterality.value if pl.laterality else None,
            "captured_at": art.captured_at, "age_days": (case.as_of - art.captured_at).days if art.captured_at else None,
            "expires_on": expires.get(art.artifact_id), "stale": stale.get(art.artifact_id),
            "images_apex": pl.images_apex, "covers_tooth": tooth in pl.teeth_fdi,
        })

    present = len(case.dentition.present_teeth(notation.ALL_FDI_PERMANENT))
    perio = []
    for art in case.artifacts_of(ArtifactType.PERIO_CHART):
        pl = art.payload
        assert isinstance(pl, PerioChartPayload)
        mine = next((t for t in pl.teeth if t.tooth_fdi == tooth), None)
        perio.append({
            "id": art.artifact_id, "captured_at": art.captured_at, "points": pl.point_count, "possible": present * 6,
            "sites_per_tooth": _mode_sites(pl), "teeth_charted": len(pl.teeth_charted), "present": present,
            "requested_depths": mine.depths_mm if mine else None, "certified": pl.certified, "examiner": pl.examiner,
            "expires_on": expires.get(art.artifact_id), "stale": stale.get(art.artifact_id),
        })

    psr = []
    for art in case.artifacts_of(ArtifactType.PSR):
        pl = art.payload
        assert isinstance(pl, PSRPayload)
        psr.append({"id": art.artifact_id, "captured_at": art.captured_at, "scores": pl.scores,
                    "highlight": sextants.sextant_of(tooth), "expires_on": expires.get(art.artifact_id)})

    notes = []
    for art in case.artifacts_of(ArtifactType.CLINICAL_NOTE):
        pl = art.payload
        assert isinstance(pl, NotePayload)
        props = [p for p in view.proposals if isinstance(p.payload, ExtractedDetailPayload) and p.payload.source_artifact_id == art.artifact_id]
        notes.append({"id": art.artifact_id, "captured_at": art.captured_at, "author": pl.author, "type": pl.note_type,
                      "teeth": pl.teeth_fdi, "segments": _segments(pl.text, props)})

    history = sorted(case.procedure_history, key=lambda h: h.performed_on, reverse=True)
    assurance = [(sec.value, sa) for sec, sa in case.assurance.items() if sa.availability != Availability.PRESENT]
    return {"radiographs": radiographs, "perio": perio, "psr": psr, "notes": notes, "history": history, "assurance": assurance,
            "sextants": sextants.ALL_SEXTANTS}


def _segments(text: str, proposals: list[ChartArtifact]) -> list[dict]:
    """Split note text so each proposed quote renders as its own highlighted span."""
    spans = []
    for p in proposals:
        pl = p.payload
        assert isinstance(pl, ExtractedDetailPayload)
        i = text.find(pl.quote)
        if i >= 0:
            spans.append((i, i + len(pl.quote), p))
    spans.sort(key=lambda s: s[0])
    out, pos = [], 0
    for start, end, p in spans:
        if start < pos:
            continue  # overlapping quotes: first one wins
        if start > pos:
            out.append({"text": text[pos:start], "proposal": None})
        out.append({"text": text[start:end], "proposal": p, "state": proposal_state(p)})
        pos = end
    if pos < len(text):
        out.append({"text": text[pos:], "proposal": None})
    return out


# --- clinician assertions -------------------------------------------------------------------------


def assertion_rows(view: CaseView, pack: RulePack) -> tuple[list[dict], list[dict]]:
    """(relevant, other). Relevant = an applicable requirement asks for it, or it has already been answered."""
    case = view.case
    current: dict[str, AssertionPayload] = {}
    for art in case.artifacts_of(ArtifactType.CLINICIAN_ASSERTION):  # later artifacts (user input) win
        pl = art.payload
        assert isinstance(pl, AssertionPayload)
        current[pl.criterion_id] = pl
    wanted = set(criteria.relevant_criteria(case, pack)) | set(current)
    relevant, other = [], []
    for cid, crit in pack.assertion_criteria.items():
        ctx = criteria.criterion_context(case, pack, cid)
        row = {"id": cid, "label": crit.label, "clause": crit.clause, "current": current.get(cid),
               "variant": ctx.variant_text, "odontogram": ctx.hint}
        (relevant if cid in wanted else other).append(row)
    return relevant, other


# --- packet ---------------------------------------------------------------------------------------


def manifest_files(manifest: dict | None) -> list[dict]:
    """Normalise the packet manifest's file list; key names are the packet engineer's, so be lenient."""
    if not manifest:
        return []
    out = []
    for i, f in enumerate(manifest.get("files", []), start=1):
        spec = f.get("spec_ok", f.get("spec_pass"))
        if isinstance(f.get("spec_checks"), dict):
            spec = f["spec_checks"].get("pass", spec)
        out.append({
            "seq": f.get("seq", i),
            "filename": f.get("filename") or f.get("name") or f.get("path", "—"),
            "kind": f.get("kind") or f.get("type", "—"),
            "requirements": f.get("requirement_ids") or f.get("requirements") or [],
            "spec_ok": spec,
            "bytes": f.get("bytes"),
        })
    return out


def kb(n: int | None) -> str:
    return f"{(n or 0) / 1024:,.0f} KB"
