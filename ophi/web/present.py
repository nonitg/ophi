"""View-model helpers: turn service/engine objects into the shapes the templates render.

No judgement lives here. Verdicts, statuses and gaps come from the engine, stages from `ophi.workflow`;
this module only labels, formats and groups them. Copy law: Ophi's own words describe documentation
completeness, never payer behaviour. Sun Life's decisions are shown as Sun Life's (see `payer` in rows).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from ophi.assertions import criteria
from ophi.casegen.dsl import CAPTURABLE
from ophi.cdm.models import (
    ArtifactType, AssertionPayload, Availability, ChartArtifact, ExtractedDetailPayload, NotePayload,
    PerioChartPayload, PSRPayload, RadiographPayload,
)
from ophi.dental import notation, sextants
from ophi.engine.models import Action, Status, Verdict
from ophi.lookback import DOCUMENT_REQUIREMENTS
from ophi.rules.schema import RulePack
from ophi.service import MANUAL_MINUTES_PER_PREAUTH, CaseView
from ophi.workflow import (
    CHART_STAGES, ORDER, OWNER, SUN_LIFE_TURNAROUND_DAYS, Stage, chair_actions, chart_actions, criteria_can_start, desk_actions,
    pending_criteria, reconsider_by, send_by, valid_until,
)

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

# Stages are named as the board's columns are, in the order the job happens.
STAGE_LABEL: dict[Stage, str] = {
    Stage.PATIENT: "Needs the patient",
    Stage.PREPARE: "Paperwork",
    Stage.DENTIST: "Dentist review",
    Stage.SEND: "Ready to send",
    Stage.SUN_LIFE: "With Sun Life",
    Stage.BOOK: "Book the crown",
    Stage.RESUBMIT: "Resubmit",
    Stage.DONE: "Booked",
    Stage.NOT_NEEDED: "No preauthorization needed",
}
PIPELINE = ORDER[:ORDER.index(Stage.DONE)]  # the stages that hold open work
BOOK_SOON_DAYS = 30

# --- formatting -----------------------------------------------------------------------------------


def money(dollars: float | None) -> str:
    if dollars is None:
        return "—"
    return f"${dollars:,.0f}" if float(dollars).is_integer() else f"${dollars:,.2f}"


def short_date(d: date | None) -> str:
    return d.strftime("%b %-d") if d else "—"


def long_date(d: date | None) -> str:
    return d.strftime("%A %b %-d") if d else "—"


CLINIC_TZ = ZoneInfo("America/Toronto")  # the demo clinic is in Ontario; times are stored in UTC


def local_time(dt: datetime | None, fmt: str = "%b %-d, %-I:%M %p") -> str:
    return dt.astimezone(CLINIC_TZ).strftime(fmt) if dt else "—"


def full_date(d: date | None) -> str:
    return d.strftime("%b %-d, %Y") if d else "—"


def sentence(s: str) -> str:
    """Engine labels arrive lower-case ('left BW'); capitalise the first letter only."""
    return s[:1].upper() + s[1:]


def day_heading(d: date) -> str:
    return d.strftime("%A, %B %-d")


def days_until(d: date | None, today: date) -> int | None:
    return (d - today).days if d else None


def in_days(n: int) -> str:
    if n == 0:
        return "today"
    if n == 1:
        return "tomorrow"
    if n == -1:
        return "yesterday"
    return f"in {n} days" if n > 0 else f"{-n} days ago"


def tooth_name(fdi: int) -> str:
    return notation.describe(fdi)


def source_title(pack: RulePack, key: str) -> str:
    s = pack.sources.get(key)
    return s.title if s else key


def plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def initials(name: str) -> str:
    parts = [p for p in name.replace("Dr.", "").split() if p]
    return "".join(p[0] for p in parts[:2]).upper()


def who_tag(kind: str | None, actor: Actor, provider: str) -> dict:
    """A monogram and a name for whoever does a step, e.g. {'mark': 'PL', 'label': 'Dr. Priya Lau'}."""
    person = provider if kind == "dentist" else ACTORS["coordinator"].name
    return {"kind": kind or "", "label": who_label(kind, actor, provider),
            "mark": {"sun_life": "SL", "ophi": "O"}.get(kind or "") or initials(person)}


def who_label(owner: str | None, actor: Actor, provider: str) -> str:
    """Name the person who acts next, as the viewer would say it: 'You' for themselves."""
    if owner == "dentist":
        return "You" if actor.is_dentist else provider
    if owner == "coordinator":
        return ACTORS["coordinator"].name if actor.is_dentist else "You"
    return {"sun_life": "Sun Life", "ophi": "Ophi"}.get(owner or "", "")


# --- actions --------------------------------------------------------------------------------------

_FROM_ID = re.compile(r"\s*\(from [a-z0-9_.\-]+\)$", re.I)


def action_title(a: Action) -> str:
    """Engine titles for proposals end with '(from note_0514)'; the quote itself is shown, so the id is noise."""
    return _FROM_ID.sub("", a.title)


def _action_hint(view: CaseView, a: Action) -> str | None:
    """For stale or thin evidence, the concrete last-seen fact beats prose."""
    for rid in a.unblocks:
        r = view.assessment.requirement(rid)
        if r is None:
            continue
        if r.shortfall.stale:
            s = r.shortfall.stale[0]
            return f"Last one {full_date(s.captured_at)}, {round(s.age_days / 30.44)} months old"
        if r.shortfall.incomplete and r.shortfall.incomplete.get("sites_per_tooth", 6) < 6:
            return f"{r.shortfall.incomplete['sites_per_tooth']}-point chart on file"
    return None


def gap_rows(view: CaseView) -> list[dict]:
    """The chart work on a case, each with the requirement it settles and any quote to confirm. Chair gaps first:
    the visit takes longest to arrange."""
    return [{"action": act, "title": action_title(act), "hint": _action_hint(view, act), "requirement": _unblocked(view, act),
             "chair": act.needs_patient, "capturable": act.needs_patient and bool(set(act.unblocks) & CAPTURABLE),
             "proposal": pending_proposal_for(view, act) if act.action_type == "confirm_extraction" else None}
            for act in chair_actions(view.assessment) + desk_actions(view.assessment)]


# A chair gap as the chair team says it, and who there does it. Ontario: only a dentist orders X-rays and an
# assistant or hygienist takes them; only a hygienist or the dentist probes (RCDSO, CDHO).
CHAIR_SHORT = {"radiograph_pa": "PA X-ray of #{tooth}", "radiograph_bw": "bitewing X-rays", "perio_chart": "6-site perio chart",
               "basic_treatment_complete": "basic treatment"}
CHAIR_ROLE = {"radiograph_pa": "Assistant", "radiograph_bw": "Assistant", "perio_chart": "Hygienist",
              "basic_treatment_complete": "Dentist"}


def in_chair(view: CaseView) -> bool:
    """The patient is in an operatory and the chart still needs them: the one moment a gap costs no extra visit."""
    return view.case.in_chair is not None and view.stage == Stage.PATIENT


def first_name(view: CaseView) -> str:
    name = view.case.patient.display_name  # the PMS may store "LAST, FIRST"
    return name.split(",")[1].split()[0].title() if "," in name else name.split()[0]


def chair_items(view: CaseView) -> list[dict]:
    """The chair gaps as one visit's checklist: what to take, who takes it, and what the chart has now."""
    out = []
    for act in chair_actions(view.assessment):
        rid = act.unblocks[0]
        out.append({"rid": rid, "label": CHAIR_SHORT.get(rid, action_title(act)).format(tooth=view.case.requested_tooth),
                    "role": CHAIR_ROLE.get(rid), "hint": _action_hint(view, act), "capturable": rid in CAPTURABLE})
    return out


