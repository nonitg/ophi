"""A decided live case saved into the outcomes schema, so today's decisions train the next model."""

from __future__ import annotations

from datetime import date

import pytest

from ophi.casegen.dsl import build_case
from ophi.engine.assess import assess
from ophi.outcomes import store
from ophi.outcomes.from_live import (CHANNEL, attempt_id, reason_code, save_attempt, save_sent, submission_for,
                                     to_past_export)
from ophi.outcomes.training_set import SENT, VAGUE
from ophi.rules.loader import pack_for
from tests import _pg
from tests._cases import assess_dict, ready_dict

SENT_ON = date(2026, 9, 17)


def _case(d: dict | None = None):
    return build_case(d or ready_dict(), "inline")


def test_export_carries_everything_the_clinic_sent_plus_the_decision():
    d = to_past_export(_case(), attempt_id("inline", 1), SENT_ON, "denied", "missing_radiograph")
    assert set(SENT) <= set(d)  # the training set renders these fields; all must be built
    assert d["preauth_id"] == "inline#1" and d["submission_channel"] == CHANNEL
    assert d["submitted_date"] == "2026-09-17"
    assert d["decision"] == {"status": "denied", "reason_code": "DOC_MISSING_RADIOGRAPH", "reason_category": None}


def test_a_vague_denial_is_labelled_unspecified_not_dropped():
    assert reason_code("denied", None) == VAGUE
    assert reason_code("denied", "missing_radiograph") == "DOC_MISSING_RADIOGRAPH"
    assert reason_code("approved", None) is None


def test_submission_hashes_the_patient_before_it_leaves_the_case():
    sub = submission_for(_case(), "inline#1", SENT_ON, "denied", "missing_radiograph")
    assert sub.member_hash != "9001" and "9001" not in sub.member_hash
    assert sub.code == "27211" and sub.tooth_fdi == 46
    assert sub.outcome.status == "denied" and sub.outcome.reason_code == "DOC_MISSING_RADIOGRAPH"


@pytest.fixture(scope="module")
def conn():
    name, url = _pg.start()
    try:
        with store.connect(url) as c:
            store.migrate(c)
            yield c
    finally:
        _pg.stop(name)


def test_two_attempts_sit_side_by_side_so_the_fix_is_readable(conn):
    """The denied request and the approved one that followed are two rows on one case: the difference
    between them is the counterfactual the clinic wants back."""
    denied = ready_dict() | {"radiographs": []}
    save_attempt(conn, _case(denied), assess_dict(denied), attempt_id("inline", 1), SENT_ON, "denied", "missing_radiograph")
    approved = ready_dict()
    save_attempt(conn, _case(approved), assess_dict(approved), attempt_id("inline", 2), date(2026, 9, 24), "approved", None)

    rows = dict(conn.execute("select preauth_id, reason_code from outcomes.decision where preauth_id like 'inline#%'").fetchall())
    assert rows == {"inline#1": "DOC_MISSING_RADIOGRAPH", "inline#2": None}
    pa = dict(conn.execute(
        "select preauth_id, status from outcomes.requirement_result where requirement_id = 'radiograph_pa'"
        " and preauth_id like 'inline#%'").fetchall())
    assert pa["inline#1"] == "unsatisfied" and pa["inline#2"] == "satisfied"


def test_recording_the_same_decision_twice_replaces_the_row(conn):
    d = ready_dict()
    for _ in range(2):
        save_attempt(conn, _case(d), assess_dict(d), attempt_id("dup", 1), SENT_ON, "approved", None)
    assert conn.execute("select count(*) from outcomes.submission where preauth_id = 'dup#1'").fetchone()[0] == 1


def test_recording_a_decision_hands_the_attempt_to_the_sink(tmp_path):
    """The hook fires on the real service path, with the attempt number and the date it was sent -- a decision
    staff enter is the only moment the chart still describes what went out."""
    from ophi.packet.narrative import draft_narrative
    from ophi.service import CaseService, Store

    seen = []
    svc = CaseService(store=Store(tmp_path / "var"), record_outcome=lambda *a: seen.append(a))

    def send():
        v = svc.view("whitfield")
        svc.sign_off("whitfield", "Dr. Priya Lau", "ON-48213", draft_narrative(v.case, v.assessment, svc.pack))
        svc.mark_submitted("whitfield", "Kim Osei")

    send()
    sent_on = svc.store.load("whitfield").submitted_on
    svc.record_decision("whitfield", "denied", svc.today(), "No radiograph received.", "Kim Osei",
                        reason_key="missing_radiograph")
    assert seen == [("whitfield", 1, sent_on, "denied", "missing_radiograph")]

    svc.start_resubmission("whitfield", "Kim Osei", "missing_radiograph")
    send()
    svc.record_decision("whitfield", "approved", svc.today(), None, "Kim Osei")
    assert seen[-1][:2] == ("whitfield", 2)  # the second attempt is its own row, not an overwrite of the first


