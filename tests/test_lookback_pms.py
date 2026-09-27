"""The Look-Back over the clinic's own predeterminations, instead of the fictional history under cases/.

Charts are the saved Fictional Data dumps, so none of this needs the lab VM.
"""
from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

import pytest

from ophi.service import CaseService, Store
from ophi.sources import abeldent
from ophi.sources.pms_lookback import PmsLookBack, lookback_rows

CHARTS = Path(__file__).parents[1] / "fixtures/abeldent/fictional"
YOKOYAMA, CHERSKI = 158, 160
CROWN_TRANS_ID = 1178  # the planned 27211 on #24 in patient 158's chart

# Rows as ABELDent returns them: a denial with an electronic answer, and one Sun Life will answer on paper.
ROWS = [
    {"claim_id": 9001, "patient_id": YOKOYAMA, "code": "27211", "tooth": 24, "sent_on": "2026-09-10", "status": "P",
     "trans_id": CROWN_TRANS_ID, "fee_cents": 128500, "patient_name": "Aiko Yokoyama",
     "carrier_ref": "SL260910000158", "carrier": "Sun Life Assurance Company of Canada", "answered_on": "2026-09-17",
     "received": "A04=23|G05=E|G15-1=0|G26-1=A current periapical radiograph|G26-2=of tooth 24 was not received."},
    {"claim_id": 9003, "patient_id": CHERSKI, "code": "27211", "tooth": 26, "sent_on": "2026-09-15", "status": "Q",
     "trans_id": 1107, "fee_cents": 58100, "patient_name": "Ana Cherski",
     "carrier_ref": "SL260915000160", "carrier": "Sun Life Assurance Company of Canada", "answered_on": "2026-09-15",
     "received": "A04=13|G05=H|G07=Response will be mailed to the office."},
]


def chart(pid: int) -> dict:
    return json.loads((CHARTS / f"{pid}.json").read_text())


def fetch_charts(pids, charts=None):
    return {p: (charts or {}).get(p) or chart(p) for p in pids}


@pytest.fixture
def claims():
    return abeldent.list_predeterminations(lambda q, p: ROWS)


def test_rows_re_derive_the_gap_and_skip_answers_still_to_come(claims):
    rows, undecided = lookback_rows(claims, fetch_charts)
    assert [r.case_id for r in rows] == ["pred_9001"]  # the paper answer carries no decision yet
    assert undecided == 1
    row = rows[0]
    assert (row.patient_name, row.tooth_fdi, row.decision, row.fee_dollars) == ("Aiko Yokoyama", 24, "denied", 1285.0)
    # Sun Life's words are carried but never trusted: the engine names the missing document itself.
    assert any("periapical" in g for g in row.gaps)
    assert row.denial_text == "A current periapical radiograph of tooth 24 was not received."
    # A chart dump holds no clinician assertions, so nothing rests on one being called "still open".
    assert row.other_open == []


def test_a_film_taken_since_the_denial_does_not_close_the_gap(claims):
    """The patient came in after the denial. The chart shows the film today; it was not there when this was sent."""
    later = copy.deepcopy(chart(YOKOYAMA))
    later["imaging"]["procedure_events"].append(
        {"trans_id": 99999, "code": "02111", "tooth_fdi": 24, "date": "2026-09-20"})
    rows, _ = lookback_rows(claims, lambda pids: fetch_charts(pids, {YOKOYAMA: later}))
    row = rows[0]
    assert any("periapical" in g for g in row.gaps), "a film dated after the submission must not satisfy it"
    assert not any("periapical" in u for u in row.unverifiable), "nor read as one the PMS could not show"


def test_a_film_taken_before_the_denial_closes_the_gap(claims):
    """The control for the test above: the same film, dated before it was sent, is evidence."""
    earlier = copy.deepcopy(chart(YOKOYAMA))
    earlier["imaging"]["procedure_events"].append(
        {"trans_id": 99999, "code": "02111", "tooth_fdi": 24, "date": "2026-09-01"})
    rows, _ = lookback_rows(claims, lambda pids: fetch_charts(pids, {YOKOYAMA: earlier}))
    assert not any("periapical" in g for g in rows[0].gaps)