def gap_summary(view: CaseView) -> str:
    """Ophi's finding in one line, split by who can close it, so it adds up to what's still undocumented."""
    a = view.assessment
    chair, desk = len(chair_actions(a)), len(desk_actions(a))
    if chair and desk:
        found = f"Ophi found {chair + desk} gaps: {chair} need the patient, {desk} at the desk."
    elif chair:
        found = f"Ophi found {plural(chair, 'gap')} that need{'s' if chair == 1 else ''} the patient."
    else:
        found = f"Ophi found {plural(desk, 'gap')} to fix at the desk."
    dentist = sum(1 for r in a.requirements if r.applicable and r.status not in (Status.SATISFIED, Status.AT_RISK)
                  and _awaiting_dentist_only(r))
    return found + (f" {view.case.treatment.provider.name} confirms {dentist} more." if dentist else "")


def _unblocked(view: CaseView, a: Action):
    return view.assessment.requirement(a.unblocks[0]) if a.unblocks else None


def advisory(view: CaseView) -> list[Action]:
    return [x for x in view.assessment.actions if not x.blocking]


# --- timing: the appointment is the deadline -------------------------------------------------------


def timing(view: CaseView, today: date) -> dict:
    """The one date that matters for this case right now, as a short chip for the person acting on it.
    Tone: 'bad' is late, 'warn' is due within two days (or Sun Life past its usual turnaround)."""
    st, stage = view.state, view.stage
    appt = st.booked_on or view.case.treatment.appointment_date
    out: dict = {"appt": appt, "appt_in": days_until(appt, today), "late": False, "tone": "", "text": ""}
    if view.test_run:  # nothing is really due on a test run; its deadlines would compete with real work
        return out
    if in_chair(view):  # now beats every date
        out.update(tone="warn", text="In the chair now")
        return out
    if appt and appt < today and stage not in (Stage.DONE, Stage.BOOK):
        out.update(tone="bad", late=True, text="Appointment passed")
        return out
    if stage in (*CHART_STAGES, Stage.DENTIST, Stage.SEND, Stage.RESUBMIT):
        if not appt:
            out.update(text="No appointment")
            return out
        sb = send_by(appt)
        left = (sb - today).days
        out.update(send_by=sb, send_in=left, late=left < 0)
        # Before sending, the visit or the dentist's signature is the gate; name the deadline for the step the case is on.
        verb = {Stage.PATIENT: "Visit needed", Stage.DENTIST: "Sign"}.get(stage, "Send")
        if left < 0:
            out.update(tone="bad", text=f"Late for {short_date(appt)} crown")
        else:
            out.update(tone="warn" if left <= 2 else "", text=f"{verb} {in_days(left)}" if left <= 2 else f"{verb} by {short_date(sb)}")
    elif stage == Stage.SUN_LIFE:
        waited = (today - st.submitted_on).days
        out.update(waited=waited, text="Sent today" if waited == 0 else f"Sent {plural(waited, 'day')} ago")
        if waited > SUN_LIFE_TURNAROUND_DAYS:
            out.update(tone="warn", late=True)
    elif stage == Stage.BOOK:
        left = (valid_until(st.decision.decided_on) - today).days
        if left <= BOOK_SOON_DAYS:  # a decision is valid for a year; only its last month is worth a chip
            out.update(tone="bad" if left < 0 else "warn", text=f"Book by {full_date(valid_until(st.decision.decided_on))}")
    elif stage == Stage.DONE:
        out.update(tone="ok", text=f"Booked {short_date(st.booked_on)}")
    return out


