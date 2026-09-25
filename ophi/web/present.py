"""View-model helpers: turn service/engine objects into the shapes the templates render.

No judgement lives here. Verdicts, statuses and gaps come from the engine; this module only labels,
formats and groups them. Copy law: labels describe documentation completeness, never payer behaviour.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from ophi.assertions import criteria
from ophi.cdm.models import (
    ArtifactType, AssertionPayload, Availability, Case, ChartArtifact, ExtractedDetailPayload, NotePayload,
    PerioChartPayload, PSRPayload, RadiographPayload, Section,
)
from ophi.dental import notation, sextants
from ophi.engine import recency
from ophi.engine.models import Action, Status, Verdict
from ophi.rules.schema import AssertionCriterion, RulePack
from ophi.service import CaseView

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

# Who acts on each kind of blocking engine action, and what every screen calls it. One table feeds the
# case headline, the case lanes, the queue chips and the inbox, so they never disagree. The coordinator
# fixes the chart, checks what Ophi cannot verify and confirms its findings; the treating dentist takes
# the clinical steps, records the clinical criteria and signs.
TASK_KINDS: dict[str, tuple[str, str]] = {  # kind -> (who acts, plural)
    "chart gap": ("coordinator", "chart gaps"),
    "item Ophi cannot verify": ("coordinator", "items Ophi cannot verify"),
    "chart finding to confirm": ("coordinator", "chart findings to confirm"),
    "packet to submit": ("coordinator", "packets to submit"),
    "clinical step": ("dentist", "clinical steps"),
    "clinical criterion": ("dentist", "clinical criteria"),
    "packet to sign": ("dentist", "packets to sign"),
}
_KIND_OF_ACTION = {"confirm_extraction": "chart finding to confirm", "check_source": "item Ophi cannot verify",
                   "resolve_unknown": "item Ophi cannot verify", "criterion_not_met": "clinical step",
                   "excluded_code": "clinical step", "assert": "clinical criterion"}
_FROM_ID = re.compile(r"\s*\(from [a-z0-9_.\-]+\)$", re.I)


def task_kind(a: Action) -> str:
    """Pack gaps with clinical effort are the dentist's; every other gap is chart work."""
    return _KIND_OF_ACTION.get(a.action_type) or ("clinical step" if a.effort == "clinical" else "chart gap")


def task_text(kind: str, n: int) -> str:
    return plural(n, kind, TASK_KINDS[kind][1])


def action_title(a: Action) -> str:
    """Engine titles for proposals end with '(from note_0514)'; the quote itself is shown, so the id is noise."""
    return _FROM_ID.sub("", a.title)


def gap_groups(view: CaseView) -> dict:
    """Blocking work split by who acts: `work` is the coordinator's, `clinical` the dentist's steps, `confirms`
    the requirements still waiting on the dentist's criteria."""
    a = view.assessment
    by = _unblocked_by(a)
    work, clinical = [], []
    for act in a.actions:
        if not act.blocking or act.action_type == "assert":
            continue
        r = _unblocked(view, act)
        cls, status = status_of(r, by) if r else ("bad", "Open")
        item = {"action": act, "title": action_title(act), "requirement": r, "cls": cls, "status": status,
                "kind": task_kind(act), "hint": _action_hint(view, act),
                "proposal": pending_proposal_for(view, act) if act.action_type == "confirm_extraction" else None}
        (clinical if TASK_KINDS[item["kind"]][0] == "dentist" else work).append(item)
    confirms = _confirm_rows(a)
    return {"work": work, "clinical": clinical, "confirms": confirms, "advisory": [act for act in a.actions if not act.blocking],
            "criteria_pending": sum(c["criteria"] for c in confirms)}


def _unblocked(view: CaseView, a: Action):
    return view.assessment.requirement(a.unblocks[0]) if a.unblocks else None


