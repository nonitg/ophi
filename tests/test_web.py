"""Web layer against a fresh Store. Packet-dependent asserts skip when the packet module has not landed."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from ophi.service import CaseService, Store
from ophi.web.app import create_app

RESTORABILITY = ["no_active_perio", "crown_root_ratio", "no_furcation", "margin_3mm", "ferrule_1_5mm",
                 "mesiodistal_space", "no_adjunctive_needed"]
ALL_TREMBLAY = RESTORABILITY + ["extensively_restored", "active_disease_addressed", "endo_healed"]

# Ophi's own voice never predicts payer behaviour. Chart quotes and Sun Life text are exempt.
FORBIDDEN = re.compile(r"\b(will be approved|approved|eligible|covered|likely|probability)\b", re.I)


@pytest.fixture
def client(tmp_path):
    svc = CaseService(store=Store(tmp_path / "state"))
    app = create_app(svc=svc, packets_dir=tmp_path / "packets")
    return TestClient(app, follow_redirects=False)


def as_dentist(client: TestClient) -> None:
    client.cookies.set("actor", "dentist")


def _draft(case_id: str) -> str:
    """The template narrative for a demo case, as the packet screen would prefill it."""
    from ophi.casegen.dsl import load_case
    from ophi.engine.assess import assess
    from ophi.extract.proposer import propose_for_case
    from ophi.packet.narrative import draft_narrative
    from ophi.rules.loader import default_pack
    from ophi.service import CASES_DIR
    case = load_case(CASES_DIR / f"{case_id}.yaml")
    case = case.with_artifacts(propose_for_case(case))
    return draft_narrative(case, assess(case, default_pack()), default_pack())


def test_queue_lists_cases_with_verdicts(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Kowalchuk" in r.text
    assert "Blocked" in r.text
    assert "of treatment at risk" in r.text


def test_case_review_shows_the_bitewing_explanation(client):
    r = client.get("/cases/singh")
    assert r.status_code == 200
    assert "Bitewings do not image the periapical region" in r.text
    assert "9 of 13" in r.text
    assert "6.3.5 Crowns" in r.text  # every gap carries its clause


def test_assert_requires_dentist(client):
    r = client.post("/cases/singh/assert", data={"criterion_id": "ferrule_1_5mm", "value": "met"})
    assert r.status_code == 403


def test_assert_as_dentist_is_recorded_and_attributed(client):
    as_dentist(client)
    r = client.post("/cases/singh/assert", data={"criterion_id": "ferrule_1_5mm", "value": "met", "note": "on the PA"})
    assert r.status_code == 303
    page = client.get("/cases/singh").text
    assert "Dr. Priya Lau" in page
    assert "on the PA" in page


def test_confirm_proposal_shows_confirmed_by(client):
    r = client.post("/cases/tremblay/proposals/note_0514.proposal1", data={"decision": "confirmed"})
    assert r.status_code == 303
    assert "Confirmed by" in client.get("/cases/tremblay").text


def test_unknown_proposal_is_404(client):
    assert client.post("/cases/tremblay/proposals/nope", data={"decision": "confirmed"}).status_code == 404


def complete_tremblay(client: TestClient) -> None:
    as_dentist(client)
    client.post("/cases/tremblay/proposals/note_0514.proposal1", data={"decision": "confirmed"})
    for cid in ALL_TREMBLAY:
        assert client.post("/cases/tremblay/assert", data={"criterion_id": cid, "value": "met"}).status_code == 303


def test_tremblay_happy_path_reaches_ready_then_signs_off(client):
    complete_tremblay(client)
    assert "ready for sign-off" in client.get("/cases/tremblay").text

    r = client.get("/cases/tremblay/packet")
    assert r.status_code == 200
    assert "I have reviewed this packet" in r.text

    # Browsers submit textareas with CRLF; the signed hash must still match the LF packet text.
    r = client.post("/cases/tremblay/sign-off", data={"narrative": "Crown #24 following endodontic treatment.\r\nAsymptomatic."})
    assert r.status_code == 303
    page = client.get("/cases/tremblay/packet").text
    assert "never transmits" in page
    assert "Dr. Priya Lau" in page
    assert "attestation.narrative_sha256" not in page  # verifier finding when hashes disagree

    assert client.post("/cases/tremblay/submitted").status_code == 303
    assert "Marked submitted" in client.get("/cases/tremblay/packet").text
    assert "Signed" in client.get("/").text


def test_sign_off_blocked_when_verdict_not_ready(client):
    as_dentist(client)
    r = client.post("/cases/singh/sign-off", data={"narrative": "x"})
    assert r.status_code == 409
    assert "Sign-off is blocked" in r.text


def test_sign_off_requires_dentist(client):
    assert client.post("/cases/whitfield/sign-off", data={"narrative": "x"}).status_code == 403


def test_packet_download_and_pdf(client):
    pytest.importorskip("ophi.packet.build")
    r = client.get("/cases/whitfield/packet")
    assert r.status_code == 200
    assert client.get("/cases/whitfield/packet/preview.pdf").status_code == 200
    # Unsigned: a draft preview exists, but the packet cannot leave the building.
    assert client.get("/cases/whitfield/packet/download").status_code == 409
    client.cookies.set("actor", "dentist")
    narrative = client.get("/cases/whitfield/packet").text
    assert "draft" in narrative and "not for submission" in narrative
    r = client.post("/cases/whitfield/sign-off", data={"narrative": _draft("whitfield")})
    assert r.status_code == 303
    r = client.get("/cases/whitfield/packet/download")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    assert "ophi-packet-whitfield.zip" in r.headers["content-disposition"]


def test_look_back_renders(client):
    r = client.get("/look-back")
    assert r.status_code == 200
    assert "never resubmitted" in r.text


def test_settings_shows_pack_and_audit_csv(client):
    as_dentist(client)
    client.post("/cases/singh/assert", data={"criterion_id": "ferrule_1_5mm", "value": "met"})
    r = client.get("/settings")
    assert r.status_code == 200
    assert client.app.state.svc.pack.version in r.text
    assert "ferrule_1_5mm=met" in r.text
    csv = client.get("/settings/audit.csv")
    assert csv.status_code == 200
    assert csv.headers["content-type"].startswith("text/csv")
    assert "ferrule_1_5mm=met" in csv.text


def test_assessment_json(client):
    r = client.get("/api/cases/singh/assessment.json")
    assert r.status_code == 200
    assert r.json()["verdict"] == "BLOCKED"


def test_actor_cookie_and_reset(client):
    r = client.post("/actor", data={"actor": "dentist"}, headers={"referer": "/cases/singh"})
    assert r.status_code == 303 and r.headers["location"] == "/cases/singh"
    assert "actor=dentist" in r.headers["set-cookie"]
    as_dentist(client)
    client.post("/cases/singh/assert", data={"criterion_id": "ferrule_1_5mm", "value": "met"})
    assert client.post("/reset").status_code == 303
    assert "Not yet recorded" in client.get("/cases/singh").text
    assert client.app.state.svc.store.audit_log() == []


def test_copy_law_in_ophi_voice(client):
    # Look-Back is excluded: it reports Sun Life's recorded decisions ("approved"/"denied"), not Ophi's voice.
    for path in ["/", "/cases/singh", "/cases/deng", "/cases/rosco", "/cases/whitfield/packet", "/settings"]:
        html = client.get(path).text
        hits = [m.group(0) for m in FORBIDDEN.finditer(html)]
        assert not hits, f"{path}: {hits}"


def test_unknown_case_is_404(client):
    assert client.get("/cases/nobody").status_code == 404