def advice(view: CaseView, t: dict, today: date) -> str | None:
    """The one recommendation a late case needs, in the words an MOA would use."""
    if view.stage == Stage.SUN_LIFE and t["late"]:
        return f"Past Sun Life's usual {SUN_LIFE_TURNAROUND_DAYS} days."
    if t["late"] and t["appt"] and t["appt"] < today:
        return "The appointment has passed. Rebook the patient."
    if t["late"] and t["appt"]:
        return (f"The crown is {long_date(t['appt'])}, sooner than Sun Life's usual {SUN_LIFE_TURNAROUND_DAYS} days. "
                "Move it, or tell the patient.")
    return None


def _payer(d) -> dict | None:
    return {"outcome": d.outcome, "on": d.decided_on, "reason": d.reason} if d else None


# --- board -----------------------------------------------------------------------------------------

# The board's columns, in the order the job happens: key, title, the stages it holds, who has the case, and
# what they do there (as "you ..." and as "<name> ..."). Booked cases close out the last column.
COLUMNS: list[tuple[str, str, tuple[Stage, ...], str | None, tuple[str, str]]] = [
    ("patient", "Needs the patient", (Stage.PATIENT,), "coordinator", ("book a visit", "books a visit")),
    ("prepare", "Paperwork", (Stage.PREPARE,), "coordinator", ("fix it in the PMS", "fixes it")),
    ("dentist", "Dentist review", (Stage.DENTIST,), "dentist", ("sign", "signs")),
    ("send", "Ready to send", (Stage.SEND,), "coordinator", ("send from the PMS", "sends it")),
    ("sun_life", "With Sun Life", (Stage.SUN_LIFE,), "sun_life", ("", "decides")),
    ("decision", "Decision back", (Stage.BOOK, Stage.RESUBMIT, Stage.DONE), "coordinator", ("book or resubmit", "books or resubmits")),
]
COLUMN_OF: dict[Stage, str] = {s: key for key, _, stages, _, _ in COLUMNS for s in stages}