def _confirm_rows(a) -> list[dict]:
    """One line per requirement still waiting on the dentist's criteria, in action rank order. Counted from the
    engine's shortfall, so a 'not met' answer on one criterion never hides the ones still unanswered."""
    first_rank: dict[str, int] = {}
    for i, act in enumerate(a.actions):
        for rid in act.unblocks:
            first_rank.setdefault(rid, i)
    waiting = sorted((r for r in a.requirements if r.applicable and r.shortfall.missing_assertions),
                     key=lambda r: first_rank.get(r.requirement_id, len(a.actions)))
    rows = []
    for r in waiting:
        n = len(r.shortfall.missing_assertions)
        rows.append({"requirement": r, "criteria": n, "label": f"{r.label} ({n} criteria)" if n > 1 else r.label})
    return rows


def headline(view: CaseView, gaps: dict) -> dict:
    """The sentence at the top of Case Review. Documentation completeness only — never payer behaviour."""
    a = view.assessment
    provider = view.case.treatment.provider.name
    if view.signed:
        so = view.state.sign_off
        if view.state.submitted_at:
            return {"tone": "signed", "title": f"Signed by {so.signed_by}.",
                    "sub": f"Marked submitted on {view.state.submitted_at:%b %-d}. The clinic sent it; Ophi never transmits."}
        return {"tone": "signed", "title": f"Signed by {so.signed_by}.",
                "sub": "Download the packet from the packet screen and submit it through your PMS. Ophi never transmits."}
    if a.verdict in (Verdict.BLOCKED, Verdict.NEEDS_INPUT):
        kinds: dict[str, int] = {}
        for w in gaps["work"] + gaps["clinical"]:
            kinds[w["kind"]] = kinds.get(w["kind"], 0) + 1
        parts = [task_text(k, n) for k, n in kinds.items()]
        if gaps["criteria_pending"]:
            parts.append(f"{task_text('clinical criterion', gaps['criteria_pending'])} for {provider} to confirm")
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


# --- requirement families: one order for the case strip, the queue matrix and the trail -------------

# Who produces the evidence names the family: documents come from the chart, the plan's age, tooth and
# frequency limits Ophi checks against it, clinical criteria only the treating dentist can assert.
# Copy law: no family label may read as a coverage claim ("Eligibility" did).
REQ_FAMILIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Chart", ("claim_form", "tx_plan_details", "radiograph_pa", "radiograph_bw", "perio_chart", "lab_codes_current")),
    ("Limits", ("client_age", "tooth_eligibility", "frequency_tooth", "frequency_client")),
    ("Clinical", ("basic_treatment_complete", "restorability", "extensively_restored", "endo_healed")),
)
REQ_SHORT: dict[str, str] = {
    "claim_form": "Claim form", "tx_plan_details": "Treatment plan", "radiograph_pa": "Periapical",
    "radiograph_bw": "Bitewings", "perio_chart": "Perio chart", "lab_codes_current": "Lab codes",
    "client_age": "Client age", "tooth_eligibility": "Tooth type", "frequency_tooth": "Tooth frequency",
    "frequency_client": "Client frequency", "basic_treatment_complete": "Basic treatment",
    "restorability": "Restorability", "extensively_restored": "Extensively restored", "endo_healed": "Endo healed",
}


def _families(requirements) -> list[tuple[str, list]]:
    """Requirements grouped by family, in family order. A requirement the map does not know lands in 'Other'."""
    by_id = {r.requirement_id: r for r in requirements}
    known = {rid for _, ids in REQ_FAMILIES for rid in ids}
    out = [(name, [by_id[i] for i in ids if i in by_id]) for name, ids in REQ_FAMILIES]
    out.append(("Other", [r for r in requirements if r.requirement_id not in known]))
    return [(name, rs) for name, rs in out if rs]


def _unblocked_by(a) -> dict[str, str]:
    """Requirement id -> the type of the first-ranked action that settles it."""
    out: dict[str, str] = {}
    for act in a.actions:
        for rid in act.unblocks:
            out.setdefault(rid, act.action_type)
    return out


