"""Sun Life's decision back into Ophi: from the PMS's own claims, or from the letter staff upload."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ophi import letters
from ophi.service import CaseService, Store
from ophi.sources import abeldent
from ophi.sources.pms_repository import AbelDentPmsRepository
from ophi.web.app import create_app
from ophi.workflow import Stage

# Rows as ABELDent returns them for the lab's fake Sun Life answers (lab/fixtures/fake-sunlife-responses.sql).
ROWS = [
    {"claim_id": 9001, "patient_id": 158, "code": "27211", "tooth": 24, "sent_on": "2026-09-10", "status": "P",
     "carrier_ref": "SL260910000158", "carrier": "Sun Life Assurance Company of Canada", "answered_on": "2026-09-17",
     "received": "A04=23|G05=E|G15-1=0|G26-1=A current periapical radiograph|G26-2=of tooth 24 was not received."},
    {"claim_id": 9002, "patient_id": 162, "code": "27211", "tooth": 26, "sent_on": "2026-09-08", "status": "P",
     "carrier_ref": "SL260908000162", "carrier": "Sun Life Assurance Company of Canada", "answered_on": "2026-09-15",
     "received": "A04=23|G05=E|G15-1=29050|G26-1=Predetermination approved."},
    {"claim_id": 9003, "patient_id": 160, "code": "27211", "tooth": 26, "sent_on": "2026-09-15", "status": "Q",
     "carrier_ref": "SL260915000160", "carrier": "Sun Life Assurance Company of Canada", "answered_on": "2026-09-15",
     "received": "A04=13|G05=H|G07=Response will be mailed to the office."},
]


def fake_sql(query, params):
    return ROWS


def fake_vm_sql(query, params=None):
    """The VM queries a case pull makes besides the charts: last chart write, crown appointments, dentist names."""
    if "dm_db_index_usage_stats" in query:
        return [{"u": None}]
    if "FROM apt" in query:
        return []
    return [{"id": "T", "name": "Dr. Terry Ackerman"}]


CHARTS = Path(__file__).parents[1] / "fixtures/abeldent/fictional"
YOKOYAMA, RANDAL, CHERSKI = "abeldent_158", "abeldent_162", "abeldent_160"


@pytest.fixture
def svc(tmp_path, monkeypatch):
    """ABELDent mode, with saved Fictional Data charts standing in for the VM."""
    repo = AbelDentPmsRepository()
    monkeypatch.setattr(repo, "planned_patient_ids", lambda: [158, 160, 162])
    monkeypatch.setattr(repo, "fetch_patient_charts", lambda pids: {p: json.loads((CHARTS / f"{p}.json").read_text()) for p in pids})
    monkeypatch.setattr(repo, "sql", fake_vm_sql)
    return CaseService(store=Store(tmp_path / "state"), repository=repo, clock=lambda: datetime(2026, 9, 26, 12),
                       pms_claims=lambda: abeldent.list_predeterminations(fake_sql), note_reader=lambda text: "missing_radiograph")


def test_list_predeterminations_reads_status_and_electronic_answer():
    denied, approved, paper = abeldent.list_predeterminations(fake_sql)
    assert (denied.outcome, denied.decided_on, denied.benefit_cents) == ("denied", date(2026, 9, 17), 0)
    assert denied.reason == "A current periapical radiograph of tooth 24 was not received."
    assert (approved.outcome, approved.benefit_cents) == ("approved", 29050)
    assert (paper.answer_at, paper.status_label, paper.outcome) == ("paper", "Pred. Sent, expect paper response", None)


def test_sync_marks_sent_and_records_electronic_answers(svc):
    svc.sync_from_pms()  # none is signed in Ophi: ABELDent is the record of what was sent
    assert svc.view(RANDAL).stage == Stage.BOOK
    yok = svc.view(YOKOYAMA)
    assert yok.stage == Stage.RESUBMIT and yok.state.decision.recorded_by == "ABELDent"
    assert yok.state.decision.reason_key == "missing_radiograph"
    cher = svc.view(CHERSKI)
    assert cher.stage == Stage.SUN_LIFE and cher.pms.answer_at == "paper"
    assert any("without a sign-off in Ophi" in e.detail for e in svc.store.audit_log(CHERSKI))


def test_resubmission_goes_to_the_column_the_reason_names_and_the_old_claim_stays_used(svc):
    svc.sync_from_pms()
    svc.start_resubmission(YOKOYAMA, "Kim Osei", "missing_radiograph")
    svc.sync_from_pms()  # the earlier claim must not mark the new request sent
    v = svc.view(YOKOYAMA)
    assert v.stage == Stage.PATIENT and v.state.submitted_on is None
    svc.resolve_ask(YOKOYAMA, "Kim Osei")
    assert svc.view(YOKOYAMA).state.ask.done_by == "Kim Osei"


def test_read_letter_passes_the_file_through_and_rejects_other_types():
    seen = []

    def reader(parts):
        seen.append(parts[0])
        return letters.LetterReading(outcome="denied", reason_key="insufficient_ferrule")

    assert letters.read_letter(b"%PDF", "application/pdf", reader).reason_key == "insufficient_ferrule"
    letters.read_letter(b"\x89PNG", "image/png", reader)
    assert seen == [(b"%PDF", "application/pdf"), (b"\x89PNG", "image/png")]
    with pytest.raises(letters.LetterError):
        letters.read_letter(b"x", "text/plain", reader)


def test_uploaded_letter_prefills_the_decision_then_records_it(svc, tmp_path, monkeypatch):
    svc.sync_from_pms()
    reading = letters.LetterReading(outcome="denied", decided_on=date(2026, 9, 17), reason_key="insufficient_ferrule",
                                    reason="Less than 1.5 mm of sound tooth structure remains on tooth 26.")
    monkeypatch.setattr(letters, "read_letter", lambda data, media_type: reading)
    client = TestClient(create_app(auto_rules_check=False, svc=svc, packets_dir=tmp_path / "packets"), follow_redirects=False)
    r = client.post(f"/cases/{CHERSKI}/letter", files={"letter": ("letter.pdf", b"%PDF", "application/pdf")})
    assert r.status_code == 200 and "Less than 1.5 mm of sound tooth structure" in r.text
    assert 'name="reason_key" value="insufficient_ferrule"' in r.text
    client.post(f"/cases/{CHERSKI}/decision", data={"outcome": "denied", "decided_on": "2026-09-17",
                                                 "reason": reading.reason, "reason_key": "insufficient_ferrule"})
    assert svc.view(CHERSKI).state.decision.reason_key == "insufficient_ferrule"
    client.post(f"/cases/{CHERSKI}/resubmit", data={"reason_key": "insufficient_ferrule"})
    assert svc.view(CHERSKI).state.ask.stage == Stage.DENTIST