def _can_confirm_early(view: CaseView) -> bool:
    return view.stage in CHART_STAGES and bool(pending_criteria(view.assessment)) and criteria_can_start(view.assessment)


def _is_mine(view: CaseView, t: dict, actor: Actor) -> bool:
    """Whether the viewer has something to do on this case today."""
    stage = view.stage
    if in_chair(view):
        return True  # the dentist orders the film, the desk sees the patient before they go
    if actor.is_dentist:
        return stage == Stage.DENTIST or _can_confirm_early(view)
    return OWNER[stage] == "coordinator" or (stage == Stage.SUN_LIFE and t["late"])


def card_action(view: CaseView, actor: Actor, today: date) -> dict:
    """The card's one line of work, plus at most one supporting line (`note`, or Sun Life's decision in `payer`)."""
    stage, st = view.stage, view.state
    provider = view.case.treatment.provider.name
    crit = pending_criteria(view.assessment)
    out: dict = {"title": "", "more": 0, "note": None, "payer": None, "waiting": None}
    if stage in CHART_STAGES and actor.is_dentist and _can_confirm_early(view) and not in_chair(view):
        out["title"] = f"Confirm {plural(crit, 'clinical criterion', 'clinical criteria')}"
    elif stage == Stage.PATIENT:
        # One visit closes every chair gap, so the card names them together.
        todo = ", ".join(i["label"] for i in chair_items(view))
        appt = view.case.treatment.appointment_date
        late = appt and send_by(appt) < today  # no visit can save that date: the crown moves first
        visit = "Move the crown, then book a visit" if late else "Book a visit"
        out["title"] = f"Before {first_name(view)} leaves: {todo}" if in_chair(view) else f"{visit}: {todo}"
        desk = len(desk_actions(view.assessment))
        if desk:
            out["note"] = f"+{plural(desk, 'desk fix', 'desk fixes')}"
    elif stage == Stage.PREPARE:
        work = chart_actions(view.assessment)
        out.update(title=action_title(work[0]) if work else "Check the procedure code", more=max(len(work) - 1, 0))
        if _can_confirm_early(view):
            out["note"] = f"{provider} can confirm criteria now"
    elif stage == Stage.DENTIST:
        out["title"] = f"Confirm {plural(crit, 'clinical criterion', 'clinical criteria')}" if crit else "Review and sign the packet"
    elif stage == Stage.SEND:
        out["title"] = "Send the packet from your PMS"
    elif stage == Stage.SUN_LIFE:
        out["title"] = "Check your CDAnet mailbox" if (today - st.submitted_on).days > SUN_LIFE_TURNAROUND_DAYS else "Waiting for the decision"
    elif stage == Stage.BOOK:
        out.update(title="Call the patient to book", payer=_payer(st.decision))
    elif stage == Stage.RESUBMIT:
        appt = view.case.treatment.appointment_date
        late = appt and send_by(appt) < today  # a new request can't be back in time: the appointment moves first
        out.update(title="Move the appointment, then resubmit" if late else "Resubmit, or ask for reconsideration", payer=_payer(st.decision))
    elif stage == Stage.DONE:
        out["title"] = "Crown booked"
    if st.attempts and stage in (*CHART_STAGES, Stage.DENTIST, Stage.SEND):
        out["note"] = out["note"] or "Resubmission"
    return out


def card(view: CaseView, actor: Actor, today: date) -> dict:
    t = timing(view, today)
    # Late for the appointment first (a patient is affected), then Sun Life running past its usual turnaround,
    # then the nearest deadline (or the longest wait at Sun Life).
    due = t.get("send_by") or view.state.submitted_on or t["appt"] or date.max
    urgency = -1 if in_chair(view) else 3 if view.test_run else (1 if view.stage == Stage.SUN_LIFE else 0) if t["late"] else 2
    mine, act = _is_mine(view, t, actor), card_action(view, actor, today)
    if not mine and view.stage != Stage.DONE:
        act["waiting"] = who_label(OWNER[view.stage], actor, view.case.treatment.provider.name)
    return {"view": view, "case": view.case, "stage": view.stage, "timing": t, "action": act,
            "mine": mine, "advice": advice(view, t, today), "sort": (urgency, due),
            "chair": chair_items(view) if in_chair(view) else None, "first": first_name(view)}


def _mine_first(cards: list[dict]) -> list[dict]:
    """The viewer's cases, most urgent first."""
    return sorted((c for c in cards if c["mine"]), key=lambda c: c["sort"])