def status_of(r, by: dict[str, str]) -> tuple[str, str]:
    """Status class and words for one requirement. An indeterminate requirement that no dentist answer settles
    (the source cannot see that part of the chart, or an identifier is missing) reads 'Cannot verify'."""
    if r.status == Status.INDETERMINATE and by.get(r.requirement_id, "assert") != "assert":
        return "unknown", "Cannot verify"
    return STATUS_CLASS[r.status], STATUS_LABEL[r.status]


def _cell(r, by: dict[str, str]) -> dict:
    cls, status = status_of(r, by)
    return {"id": r.requirement_id, "short": REQ_SHORT.get(r.requirement_id, r.label), "label": r.label,
            "status": status, "cls": cls, "applicable": r.applicable}


def strip(a) -> list[dict]:
    """The whole rule check in one glance: every pack requirement as a cell, grouped by family. Not-applicable
    cells keep the queue's columns aligned; the case screen leaves them out."""
    by = _unblocked_by(a)
    return [{"family": name, "cells": [_cell(r, by) for r in rs]} for name, rs in _families(a.requirements)]


_PART_PHRASE = {"bad": "missing or stale", "unknown": "cannot verify", "pending": "awaiting confirmation", "ask": "awaiting the dentist",
                "risk": "with a noted risk"}


def completeness_parts(a) -> list[dict]:
    """What is not yet documented: (status class, counted phrase) pairs for the bar legend, in bar-colour order."""
    by = _unblocked_by(a)
    counts: dict[str, int] = {}
    for r in a.requirements:
        if r.applicable:
            cls = status_of(r, by)[0]
            counts[cls] = counts.get(cls, 0) + 1
    return [{"cls": k, "text": f"{counts[k]} {_PART_PHRASE[k]}"} for k in _PART_PHRASE if counts.get(k)]


# --- stages and people: who each case is waiting on ---------------------------------------------------

# One vocabulary for the queue rail, the row pill and the case header, in the order a case moves.
STAGES: tuple[tuple[str, str], ...] = (("blocked", "Blocked"), ("needs", "Needs input"), ("ready", "Ready to sign"),
                                       ("signed", "Signed"), ("submitted", "Submitted"))
_STAGE_OF = {Verdict.BLOCKED: "blocked", Verdict.NEEDS_INPUT: "needs", Verdict.READY_TO_SUBMIT: "ready",
             Verdict.READY_WITH_RISKS: "ready"}


def stage(view: CaseView) -> dict:
    v = view.assessment.verdict
    if view.signed:
        key = "submitted" if view.state.submitted_at else "signed"
    else:
        key = _STAGE_OF.get(v, "other")
    if key == "other":  # exclusions and codes with no preauth rule sit outside the pipeline
        return {"key": key, "label": VERDICT_SHORT[v], "cls": VERDICT_CLASS[v]}
    risks = key == "ready" and v == Verdict.READY_WITH_RISKS
    return {"key": key, "label": "Ready, with risks" if risks else dict(STAGES)[key], "cls": "risks" if risks else key}


def monogram(name: str) -> str:
    """Initials for a person chip: 'Dr. Priya Lau' -> 'PL'."""
    parts = [p for p in re.split(r"[\s.]+", name) if p and p.lower() not in ("dr", "dre")]
    return "".join(p[0].upper() for p in (parts[:1] + parts[-1:] if len(parts) > 1 else parts)) or "?"


def _person(role: str, name: str, count: int, what: str) -> dict:
    return {"role": role, "name": name, "initials": monogram(name), "count": count, "what": what}


def _tasks(view: CaseView, gaps: dict | None = None) -> list[tuple[str, int]]:
    """(task kind, count) for everything the case waits on."""
    if view.signed:
        return [] if view.state.submitted_at else [("packet to submit", 1)]
    if view.assessment.verdict in READY_VERDICTS:
        return [("packet to sign", 1)]
    gaps = gaps or gap_groups(view)
    counts: dict[str, int] = {}
    for w in gaps["work"] + gaps["clinical"]:
        counts[w["kind"]] = counts.get(w["kind"], 0) + 1
    if gaps["criteria_pending"]:
        counts["clinical criterion"] = gaps["criteria_pending"]
    return list(counts.items())


