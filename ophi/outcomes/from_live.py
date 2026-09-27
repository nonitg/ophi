"""A decided live case -> the outcomes schema, so today's denials train the next model.

Past requests reach the training set through an administrator export; a case Ophi ran itself never did, so
every decision the clinic recorded was learning thrown away. The chart is exported at the moment the decision
is recorded, which is the last moment it still describes what was sent -- staff start fixing right afterwards,
and a resubmission's chart is a different request. Each attempt is its own row (`<case id>#<n>`), so a denial
and the approval that followed sit side by side and the difference between them is readable.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date

import psycopg

from ophi.cdm.models import Case
from ophi.engine.models import Assessment
from ophi.outcomes import store
from ophi.outcomes.adapter import PastSubmission, to_submission
from ophi.outcomes.case_export import to_export
from ophi.outcomes.denial_map import EXPORT_CODE
from ophi.outcomes.training_set import VAGUE

log = logging.getLogger("uvicorn.error")

# Tells a live-recorded request apart from an administrator export, which is also the label-provenance marker
# the training set needs: an export's reason_code was assigned by an administrator, while a live row's was read
# off the payer's words by Gemini and may be wrong. Filter or down-weight on this rather than trusting both alike.
CHANNEL = "ophi"


def attempt_id(case_id: str, attempt: int) -> str:
    """Attempts are numbered from 1 in the order they were sent."""
    return f"{case_id}#{attempt}"


def reason_code(outcome: str, reason_key: str | None) -> str | None:
    """A denial whose letter named no reason is Sun Life's vague letter, which the training set labels
    UNSPECIFIED rather than dropping -- a vague denial is still a denial."""
    if outcome != "denied":
        return None
    return EXPORT_CODE.get(reason_key or "") or VAGUE


def with_decision(export: dict, preauth_id: str, submitted_on: date, outcome: str, reason_key: str | None) -> dict:
    """An export of the sent chart, named and labelled with Sun Life's answer."""
    return export | {
        "preauth_id": preauth_id,
        "submission_channel": CHANNEL,
        "submitted_date": submitted_on.isoformat(),
        "decision": {"status": outcome, "reason_code": reason_code(outcome, reason_key), "reason_category": None},
    }


def to_past_export(case: Case, preauth_id: str, submitted_on: date, outcome: str, reason_key: str | None) -> dict:
    """The case as it stands now, in the shape past requests come in. Only right for an attempt still in flight;
    an attempt already resubmitted must go through its stored snapshot instead."""
    return with_decision(to_export(case), preauth_id, submitted_on, outcome, reason_key)


def submission_for(case: Case, preauth_id: str, submitted_on: date, outcome: str, reason_key: str | None) -> PastSubmission:
    return to_submission(to_past_export(case, preauth_id, submitted_on, outcome, reason_key))


def save_attempt(conn: psycopg.Connection, case: Case, a: Assessment | None, preauth_id: str, submitted_on: date,
                 outcome: str, reason_key: str | None) -> None:
    """Idempotent per attempt: recording the same decision twice replaces the row rather than adding one."""
    store.save(conn, submission_for(case, preauth_id, submitted_on, outcome, reason_key), a)
    conn.commit()


def sink(svc, connect=store.connect) -> Callable[[str, int, date, str, str | None], None]:
    """The hook CaseService calls when staff record a decision. Reassessing here rather than reusing the page's
    reading keeps the stored requirement results the engine's own, on the pack in force for the request's date.

    An unreachable database is logged and swallowed: a clinic must still be able to record Sun Life's answer when
    Supabase is down. The row is lost, not the decision -- scripts/backfill-live-outcomes.py sends it later.
    """

    def record(case_id: str, attempt: int, submitted_on: date, outcome: str, reason_key: str | None) -> None:
        try:
            pid = attempt_id(case_id, attempt)
            sent = svc.store.load(case_id).snapshot  # frozen when this attempt was sent
            with connect() as conn:
                if sent is not None:
                    save_sent(conn, sent, pid, submitted_on, outcome, reason_key)
                else:  # no snapshot (an older case, or a chart Ophi could not read): the chart as it stands now
                    case, a = svc.assess_under(case_id, svc.pack_for(svc.base_case(case_id)))
                    save_attempt(conn, case, a, pid, submitted_on, outcome, reason_key)
        except Exception:  # noqa: BLE001 — any store or connection failure
            log.warning("outcomes: could not record %s attempt %d for training", case_id, attempt, exc_info=True)

    return record


def save_sent(conn: psycopg.Connection, sent, preauth_id: str, submitted_on: date, outcome: str,
              reason_key: str | None) -> None:
    """One attempt, from the snapshot frozen when it was sent (`service.Sent`). This is what makes a case with
    any number of attempts storable: each row carries the chart that attempt actually went out with."""
    d = with_decision(sent.export, preauth_id, submitted_on, outcome, reason_key)
    store.save(conn, to_submission(d), Assessment.model_validate(sent.assessment))
    conn.commit()
