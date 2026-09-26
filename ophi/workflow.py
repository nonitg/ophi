"""Where each preauthorization is in its life, who acts next, and by when.

A case's stage is derived, never stored: the assessment plus the steps people recorded (sign-off,
submission, Sun Life's decision, booking) decide it. The dates here are scheduling guidance from
published figures. They never predict what Sun Life will decide.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from dateutil.relativedelta import relativedelta

from ophi.engine.models import Assessment, RequirementResult, Status, Verdict

# Health Canada, reported by Oral Health Group (2026-06-18): "more than 95 per cent of preauthorization
# requests are now processed within seven days". Guidance for planning, not a Sun Life service level.
SUN_LIFE_TURNAROUND_DAYS = 7
TURNAROUND_SOURCE = ("Health Canada, via Oral Health Group, June 2026",
                     "https://www.oralhealthgroup.com/dental-governance-regulations/cdcp-update-less-than-half-of-dental-preauthorization-requests-approved-as-new-trends-emerge-1003996608/")
# CDCP Dental Benefits Guide, "Preauthorization validity": decisions are valid for up to 12 months from the
# date of approval, while the client is still enrolled on the date of service.
DECISION_VALID_MONTHS = 12
# CDCP Dental Benefits Guide, Appendix C: reconsideration within 60 days of the denial, with new clinical
# information; one level, and its decision is final.
RECONSIDERATION_DAYS = 60


class Stage(StrEnum):
    PREPARE = "prepare"      # chart gaps the coordinator closes
    DENTIST = "dentist"      # only the treating dentist's confirmations or signature remain
    SEND = "send"            # signed; the clinic submits it through its PMS
    SUN_LIFE = "sun_life"    # submitted; waiting on Sun Life
    BOOK = "book"            # Sun Life approved it; book the crown
    RESUBMIT = "resubmit"    # Sun Life denied it; fix and send a new request
    DONE = "done"            # the crown appointment is booked
    NOT_NEEDED = "not_needed"  # no preauthorization rule applies to this code


# Lifecycle order: the worklist groups and the case page steps both follow it.
ORDER = [Stage.PREPARE, Stage.DENTIST, Stage.SEND, Stage.SUN_LIFE, Stage.BOOK, Stage.RESUBMIT, Stage.DONE, Stage.NOT_NEEDED]

OWNER: dict[Stage, str | None] = {
    Stage.PREPARE: "coordinator", Stage.DENTIST: "dentist", Stage.SEND: "coordinator", Stage.SUN_LIFE: "sun_life",
    Stage.BOOK: "coordinator", Stage.RESUBMIT: "coordinator", Stage.DONE: None, Stage.NOT_NEEDED: None,
}


def chart_actions(a: Assessment) -> list:
    """Blocking work on the chart itself; staff do it, not the dentist."""
    return [x for x in a.actions if x.blocking and x.action_type != "assert"]


def dentist_actions(a: Assessment) -> list:
    return [x for x in a.actions if x.blocking and x.action_type == "assert"]


# The dentist judges crown-to-root ratio, margin, ferrule and furcation on the films, and active disease on the
# perio chart. While either is missing or stale, the criteria wait for it.
CLINICAL_EVIDENCE = {"radiograph_pa", "radiograph_bw", "perio_chart"}


def criteria_can_start(a: Assessment) -> bool:
    """True when the chart work still open is paperwork (a code, a form, a quote to confirm), not evidence
    the dentist needs in front of them to answer."""
    return not any(set(x.unblocks) & CLINICAL_EVIDENCE for x in chart_actions(a))


def pending_criteria(a: Assessment) -> int:
    """Clinical criteria still waiting on the dentist, counted across every requirement that asks for them."""
    return len({c for r in a.requirements if r.applicable for c in r.shortfall.missing_assertions})


def stage_of(assessment: Assessment, signed: bool, submitted_on: date | None, outcome: str | None, booked_on: date | None) -> Stage:
    if booked_on:
        return Stage.DONE
    if outcome:
        return Stage.BOOK if outcome == "approved" else Stage.RESUBMIT
    if submitted_on:
        return Stage.SUN_LIFE
    if signed:
        return Stage.SEND
    if assessment.verdict == Verdict.PREAUTH_NOT_REQUIRED:
        return Stage.NOT_NEEDED
    if assessment.verdict == Verdict.EXCLUDED_AS_CODED or chart_actions(assessment):
        return Stage.PREPARE
    return Stage.DENTIST


def send_by(appointment: date | None) -> date | None:
    """The last day to send and still leave Sun Life its usual turnaround before the appointment."""
    return appointment - relativedelta(days=SUN_LIFE_TURNAROUND_DAYS) if appointment else None


def valid_until(decided_on: date) -> date:
    return decided_on + relativedelta(months=DECISION_VALID_MONTHS)


def reconsider_by(decided_on: date) -> date:
    return decided_on + relativedelta(days=RECONSIDERATION_DAYS)


def documentation_gaps(a: Assessment) -> list[RequirementResult]:
    """Requirements Ophi found missing, stale, undated or incomplete in the chart. What the source couldn't show
    (indeterminate) is not counted as found, and waiting on the dentist is a step, not a gap."""
    out = []
    for r in a.requirements:
        sf = r.shortfall
        if r.applicable and r.status == Status.UNSATISFIED and (sf.missing or sf.stale or sf.undated or sf.incomplete):
            out.append(r)
    return out