def test_the_channel_separates_machine_read_labels_from_administrator_ones(conn):
    """A live row's reason_code is Gemini's reading of the payer's words; an export's was assigned by an
    administrator. Training has to be able to tell them apart, and the channel is what does it."""
    d = ready_dict() | {"radiographs": []}
    save_attempt(conn, _case(d), assess_dict(d), attempt_id("prov", 1), SENT_ON, "denied", "missing_radiograph")
    rows = conn.execute("select channel from outcomes.submission where preauth_id = 'prov#1'").fetchall()
    assert rows == [(CHANNEL,)] and CHANNEL != "cdanet_eclaim"


def test_a_case_stores_every_attempt_it_makes(conn, tmp_path):
    """Three attempts, three rows, each with the chart that attempt went out with. A case is not guaranteed to
    settle in two, so nothing here may depend on the count."""
    from ophi.packet.narrative import draft_narrative
    from ophi.service import CaseService, Store

    svc = CaseService(store=Store(tmp_path / "var"))
    svc.record_outcome = lambda cid, n, on, outcome, key: save_sent(
        conn, svc.store.load(cid).snapshot, attempt_id(cid, n), on, outcome, key)

    def send():
        v = svc.view("whitfield")
        svc.sign_off("whitfield", "Dr. Priya Lau", "ON-48213", draft_narrative(v.case, v.assessment, svc.pack))
        svc.mark_submitted("whitfield", "Kim Osei")

    for reason in ("missing_radiograph", "insufficient_notes"):
        send()
        svc.record_decision("whitfield", "denied", svc.today(), "No.", "Kim Osei", reason_key=reason)
        svc.start_resubmission("whitfield", "Kim Osei", reason)
    send()
    svc.record_decision("whitfield", "approved", svc.today(), None, "Kim Osei")

    rows = dict(conn.execute("select preauth_id, reason_code from outcomes.decision "
                             "where preauth_id like 'whitfield#%' order by 1").fetchall())
    assert rows == {"whitfield#1": "DOC_MISSING_RADIOGRAPH", "whitfield#2": "DOC_INSUFFICIENT_NOTES", "whitfield#3": None}
    assert [a.sent is not None for a in svc.store.load("whitfield").attempts] == [True, True]


def test_the_snapshot_is_the_chart_as_sent_not_as_it_stands_now(tmp_path):
    """The point of the snapshot: staff fix the chart after a denial, and the denied attempt still reads as it
    was sent. Without it, a row labelled "denied, no radiograph" would carry a chart holding the radiograph."""
    from ophi.outcomes.case_export import to_export
    from ophi.packet.narrative import draft_narrative
    from ophi.service import CaseService, Store
    from tests._cases import ALL_CRITERIA

    svc = CaseService(store=Store(tmp_path / "var"))
    svc.skip_gaps("singh", "Kim Osei")  # singh is sent without its periapical film
    svc.assert_many("singh", [{"criterion_id": c, "value": "met"} for c in ALL_CRITERIA], "Dr. Priya Lau", "ON-48213")
    v = svc.view("singh")
    svc.sign_off("singh", "Dr. Priya Lau", "ON-48213", draft_narrative(v.case, v.assessment, svc.pack))
    svc.mark_submitted("singh", "Kim Osei")

    svc.record_decision("singh", "denied", svc.today(), "No film.", "Kim Osei", reason_key="missing_radiograph")
    svc.start_resubmission("singh", "Kim Osei", "missing_radiograph")
    svc.restore_gaps("singh", "Kim Osei")
    svc.record_capture("singh", "radiograph_pa", "Kim Osei")  # staff take the film the denial asked for

    kept = svc.store.load("singh").attempts[0].sent.export
    assert _films(kept) == 0  # the attempt that was denied still has no radiograph
    assert _films(to_export(svc.view("singh").case)) == 1  # the chart moved on; the stored attempt did not


def _films(export: dict) -> int:
    return sum(1 for a in export["attachments"] if a["type"] == "periapical_radiograph")


def test_an_archived_attempt_remembers_whether_a_dentist_signed_it(tmp_path):
    """`start_resubmission` clears the case's sign-off, so the snapshot is the only place an archived attempt
    can say it went out signed. A synced send and a signed send read alike on the assessment alone."""
    from ophi.packet.narrative import draft_narrative
    from ophi.service import CaseService, Store

    svc = CaseService(store=Store(tmp_path / "var"))
    v = svc.view("whitfield")
    svc.sign_off("whitfield", "Dr. Priya Lau", "ON-48213", draft_narrative(v.case, v.assessment, svc.pack))
    svc.mark_submitted("whitfield", "Kim Osei")
    svc.record_decision("whitfield", "denied", svc.today(), "No.", "Kim Osei", reason_key="missing_radiograph")
    svc.start_resubmission("whitfield", "Kim Osei", "missing_radiograph")

    st = svc.store.load("whitfield")
    assert st.sign_off is None  # the case's own signature is gone: each request is attested separately
    sent = st.attempts[0].sent
    assert sent.signed and sent.sign_off.signed_by == "Dr. Priya Lau"
