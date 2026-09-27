"""The Recover slice: a call-back date, a call history, and a past denial finding its way back to the board."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ophi.lookback import LookBackReport, LookBackRow
from ophi.service import CaseService, Store
from ophi.web.app import create_app


@pytest.fixture
def svc(tmp_path: Path) -> CaseService:
    return CaseService(store=Store(tmp_path / "state"))


@pytest.fixture
def client(svc: CaseService, tmp_path: Path) -> TestClient:
    return TestClient(create_app(auto_rules_check=False, svc=svc, packets_dir=tmp_path / "packets"),
                      follow_redirects=True)


def a_row(svc: CaseService, **over) -> LookBackRow:
    """A denial for a crown that is also planned on the board -- the clinic took it back up."""
    case = svc.base_case(svc.case_ids()[0])
    fields = dict(case_id="pred_1", patient_label="M.D.", patient_name=case.patient.display_name,
                  code=case.treatment.code, tooth_fdi=case.requested_tooth, submitted_on=date(2025, 11, 4),
                  decision="denied", fee_dollars=1120.0, gaps=["Periapical radiograph of the requested tooth"])
    return LookBackRow(**(fields | over))


def a_report(rows: list[LookBackRow]) -> LookBackReport:
    denied = [r for r in rows if r.decision == "denied"]
    return LookBackReport(window_label="last 12 months", ruleset_version="test", submitted=len(rows),
                          denied=len(denied), denied_dollars=sum(r.fee_dollars for r in denied), approved=0,
                          denied_with_doc_gap=len(denied), denied_with_doc_gap_dollars=0.0,
                          never_resubmitted=len(denied), never_resubmitted_dollars=0.0, rows=rows)


def test_a_call_back_date_is_recorded_and_every_call_is_kept(svc: CaseService):
    row_id = svc.recover_rows()[0]["row"].case_id
    soon = svc.today() + timedelta(days=3)
    svc.record_followup(row_id, "left_message", "no answer", "Kim Osei")
    svc.record_followup(row_id, "rebooking", "wants to come in", "Kim Osei", callback_on=soon)

    x = next(x for x in svc.recover_rows() if x["row"].case_id == row_id)
    assert [c.status for c in x["calls"]] == ["left_message", "rebooking"]
    assert x["followup"].callback_on == soon  # the list shows the latest call, the history keeps the rest


def test_a_call_back_date_in_the_past_is_refused(svc: CaseService):
    row_id = svc.recover_rows()[0]["row"].case_id
    with pytest.raises(ValueError, match="in the past"):
        svc.record_followup(row_id, "left_message", None, "Kim Osei", callback_on=svc.today() - timedelta(days=1))


def test_a_patient_not_proceeding_takes_no_call_back_date(svc: CaseService):
    row_id = svc.recover_rows()[0]["row"].case_id
    with pytest.raises(ValueError, match="not proceeding"):
        svc.record_followup(row_id, "declined", None, "Kim Osei", callback_on=svc.today() + timedelta(days=7))


def test_a_denial_whose_crown_is_planned_again_links_to_the_board(svc: CaseService):
    """Ophi never writes to the PMS, so a reopened denial is recognised, not created: the clinic re-plans the
    crown and the row finds it by patient, code and tooth."""
    svc.lookback_report = lambda: a_report([a_row(svc)])
    x = svc.recover_rows()[0]
    assert x["case_id"] == svc.case_ids()[0]
    assert [r["case_id"] for r in svc.recovered_rows()] == [svc.case_ids()[0]]


def test_a_denial_with_no_matching_board_case_stays_on_the_call_list(svc: CaseService):
    svc.lookback_report = lambda: a_report([a_row(svc, patient_name="Nobody At All", tooth_fdi=48)])
    assert svc.recover_rows()[0]["case_id"] is None
    assert svc.recovered_rows() == []


def test_the_page_says_a_crown_is_back_on_the_board(svc: CaseService, client: TestClient):
    svc.lookback_report = lambda: a_report([a_row(svc)])
    page = client.get("/recover").text
    assert "back on the board" in page
    assert f'href="/cases/{svc.case_ids()[0]}"' in page


def test_an_overdue_call_back_is_called_out(svc: CaseService, client: TestClient):
    row_id = svc.recover_rows()[0]["row"].case_id
    svc.record_followup(row_id, "left_message", None, "Kim Osei", callback_on=svc.today())
    assert "to call back today" in client.get("/recover").text


def test_the_script_route_never_shows_a_draft_that_fails_its_own_check(svc: CaseService, client: TestClient,
                                                                      monkeypatch):
    """The drafter is a model; the verifier is not. A draft that quotes a fee is withheld, not shown."""
    import ophi.web.app as web
    from ophi.letters import LetterError

    def refuses(*_a, **_k):
        raise LetterError("the draft quoted a fee")

    row = svc.recover_rows()[0]["row"]
    monkeypatch.setattr(web, "draft_call_script", refuses)
    page = client.post(f"/recover/{row.case_id}/script").text
    assert "the draft quoted a fee" in page
    assert "call-script-text" not in page  # nothing a staffer could read aloud