def board(views: list[CaseView], actor: Actor, today: date) -> dict:
    """Every preauthorization as a card in the column for the step it is on. Cards the viewer acts on are
    marked `mine`; the most urgent of them is `start`, the one thing to do first."""
    cards = [card(v, actor, today) for v in views if v.stage != Stage.NOT_NEEDED]
    provider = views[0].case.treatment.provider.name if views else "the dentist"
    columns = []
    for key, label, stages, owner, (you_do, they_do) in COLUMNS:
        cs = sorted((c for c in cards if c["stage"] in stages and c["stage"] != Stage.DONE), key=lambda c: c["sort"])
        cs += sorted((c for c in cards if c["stage"] in stages and c["stage"] == Stage.DONE),  # finished: last, newest first
                     key=lambda c: c["view"].state.booked_on, reverse=True)
        who = who_tag(owner, actor, provider) if owner else None
        job = f"{who['label']} {you_do if who['label'] == 'You' else they_do}" if who else they_do
        columns.append({"key": key, "label": label, "cards": cs, "who": who, "job": job,
                        "mine": owner == ("dentist" if actor.is_dentist else "coordinator")})
    mine = _mine_first(cards)
    n = len(mine)
    if actor.is_dentist:
        headline = f"{plural(n, 'case is', 'cases are')} waiting on you" if n else "Nothing is waiting on you"
    else:
        headline = f"{plural(n, 'case needs', 'cases need')} you" if n else "Nothing needs you today"
    late = sum(1 for c in mine if c["timing"]["late"])
    return {"today": today, "headline": headline, "late": late, "columns": columns, "start": mine[0] if mine else None,
            "checked": len(views)}


def next_up(views: list[CaseView], current: CaseView, actor: Actor, today: date) -> dict | None:
    """Once nothing on this case is the viewer's, their most urgent other case, so the next job is one click away."""
    if _is_mine(current, timing(current, today), actor):
        return None
    cards = [card(v, actor, today) for v in views if v.case.case_id != current.case.case_id and v.stage != Stage.NOT_NEEDED]
    mine = _mine_first(cards)
    return mine[0] if mine else None


# --- case page: the steps from chart to chair -----------------------------------------------------