def test_a_second_request_for_the_same_tooth_counts_as_resubmitted():
    resent = dict(ROWS[0], claim_id=9009, sent_on="2026-09-20",
                  received="A04=23|G05=E|G15-1=29050|G26-1=Predetermination approved.")
    claims = abeldent.list_predeterminations(lambda q, p: [ROWS[0], resent])
    rows, _ = lookback_rows(claims, fetch_charts)
    first = next(r for r in rows if r.case_id == "pred_9001")
    assert (first.resubmitted, first.resubmitted_decision) == (True, "approved")


def test_the_call_list_reads_from_the_pms_and_records_a_follow_up(tmp_path, claims):
    svc = CaseService(store=Store(tmp_path / "state"), clock=lambda: datetime(2026, 9, 27, 12),
                      lookback_report=PmsLookBack(_FakeRepo(claims)).report)
    rows = svc.recover_rows()
    assert [x["row"].case_id for x in rows] == ["pred_9001"]
    svc.record_followup("pred_9001", "left_message", "called, no answer", "Kim Osei")
    assert svc.recover_rows()[0]["followup"].status == "left_message"


def test_follow_ups_against_an_earlier_history_are_counted_not_hidden(tmp_path, claims):
    svc = CaseService(store=Store(tmp_path / "state"), clock=lambda: datetime(2026, 9, 27, 12),
                      lookback_report=PmsLookBack(_FakeRepo(claims)).report)
    svc.store.add_followup("lb07", _followup())
    assert svc.orphan_followups() == 1


def _followup():
    from ophi.service import FollowUp
    return FollowUp(status="left_message", note=None, by="Kim Osei", at=datetime(2026, 8, 15, 9))


class _FakeRepo:
    """The VM's answers for a look-back build: the change stamp, the dentist names, the charts."""

    def __init__(self, claims):
        self._claims = claims

    def sql(self, query, params=None):
        if "dm_db_index_usage_stats" in query:  # the stamp names Claim too, so it has to be matched first
            return [{"charts": "2026-09-27T09:00:00.000", "claims": 9003}]
        if "IsPredetermination" in query:
            return ROWS
        return [{"id": "T", "name": "Dr. Terry Ackerman"}]

    def fetch_patient_charts(self, pids):
        return fetch_charts(pids)


def test_recover_page_shows_the_pms_rows_and_takes_a_follow_up(tmp_path, claims):
    from fastapi.testclient import TestClient

    from ophi.web.app import create_app

    svc = CaseService(store=Store(tmp_path / "state"), clock=lambda: datetime(2026, 9, 27, 12),
                      lookback_report=PmsLookBack(_FakeRepo(claims)).report)
    client = TestClient(create_app(auto_rules_check=False, svc=svc, packets_dir=tmp_path / "packets", live_ml=False),
                        follow_redirects=False)
    page = client.get("/recover")
    assert page.status_code == 200
    assert "Aiko Yokoyama" in page.text and "periapical" in page.text
    assert client.post("/recover/pred_9001", data={"status": "left_message", "note": ""}).status_code == 303
    assert "Left a message" in client.get("/recover").text


def test_a_paper_answer_then_a_resend_is_still_reported():
    """Sun Life answered the first attempt on paper, so only the resend's answer ever reached the PMS. The
    request is judged from that answer rather than dropped: paper answers are most of the denials at many
    clinics, and a request that falls out of both the numerator and the denominator skews the denial rate."""
    paper = dict(ROWS[0], claim_id=9101, sent_on="2026-08-01", status="Q",
                 received="A04=13|G05=H|G07=Response will be mailed to the office.")
    resent = dict(ROWS[0], claim_id=9102, sent_on="2026-09-10", status="P",
                  received="A04=23|G05=E|G15-1=0|G26-1=A current periapical radiograph was not received.")
    rows, undecided = lookback_rows(abeldent.list_predeterminations(lambda q, p: [paper, resent]), fetch_charts)
    assert [r.case_id for r in rows] == ["pred_9102"] and undecided == 0
    # Nothing was sent after the answer we can read, so it is still worth a call.
    assert rows[0].decision == "denied" and not rows[0].resubmitted
