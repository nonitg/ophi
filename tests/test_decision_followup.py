"""Sun Life's decision back into Ophi: from the PMS's own claims, or from the letter staff upload."""
from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from ophi import demo, letters
from ophi.service import CaseService, Store
from ophi.sources import abeldent
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


@pytest.fixture
def svc(tmp_path):
    s = CaseService(store=Store(tmp_path / "state"), pms_claims=lambda: abeldent.list_predeterminations(fake_sql),
                    note_reader=lambda text: "missing_radiograph")
    demo.seed(s)
    return s


def test_list_predeterminations_reads_status_and_electronic_answer():
    denied, approved, paper = abeldent.list_predeterminations(fake_sql)
    assert (denied.outcome, denied.decided_on, denied.benefit_cents) == ("denied", date(2026, 9, 17), 0)
    assert denied.reason == "A current periapical radiograph of tooth 24 was not received."
    assert (approved.outcome, approved.benefit_cents) == ("approved", 29050)
    assert (paper.answer_at, paper.status_label, paper.outcome) == ("paper", "Pred. Sent, expect paper response", None)


def test_sync_marks_sent_and_records_electronic_answers(svc):
    svc.sync_from_pms()
    assert svc.view("randal").stage == Stage.BOOK
    yok = svc.view("yokoyama")
    assert yok.stage == Stage.RESUBMIT and yok.state.decision.recorded_by == "ABELDent"
    assert yok.state.decision.reason_key == "missing_radiograph"
    cher = svc.view("cherski")
    assert cher.stage == Stage.SUN_LIFE and cher.pms.answer_at == "paper"


def test_resubmission_goes_to_the_column_the_reason_names_and_the_old_claim_stays_used(svc):
    svc.sync_from_pms()
    svc.start_resubmission("yokoyama", "Kim Osei", "missing_radiograph")
    svc.sync_from_pms()  # the earlier claim must not mark the new request sent
    v = svc.view("yokoyama")
    assert v.stage == Stage.PATIENT and v.state.submitted_on is None
    svc.resolve_ask("yokoyama", "Kim Osei")
    assert svc.view("yokoyama").stage == Stage.DENTIST


def test_read_letter_sends_a_pdf_as_a_document_and_a_photo_as_an_image():
    seen = []

    def reader(content):
        seen.append(content[0]["type"])
        return letters.LetterReading(outcome="denied", reason_key="insufficient_ferrule")

    assert letters.read_letter(b"%PDF", "application/pdf", reader).reason_key == "insufficient_ferrule"
    letters.read_letter(b"\x89PNG", "image/png", reader)
    assert seen == ["document", "image"]
    with pytest.raises(letters.LetterError):
        letters.read_letter(b"x", "text/plain", reader)


def test_uploaded_letter_prefills_the_decision_then_records_it(svc, tmp_path, monkeypatch):
    svc.sync_from_pms()
    reading = letters.LetterReading(outcome="denied", decided_on=date(2026, 9, 17), reason_key="insufficient_ferrule",
                                    reason="Less than 1.5 mm of sound tooth structure remains on tooth 26.")
    monkeypatch.setattr(letters, "read_letter", lambda data, media_type: reading)
    client = TestClient(create_app(svc=svc, packets_dir=tmp_path / "packets"), follow_redirects=False)
    r = client.post("/cases/cherski/letter", files={"letter": ("letter.pdf", b"%PDF", "application/pdf")})
    assert r.status_code == 200 and "Less than 1.5 mm of sound tooth structure" in r.text
    assert 'name="reason_key" value="insufficient_ferrule"' in r.text
    client.post("/cases/cherski/decision", data={"outcome": "denied", "decided_on": "2026-09-17",
                                                 "reason": reading.reason, "reason_key": "insufficient_ferrule"})
    assert svc.view("cherski").state.decision.reason_key == "insufficient_ferrule"
    client.post("/cases/cherski/resubmit", data={"reason_key": "insufficient_ferrule"})
    assert svc.view("cherski").stage == Stage.DENTIST