def case_steps(view: CaseView) -> list[dict]:
    """The case's life as a sequence. Each step names who does it; the current one opens. Criteria can be
    confirmed while chart work is still open, so that step can be open alongside the current one."""
    a, st, stage = view.assessment, view.state, view.stage
    at = ORDER.index(stage)
    crit = pending_criteria(a)
    work = chart_actions(a)
    open_reqs = [r for r in a.requirements if r.applicable and r.status not in (Status.SATISFIED, Status.AT_RISK)]
    need_dentist = sum(1 for r in open_reqs if _awaiting_dentist_only(r))
    need_chart = len(open_reqs) - need_dentist
    check = f"{a.completeness['satisfied']} of {a.completeness['applicable']} CDCP requirements documented"
    if need_chart or need_dentist:
        check += "; " + ", ".join(p for p in (need_chart and f"{need_chart} need chart work", need_dentist and f"{need_dentist} need the dentist") if p)
    if stage == Stage.NOT_NEEDED:  # nothing to sign or send: the steps after the check don't apply
        return [{"key": "check", "title": "Ophi checked the chart", "who": "ophi", "state": "done", "n": 1, "summary": a.schedule.detail}]

    def state(step_stage: Stage) -> str:
        if stage == Stage.DONE:
            return "done"
        i = ORDER.index(step_stage)
        return "done" if i < at else ("current" if i == at else "upcoming")

    recorded = sum(1 for art in view.case.artifacts_of(ArtifactType.CLINICIAN_ASSERTION))
    steps = [{"key": "check", "title": "Ophi checked the chart", "who": "ophi", "state": "done", "summary": check}]

    chart = "current" if stage in CHART_STAGES else state(Stage.PREPARE)
    # While the patient is still in the chair the dentist's team closes the gaps; after, the desk books a visit.
    title = f"Before {first_name(view)} leaves" if in_chair(view) else "Book a visit" if stage == Stage.PATIENT else "Fix the paperwork"
    steps.append({"key": "chart", "title": title, "who": "dentist" if in_chair(view) else "coordinator", "state": chart,
                  "summary": plural(len(work), "gap") + " to close" if work else
                  ("Check the procedure code" if chart == "current" else "No gaps left in the chart")})

    if crit:
        early = stage in CHART_STAGES and criteria_can_start(a)
        crit_state = "current" if stage == Stage.DENTIST else ("open" if early else "upcoming")
        crit_summary = (f"{plural(crit, 'criterion', 'criteria')} to confirm" if crit_state != "upcoming"
                        else f"{plural(crit, 'criterion', 'criteria')}, once the films and perio chart are current")
    else:
        crit_state = "done"
        crit_summary = f"{plural(recorded, 'criterion', 'criteria')} recorded" if recorded else "None needed"
    steps.append({"key": "criteria", "title": "Confirm clinical criteria", "who": "dentist", "state": crit_state, "summary": crit_summary})

    if view.signed or st.sent:
        so = st.sign_off
        sign_state, sign_summary = "done", (f"Signed by {so.signed_by} on {short_date(so.signed_at.date())}" if so else "Signed")
    elif stage == Stage.DENTIST and not crit:
        sign_state, sign_summary = "current", "Ready for the dentist's review"
    else:
        sign_state, sign_summary = "upcoming", "Once the chart and criteria are complete"
    steps.append({"key": "sign", "title": "Review and sign the packet", "who": "dentist", "state": sign_state, "summary": sign_summary})

    steps.append({"key": "send", "title": "Send to Sun Life", "who": "coordinator", "state": state(Stage.SEND),
                  "summary": f"Sent {full_date(st.submitted_on)}" if st.submitted_on else
                  ("Download the packet and send it through your PMS" if stage == Stage.SEND else "After the dentist signs")})

    if st.decision:
        steps.append({"key": "decision", "title": "Sun Life's decision", "who": "sun_life", "state": "done", "payer": _payer(st.decision), "summary": ""})
    else:
        steps.append({"key": "decision", "title": "Sun Life's decision", "who": "sun_life", "state": state(Stage.SUN_LIFE),
                      "summary": "Record it when it arrives" if stage == Stage.SUN_LIFE else "Usually within 7 days of sending"})

    if st.decision and st.decision.outcome == "denied":
        steps.append({"key": "resubmit", "title": "Resubmit", "who": "coordinator", "state": "current",
                      "summary": "Send a new request, or ask for reconsideration", "reconsider_by": reconsider_by(st.decision.decided_on)})
    else:
        steps.append({"key": "book", "title": "Book the crown", "who": "coordinator",
                      "state": "done" if stage == Stage.DONE else ("current" if stage == Stage.BOOK else "upcoming"),
                      "summary": f"Booked for {long_date(st.booked_on)}" if st.booked_on else
                      ("Call the patient" if stage == Stage.BOOK else "After Sun Life's decision"),
                      "valid_until": valid_until(st.decision.decided_on) if st.decision else None})
    latest = "booked" if st.booked_on else ("decision" if st.decision else ("sent" if st.submitted_on else None))
    for n, s in enumerate(steps, start=1):
        s["n"] = n
        s["undo"] = {"send": "sent", "decision": "decision", "book": "booked"}.get(s["key"]) == latest and latest is not None
    return steps


def stepper(view: CaseView, actor: Actor) -> list[dict]:
    """The board's columns as this case's progress: done, the one it is on, and those still ahead."""
    if view.stage == Stage.NOT_NEEDED:
        return []
    at = [key for key, *_ in COLUMNS].index(COLUMN_OF[view.stage])
    provider = view.case.treatment.provider.name
    chair = in_chair(view)
    return [{"key": key, "label": label, "who": who_tag("dentist" if chair and key == "patient" else owner, actor, provider) if owner else None,
             "state": "done" if i < at or view.stage == Stage.DONE else ("current" if i == at else "upcoming")}
            for i, (key, label, _, owner, _) in enumerate(COLUMNS)]


def waiting_on(step: dict | None, actor: Actor, provider: str, t: dict) -> str | None:
    """Whom the case waits on when its open step isn't the viewer's to take, as the viewer names them."""
    if step is None:
        return None
    if step["key"] in ("criteria", "sign") and not actor.is_dentist:
        return provider
    if step["key"] == "chart" and actor.is_dentist and step["who"] == "coordinator":
        return ACTORS["coordinator"].name
    if step["key"] == "decision" and not t["late"]:
        return "Sun Life"
    return None