def waiting_on(view: CaseView, gaps: dict | None = None) -> list[dict]:
    """One chip per person the case is waiting on, with what they owe in words."""
    names = {"coordinator": ACTORS["coordinator"].name, "dentist": view.case.treatment.provider.name}
    people: dict[str, list[str]] = {}
    counts: dict[str, int] = {}
    for kind, n in _tasks(view, gaps):
        role = TASK_KINDS[kind][0]
        people.setdefault(role, []).append(task_text(kind, n))
        counts[role] = counts.get(role, 0) + n
    return [_person(role, names[role], counts[role], _join(texts)) for role, texts in people.items()]


def inbox(views: list[CaseView], actor: Actor) -> list[dict]:
    """What the person acting now owes across this week's open cases, one line per kind of task."""
    out: dict[str, dict] = {}
    for v in views:
        for kind, n in _tasks(v):
            if TASK_KINDS[kind][0] == actor.key:
                t = out.setdefault(kind, {"kind": kind, "count": 0, "cases": []})
                t["count"] += n
                t["cases"].append(v.case.patient.display_name)
    return [{**t, "text": task_text(t["kind"], t["count"])} for t in out.values()]


def stage_rail(views: list[CaseView]) -> list[dict]:
    """Cases and treatment dollars at each stage, in the order a case moves."""
    keys = [stage(v)["key"] for v in views]
    return [{"key": k, "label": label, "count": keys.count(k),
             "dollars": sum(v.dollars_at_risk for v, kk in zip(views, keys) if kk == k)} for k, label in STAGES]


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
        "requirements_checked": sum(v.assessment.completeness["applicable"] for v in views),
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
        return f"Awaiting the treating dentist's confirmation of {n} {'criterion' if n == 1 else 'criteria'} — see Clinical criteria."
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
            "sextants": sextants.ALL_SEXTANTS, "empty": _empty_text(case)}


def _empty_text(case: Case) -> dict[str, str]:
    """What an empty evidence list says. Absent and unseen are different conclusions: a section the source
    cannot see is never reported as having nothing in it."""
    unseen = {sec: sa.availability.value for sec, sa in case.assurance.items()
              if sa.availability in (Availability.UNKNOWN, Availability.DEGRADED)}
    return {sec.value: f"Not visible to the connected source ({unseen[sec]})." if sec in unseen else "None in the chart."
            for sec in (Section.IMAGING, Section.PERIO, Section.NOTES, Section.PROCEDURE_HISTORY)}


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


# --- case trail: what settled each requirement, who acts next, and the hand-off ----------------------

_CHART_EVIDENCE = {"radiograph", "perio_chart", "psr", "tx_plan", "tx_plan_details", "clinical_note"}


def documented(view: CaseView) -> list[dict]:
    """Satisfied requirements as trail rows, in family order: the evidence that settled each, its date and age
    (from the assessment, not recomputed) and who produced it."""
    rows = []
    by = _unblocked_by(view.assessment)
    for _, rs in _families(view.assessment.requirements):
        for r in rs:
            if not r.applicable or r.status not in (Status.SATISFIED, Status.AT_RISK):
                continue
            dated = [e for e in r.evidence if e.captured_at and e.type != "clinician_assertion"]
            rows.append({**_cell(r, by), "clause": r.clause, "risk": r.risk_reason, "source": _source(r), "what": _what(view, r),
                         "date": min((e.captured_at for e in dated), default=None),
                         "age": max((e.age_days for e in dated if e.age_days is not None), default=None),
                         "until": min((e.expires_on for e in r.evidence if e.expires_on), default=None)})
    return rows


