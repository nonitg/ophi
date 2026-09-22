"""View-model helpers: turn service/engine objects into the shapes the templates render.

No judgement lives here. Verdicts, statuses and gaps come from the engine; this module only labels,
formats and groups them. Copy law: labels describe documentation completeness, never payer behaviour.
"""

from __future__ import annotations

import re
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


def plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def _action_hint(view: CaseView, a: Action) -> str | None:
    """For stale or thin evidence, the concrete last-seen fact beats prose."""
    for rid in a.unblocks:
        r = view.assessment.requirement(rid)
        if r is None:
            continue
        if r.shortfall.stale:
            s = r.shortfall.stale[0]
            return f"last {s.captured_at.isoformat()}, {round(s.age_days / 30.44)} mo ago"
        if r.shortfall.incomplete and r.shortfall.incomplete.get("sites_per_tooth", 6) < 6:
            return f"{r.shortfall.incomplete['sites_per_tooth']}-point chart dated {r.shortfall.incomplete.get('captured_at')}"
    return None


def queue_lead(view: CaseView) -> dict | None:
    """The one line under a queue row: the first concrete chart action, else the first blocking action.
    Dentist confirmations are folded into the '+N more' count so the row reads as one job."""
    blocking = [a for a in view.assessment.actions if a.blocking]
    if not blocking:
        return None
    lead = next((a for a in blocking if a.action_type != "assert"), blocking[0])
    return {"title": action_title(lead), "hint": _action_hint(view, lead), "more": len(blocking) - 1}


# --- glance layer: one sentence, one bar, one hero --------------------------------------------------

# Blocking actions are grouped by who acts: the coordinator fixes the chart, the dentist confirms criteria.
_WORK_KIND = {"new_radiograph": ("chart gap", "chart gaps"), "chart_entry": ("chart gap", "chart gaps"), "review": ("chart gap", "chart gaps"),
              "confirm_extraction": ("chart finding to confirm", "chart findings to confirm"),
              "check_source": ("item the connected source cannot see", "items the connected source cannot see"),
              "resolve_unknown": ("item the connected source cannot see", "items the connected source cannot see")}
_FROM_ID = re.compile(r"\s*\(from [a-z0-9_.\-]+\)$", re.I)


def action_title(a: Action) -> str:
    """Engine titles for proposals end with '(from note_0514)'; the quote itself is shown, so the id is noise."""
    return _FROM_ID.sub("", a.title)


def gap_groups(view: CaseView) -> dict:
    a = view.assessment
    work = [{"action": act, "title": action_title(act), "requirement": _unblocked(view, act),
             "proposal": pending_proposal_for(view, act) if act.action_type == "confirm_extraction" else None}
            for act in a.actions if act.blocking and act.action_type != "assert"]
    confirms = [_confirm_row(view, act) for act in a.actions if act.blocking and act.action_type == "assert"]
    return {"work": work, "confirms": confirms, "advisory": [act for act in a.actions if not act.blocking],
            "criteria_pending": sum(c["criteria"] for c in confirms)}


def _unblocked(view: CaseView, a: Action):
    return view.assessment.requirement(a.unblocks[0]) if a.unblocks else None


def _confirm_row(view: CaseView, a: Action) -> dict:
    """One plain line per dentist confirmation, named by the requirement it settles and counting its criteria."""
    r = _unblocked(view, a)
    n = len(r.shortfall.missing_assertions) if r else 1
    label = r.label if r else a.title
    return {"action": a, "criteria": n, "label": f"{label} ({n} criteria)" if n > 1 else label}


def headline(view: CaseView, gaps: dict) -> dict:
    """The sentence at the top of Case Review. Documentation completeness only — never payer behaviour."""
    a = view.assessment
    provider = view.case.treatment.provider.name
    if view.signed:
        so = view.state.sign_off
        return {"tone": "signed", "title": f"Signed by {so.signed_by}.",
                "sub": "Download the packet from the packet screen and submit it yourself. Colombus never transmits."}
    if a.verdict in (Verdict.BLOCKED, Verdict.NEEDS_INPUT):
        kinds: dict[tuple[str, str], int] = {}
        for w in gaps["work"]:
            k = _WORK_KIND.get(w["action"].action_type, ("chart gap", "chart gaps"))
            kinds[k] = kinds.get(k, 0) + 1
        parts = [plural(n, one, many) for (one, many), n in kinds.items()]
        if gaps["criteria_pending"]:
            parts.append(f"{plural(gaps['criteria_pending'], 'clinical criterion', 'clinical criteria')} for {provider} to confirm")
        title = "Not ready to submit." if a.verdict == Verdict.BLOCKED else "Needs a human before it can go out."
        return {"tone": VERDICT_CLASS[a.verdict], "title": title, "sub": _join(parts) + " before the packet can go out." if parts else ""}
    if a.verdict == Verdict.READY_TO_SUBMIT:
        return {"tone": "ready", "title": "Documentation complete — ready for sign-off.",
                "sub": f"Every applicable CDCP requirement is documented. {provider} signs the packet; the clinic submits it."}
    if a.verdict == Verdict.READY_WITH_RISKS:
        n = sum(1 for r in a.requirements if r.applicable and r.risk_reason)
        return {"tone": "risks", "title": "Documentation complete, with noted risks.",
                "sub": f"{plural(n, 'requirement is', 'requirements are')} satisfied with a risk worth reading before {provider} signs."}
    return {"tone": VERDICT_CLASS[a.verdict], "title": VERDICT_LABEL[a.verdict] + ".", "sub": a.schedule.detail}


def _join(parts: list[str]) -> str:
    if len(parts) <= 1:
        return "".join(parts)
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def segments(a) -> list[dict]:
    """One segment per applicable requirement, in pack order — the whole rule check in one glance."""
    return [{"id": r.requirement_id, "label": r.label, "status": STATUS_LABEL[r.status], "cls": STATUS_CLASS[r.status]}
            for r in a.requirements if r.applicable]


_PART_PHRASE = {"bad": "missing or stale", "pending": "awaiting confirmation", "ask": "awaiting the dentist", "risk": "with a noted risk"}


def completeness_parts(a) -> list[dict]:
    """What is not yet documented: (status class, counted phrase) pairs for the bar legend, in bar-colour order."""
    counts: dict[str, int] = {}
    for r in a.requirements:
        if r.applicable:
            counts[STATUS_CLASS[r.status]] = counts.get(STATUS_CLASS[r.status], 0) + 1
    return [{"cls": k, "text": f"{counts[k]} {_PART_PHRASE[k]}"} for k in _PART_PHRASE if counts.get(k)]


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