def now_step(steps: list[dict], actor: Actor) -> dict | None:
    """The step whose work the case page opens: the dentist's own step when they can act on it, else the current one."""
    if actor.is_dentist:
        mine = next((s for s in steps if s["key"] in ("criteria", "sign") and s["state"] in ("current", "open")), None)
        if mine:
            return mine
    return next((s for s in steps if s["state"] == "current"), None)


_ACTIVITY = {"assert": ("recorded a criterion", "recorded {n} criteria"), "confirm_proposal": ("reviewed a chart note", "reviewed {n} chart notes"),
             "edit_narrative": ("edited the narrative",), "sign_off": ("signed the packet",), "download_packet": ("downloaded the packet",),
             "mark_submitted": ("marked it sent",), "record_decision": ("recorded Sun Life's decision",),
             "start_resubmission": ("started a resubmission",), "mark_booked": ("marked the crown booked",),
             "undo": ("took back a step",), "recover_followup": ("logged a call-back",),
             "test_skip": ("skipped the chart gaps for a test run",), "test_restore": ("restored the skipped gaps",),
             "demo_capture": ("marked a chair gap taken (demo)", "marked {n} chair gaps taken (demo)")}


def activity(events: list) -> list[dict]:
    """This case's audit events, newest first, in plain words. A run of the same action by the same person in
    the same minute (the dentist answering nine criteria at once) reads as one line."""
    out: list[dict] = []
    for e in sorted(events, key=lambda e: e.at, reverse=True):
        last = out[-1] if out else None
        if last and last["event"] == e.event and last["actor"] == e.actor and last["at"].replace(second=0, microsecond=0) == e.at.replace(second=0, microsecond=0):
            last["n"] += 1
        else:
            out.append({"at": e.at, "actor": e.actor, "event": e.event, "n": 1})
    for item in out:
        forms = _ACTIVITY.get(item["event"], (item["event"].replace("_", " "),))
        item["what"] = forms[-1].format(n=item["n"]) if item["n"] > 1 and len(forms) > 1 else forms[0]
    return out


def audit_rows(events: list, names: dict[str, str]) -> list[dict]:
    """The clinic-wide log for Settings: newest first, a patient's name instead of a case id, plain words."""
    return [{"at": e.at, "actor": e.actor, "case_id": e.case_id, "patient": names.get(e.case_id, e.case_id), "event": e.event,
             "what": _ACTIVITY.get(e.event, (e.event.replace("_", " "),))[0], "detail": e.detail}
            for e in sorted(events, key=lambda e: e.at, reverse=True)]


# --- case review details ------------------------------------------------------------------------------


def _awaiting_dentist_only(r) -> bool:
    sf = r.shortfall
    return bool(sf.missing_assertions) and not (sf.missing or sf.stale or sf.undated or sf.incomplete or sf.pending_confirmation)


def requirement_detail(r) -> str:
    """The engine repeats 'awaiting the treating dentist's confirmation' per criterion; the criteria step
    already lists them, so collapse that case to a count. Anything else renders verbatim."""
    sf = r.shortfall
    if _awaiting_dentist_only(r):
        n = len(sf.missing_assertions)
        return f"Awaiting the treating dentist's confirmation of {n} {'criterion' if n == 1 else 'criteria'}."
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
    """Group the chart for the evidence fold. Recency facts come from the assessment, not recomputed."""
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
    relevant.sort(key=lambda r: r["current"] is not None)  # unanswered first
    return relevant, other


# --- packet ---------------------------------------------------------------------------------------


FILE_LABEL = {"index": "Index", "claim_form": "Claim form", "perio_chart": "Perio chart", "psr": "PSR",
              "narrative": "Narrative (Word)", "narrative_txt": "Narrative (text)"}


def _file_label(kind: str, artifact: ChartArtifact | None) -> str:
    """A packet file as staff would name it: 'PA #24', 'BW right', 'Narrative (Word)'."""
    pl = artifact.payload if artifact else None
    if isinstance(pl, RadiographPayload):
        return f"{pl.view.value} {pl.laterality.value}" if pl.laterality else f"{pl.view.value} {', '.join(f'#{t}' for t in pl.teeth_fdi[:2])}"
    return FILE_LABEL.get(kind, sentence(kind.replace("_", " ")))


def manifest_files(manifest: dict | None, case) -> list[dict]:
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
            "label": _file_label(f.get("kind") or "", case.artifact(f["artifact_id"]) if f.get("artifact_id") else None),
            "requirements": f.get("requirement_ids") or f.get("requirements") or [],
            "spec_ok": spec,
            "bytes": f.get("bytes"),
        })
    return out


