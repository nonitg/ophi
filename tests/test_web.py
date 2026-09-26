"""Web layer against a fresh Store. Packet-dependent asserts skip when the packet module has not landed."""

from __future__ import annotations

import re
from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient

from ophi.service import CaseService, Store
from ophi.web.app import create_app

RESTORABILITY = ["no_active_perio", "crown_root_ratio", "no_furcation", "margin_3mm", "ferrule_1_5mm",
                 "mesiodistal_space", "no_adjunctive_needed"]
ALL_TREMBLAY = RESTORABILITY + ["extensively_restored", "active_disease_addressed", "endo_healed"]

# Ophi's own voice never predicts payer behaviour. Chart quotes, cited clause titles and rule ids are exempt.
FORBIDDEN = re.compile(r"\b(will be approved|approved|eligib\w*|covered|coverage|likely|probability)\b", re.I)


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


def test_base_path_serves_every_screen_and_link_under_the_prefix(tmp_path):
    """The hosted demo lives at ophi.app/<slug>; nothing it links to may escape that prefix."""
    app = create_app(svc=CaseService(store=Store(tmp_path / "state")), packets_dir=tmp_path / "packets", base_path="/demo-x")
    c = TestClient(app, follow_redirects=False)
    c.cookies.set("actor", "dentist")
    for path in ("/demo-x", "/demo-x/cases/singh", "/demo-x/cases/tremblay/packet", "/demo-x/look-back", "/demo-x/settings"):
        page = c.get(path)
        assert page.status_code == 200, path
        urls = re.findall(r'(?:href|action|src)="(/[^"]*)"', page.text)
        assert urls and all(u.startswith("/demo-x") for u in urls), (path, [u for u in urls if not u.startswith("/demo-x")])
    assert c.get("/demo-x/static/app.css").status_code == 200
    r = c.post("/demo-x/cases/singh/assert", data={"criterion_id": "ferrule_1_5mm", "value": "met"})
    assert r.headers["location"] == "/demo-x/cases/singh#assertions"
    assert c.post("/demo-x/reset").headers["location"] == "/demo-x"


def test_public_demo_does_not_expose_the_live_pms_api(tmp_path):
    """Patient search is lab-only; the proxied demo must not route it under any path."""
    app = create_app(svc=CaseService(store=Store(tmp_path / "state")), packets_dir=tmp_path / "packets", base_path="/demo-x")
    assert not [r.path for r in app.routes if "abeldent" in getattr(r, "path", "")]


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


class _OphiVoice(HTMLParser):
    """Collects the text Ophi says in its own voice: skips chart quotes, clause chips (they cite the CDCP
    source's own headings), rule ids and markup that is never shown."""

    EXEMPT_TAGS = {"q", "blockquote", "mark", "script", "style", "title", "svg"}
    EXEMPT_CLASSES = {"chip", "rid", "note-text"}
    VOID = {"input", "br", "img", "meta", "link", "hr", "source", "wbr"}

    def __init__(self):
        super().__init__()
        self.stack: list[bool] = []
        self.text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        classes = set((dict(attrs).get("class") or "").split())
        self.stack.append(bool(self.stack and self.stack[-1]) or tag in self.EXEMPT_TAGS or bool(classes & self.EXEMPT_CLASSES))

    def handle_endtag(self, tag):
        if tag not in self.VOID and self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if not (self.stack and self.stack[-1]):
            self.text.append(data)


def ophi_voice(html: str) -> str:
    parser = _OphiVoice()
    parser.feed(html)
    return " ".join(parser.text)


def test_copy_law_in_ophi_voice(client):
    # Look-back is excluded: it reports Sun Life's recorded decisions ("approved"/"denied"), not Ophi's voice.
    for actor in ("coordinator", "dentist"):
        client.cookies.set("actor", actor)
        for path in ["/", "/cases/singh", "/cases/deng", "/cases/rosco", "/cases/tremblay", "/cases/kowalchuk",
                     "/cases/whitfield", "/cases/whitfield/packet", "/settings"]:
            hits = [m.group(0) for m in FORBIDDEN.finditer(ophi_voice(client.get(path).text))]
            assert not hits, f"{path} as {actor}: {hits}"


def test_every_strip_cell_links_to_one_row_on_the_page(client):
    for case_id in ["singh", "kowalchuk", "deng", "rosco", "tremblay", "whitfield"]:
        html = client.get(f"/cases/{case_id}").text
        targets = re.findall(r'href="#(req-[a-z_]+)"', html)
        ids = re.findall(r'id="(req-[a-z_]+)"', html)
        assert targets and len(ids) == len(set(ids)), case_id
        assert set(targets) <= set(ids), f"{case_id}: {set(targets) - set(ids)}"


def test_unknown_case_is_404(client):
    assert client.get("/cases/nobody").status_code == 404