def _source(r) -> str:
    types = {e.type for e in r.evidence}
    if "clinician_assertion" in types:
        return "dentist"
    return "chart" if types & _CHART_EVIDENCE else "ophi"


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def _what(view: CaseView, r) -> str:
    """One short phrase for the evidence. Engine detail text is used verbatim when there is no artifact to name."""
    ev = r.evidence
    asserted = {e.artifact_id for e in ev if e.type == "clinician_assertion"}
    if asserted:
        by = sorted({art.payload.asserted_by for art in view.case.artifacts_of(ArtifactType.CLINICIAN_ASSERTION)
                     if art.artifact_id in asserted and isinstance(art.payload, AssertionPayload)})
        n = len(asserted)
        return (f"{n} criteria confirmed" if n > 1 else "Confirmed") + (f" by {', '.join(by)}" if by else "")
    if r.satisfied_via == "plan_in_note":
        return "Stated in the clinical note, confirmed"
    if r.satisfied_via == "structured_plan":
        return "Structured plan in the PMS"
    if ev:
        return _cap(", ".join(e.label for e in ev))
    return _cap(r.detail) if r.detail else r.label


def handoff(view: CaseView) -> dict:
    """The two human steps every case ends with. The dentist signs; the clinic submits through its own PMS."""
    so = view.state.sign_off if view.signed else None
    ready = view.assessment.verdict in READY_VERDICTS
    return {"sign": "done" if so else ("ready" if ready else "locked"), "signed_by": so.signed_by if so else None,
            "signed_at": so.signed_at if so else None,
            "submit": "done" if so and view.state.submitted_at else ("ready" if so else "locked"),
            "submitted_at": view.state.submitted_at if so else None}


def work_done(view: CaseView) -> list[dict]:
    """What Ophi did on this case, as counts. The scale of the cross-check a coordinator would do by hand."""
    a, m = view.assessment, view.minutes_estimate
    applicable = [r for r in a.requirements if r.applicable]
    return [
        {"label": "Chart entries read", "value": m["artifacts_scanned"]},
        {"label": "PMS subsystems read", "value": len(m["subsystems_read"])},
        {"label": "CDCP requirements checked", "value": len(applicable)},
        {"label": "Rule clauses cited", "value": len({(r.clause.source, r.clause.ref) for r in applicable})},
    ]


_LANES = (("pa", "Periapical"), ("bw", "Bitewings"), ("img", "Other imaging"), ("perio", "Perio"), ("notes", "Notes"))
_LANE_REQUIREMENT = {"pa": "radiograph_pa", "bw": "radiograph_bw", "perio": "perio_chart"}
RECENCY_MONTHS = 12  # the documentation matrix bound for the periapical, bitewings and perio chart
_LANE_SECTION = {"pa": Section.IMAGING, "bw": Section.IMAGING, "img": Section.IMAGING, "perio": Section.PERIO, "notes": Section.NOTES}