def kb(n: int | None) -> str:
    return f"{(n or 0) / 1024:,.0f} KB"


# --- recover: past denials worth a call -----------------------------------------------------------

FOLLOWUP_LABEL = {"left_message": "Left a message", "rebooking": "Rebooking", "declined": "Not proceeding"}


def recover(rows: list[dict]) -> dict:
    """The call list: patients still to call first (largest fee first), then those in progress, then closed."""
    def status(x):
        return x["followup"].status if x["followup"] else None
    order = {None: 0, "left_message": 1, "rebooking": 2, "declined": 3}
    items = sorted(rows, key=lambda x: (order[status(x)], -x["row"].fee_dollars))
    to_call = [x for x in rows if status(x) in (None, "left_message")]
    rebooking = [x for x in rows if status(x) == "rebooking"]
    return {"calls": items, "count": len(rows), "dollars": sum(x["row"].fee_dollars for x in rows),
            "with_gap": sum(1 for x in rows if x["row"].gaps),
            "to_call": len(to_call), "to_call_dollars": sum(x["row"].fee_dollars for x in to_call),
            "rebooking": len(rebooking), "rebooking_dollars": sum(x["row"].fee_dollars for x in rebooking),
            "declined": sum(1 for x in rows if status(x) == "declined")}


# --- results: what Ophi has done for the clinic ---------------------------------------------------


def results(views: list[CaseView], pack: RulePack, report, recovered: dict) -> dict:
    """Plain facts for the owner, in the order they matter: treatment moving, gaps caught before they reached
    Sun Life, Sun Life's recorded decisions, past denials being won back, then staff time (an estimate).
    Test runs are left out: nothing they skipped was documented."""
    views = [v for v in views if not v.test_run]
    stages = [{"label": STAGE_LABEL[s], "count": sum(1 for v in views if v.stage == s),
               "dollars": sum(v.dollars_at_risk for v in views if v.stage == s)} for s in PIPELINE]
    labels = {r.id: r.label for r in pack.requirements}
    chair = {r.id for r in pack.requirements if r.gap.needs_patient}
    caught: dict[bool, dict[str, int]] = {True: {}, False: {}}  # needs the patient -> label -> times found
    cases_with_gaps = 0
    for v in views:
        gaps = v.state.first_check.gaps if v.state.first_check else []
        cases_with_gaps += bool(gaps)
        for rid in gaps:
            found = caught[rid in chair]
            found[labels.get(rid, rid)] = found.get(labels.get(rid, rid), 0) + 1
    # Past denials missing a film or perio chart: the gaps that cost the patient another visit.
    chair_docs = {labels[rid] for rid in chair & DOCUMENT_REQUIREMENTS}
    denied_for_chair = sum(1 for row in report.rows if row.decision == "denied" and chair_docs & set(row.gaps)) if report else 0
    sent = [v for v in views if v.state.submitted_on or v.state.attempts]
    # Every decision Sun Life has sent back, including those on earlier attempts, with the case's fee.
    decided = [(d.outcome, v.dollars_at_risk) for v in views
               for d in [x.decision for x in v.state.attempts] + ([v.state.decision] if v.state.decision else [])]
    approved = [fee for outcome, fee in decided if outcome == "approved"]
    denied = [fee for outcome, fee in decided if outcome == "denied"]
    checked = len(views)
    return {
        "in_progress": [s for s in stages if s["count"]],
        "in_progress_count": sum(s["count"] for s in stages), "in_progress_dollars": sum(s["dollars"] for s in stages),
        "caught_total": sum(n for found in caught.values() for n in found.values()), "caught_cases": cases_with_gaps,
        "caught_chair": sorted(caught[True].items(), key=lambda kv: (-kv[1], kv[0])),
        "caught_desk": sorted(caught[False].items(), key=lambda kv: (-kv[1], kv[0])),
        "taken_in_chair": sum(len(v.state.captures) for v in views if v.case.in_chair),
        "denied_for_chair": denied_for_chair,
        "sent": len(sent), "sent_dollars": sum(v.dollars_at_risk for v in sent),
        "approved": len(approved), "approved_dollars": sum(approved),
        "denied": len(denied), "denied_dollars": sum(denied),
        "waiting": sum(1 for v in views if v.stage == Stage.SUN_LIFE),
        "checked": checked, "hours": round(checked * MANUAL_MINUTES_PER_PREAUTH / 60, 1),
        "report": report, "recover": recovered,
    }