def chart_timeline(view: CaseView, months: int = 36) -> dict:
    """Every dated chart entry on one time axis, with the 12-month window the CDCP recency rules use.
    Which entries are stale comes from the assessment; this only places them."""
    case, a = view.base_case, view.assessment
    as_of = case.as_of
    appt = case.treatment.appointment_date
    start = date(as_of.year - months // 12, as_of.month, 1)
    end = max(as_of, appt or as_of)
    end = date.fromordinal(end.toordinal() + 21)
    span = (end - start).days

    def x(d: date) -> float:
        return round(max(0.0, min(1.0, (d - start).days / span)) * 100, 2)

    stale = {s.artifact_id for r in a.requirements for s in r.shortfall.stale}
    risk = {e.artifact_id for r in a.requirements if r.applicable and r.status == Status.AT_RISK for e in r.evidence}
    # Green means the entry settles a requirement; evidence matched by a requirement still open stays hollow.
    used = {e.artifact_id for r in a.requirements if r.applicable and r.status in (Status.SATISFIED, Status.AT_RISK) for e in r.evidence}
    used |= {p.payload.source_artifact_id for p in view.proposals
             if p.artifact_id in used and isinstance(p.payload, ExtractedDetailPayload)}
    tooth = case.requested_tooth
    lanes: dict[str, list[dict]] = {k: [] for k, _ in _LANES}
    for art in case.artifacts:
        if not art.captured_at:
            continue
        pl = art.payload
        if isinstance(pl, RadiographPayload):
            lane = {"PA": "pa", "BW": "bw"}.get(pl.view.value, "img")
            label = f"{pl.view.value} {' '.join('#' + str(t) for t in pl.teeth_fdi[:4])}".strip()
            key = tooth in pl.teeth_fdi
        elif isinstance(pl, (PerioChartPayload, PSRPayload)):
            lane, label, key = "perio", "PSR" if isinstance(pl, PSRPayload) else f"Perio chart, {pl.point_count} sites", True
        elif isinstance(pl, NotePayload) or art.type == ArtifactType.TX_PLAN:
            lane, label, key = "notes", "Clinical note" if isinstance(pl, NotePayload) else "Treatment plan", False
        else:
            continue
        lanes[lane].append({"x": x(art.captured_at), "date": art.captured_at, "label": label, "id": art.artifact_id,
                            "stale": art.artifact_id in stale, "used": art.artifact_id in used, "risk": art.artifact_id in risk, "key": key,
                            "clamped": art.captured_at < start})
    # The oldest capture date the engine's recency rule still counts (current, or at risk between conventions).
    window = next(d for d in (date.fromordinal(as_of.toordinal() - k) for k in range(400, -1, -1))
                  if recency.check(d, as_of, RECENCY_MONTHS).status != "stale")
    years = [date(y, 1, 1) for y in range(start.year + 1, end.year + 1)]
    # A lane whose document the pack requires stays on the axis when empty: the gap is the finding.
    required = {k for k, rid in _LANE_REQUIREMENT.items() if (r := a.requirement(rid)) is not None and r.applicable}
    unseen = {sec for sec, sa in case.assurance.items() if sa.availability in (Availability.UNKNOWN, Availability.DEGRADED)}
    return {"lanes": [{"key": k, "label": label, "points": sorted(lanes[k], key=lambda p: p["date"]),
                       "unseen": _LANE_SECTION[k] in unseen}
                      for k, label in _LANES if lanes[k] or k in required],
            "window_x": x(window), "today_x": x(as_of), "appt_x": x(appt) if appt else None, "today": as_of, "appt": appt,
            "ticks": [{"x": x(y), "label": str(y.year)} for y in years], "start": start}


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


# --- look-back ------------------------------------------------------------------------------------


def lookback_months(report) -> list[dict]:
    """The window as month columns, oldest first; each submission is one cell, so the count is the picture."""
    months: dict[tuple[int, int], list] = {}
    for r in sorted(report.rows, key=lambda r: r.submitted_on):
        months.setdefault((r.submitted_on.year, r.submitted_on.month), []).append(r)
    if not months:
        return []
    (y, m), last = min(months), max(months)
    out = []
    while (y, m) <= last:
        out.append({"label": date(y, m, 1).strftime("%b"), "year": y, "rows": months.get((y, m), [])})
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def lookback_gaps(report) -> list[dict]:
    """Which required document was open on the day each denied request went out, most frequent first."""
    counts: dict[str, int] = {}
    for r in report.rows:
        if r.decision == "denied":
            for g in r.gaps:
                counts[g] = counts.get(g, 0) + 1
    top = max(counts.values(), default=1)
    return [{"label": g, "count": n, "pct": round(n / top * 100)} for g, n in sorted(counts.items(), key=lambda kv: -kv[1])]


# --- audit ----------------------------------------------------------------------------------------

EVENT_LABEL = {"assert": "Recorded a clinical criterion", "confirm_proposal": "Decided on a chart finding",
               "edit_narrative": "Edited the narrative", "sign_off": "Signed off", "download_packet": "Downloaded the packet",
               "mark_submitted": "Marked submitted"}


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
