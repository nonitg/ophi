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

# Ophi's own voice never predicts payer behaviour. Chart quotes and Sun Life text are exempt.
FORBIDDEN = re.compile(r"\b(will be approved|approved|eligible|covered|likely|probability)\b", re.I)


@pytest.fixture
def client(tmp_path):
    svc = CaseService(store=Store(tmp_path / "state"))
    app = create_app(svc=svc, packets_dir=tmp_path / "packets")
    return TestClient(app, follow_redirects=False)


@pytest.fixture
def seeded(tmp_path):
    """The demo as it runs: five cases already past sign-off, some with Sun Life's decision recorded."""
    svc = CaseService(store=Store(tmp_path / "state"))
    app = create_app(svc=svc, packets_dir=tmp_path / "packets", seed_demo=True)
    with TestClient(app, follow_redirects=False) as c:  # the first request seeds
        yield c


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


def test_board_shows_a_column_per_step_with_deadline_chips(seeded):
    r = seeded.get("/")
    assert r.status_code == 200
    for text in ("Fix chart", "With Sun Life", "Decision back", "Start here", "Kowalchuk", "Late for Sep 20 crown", "Send by Sep 22"):
        assert text in r.text


def test_base_path_serves_every_screen_and_link_under_the_prefix(tmp_path):
    """The hosted demo lives at ophi.app/<slug>; nothing it links to may escape that prefix."""
    app = create_app(svc=CaseService(store=Store(tmp_path / "state")), packets_dir=tmp_path / "packets", base_path="/demo-x",
                     seed_demo=True)
    c = TestClient(app, follow_redirects=False)
    for actor in ("coordinator", "dentist"):
        c.cookies.set("actor", actor)
        for path in ("/demo-x", "/demo-x/cases/singh", "/demo-x/cases/fontaine", "/demo-x/cases/marchand",
                     "/demo-x/cases/tremblay/packet", "/demo-x/recover", "/demo-x/results", "/demo-x/settings"):
            page = c.get(path)
            assert page.status_code == 200, path
            urls = re.findall(r'(?:href|action|src)="(/[^"]*)"', page.text)
            assert urls and all(u.startswith("/demo-x") for u in urls), (path, [u for u in urls if not u.startswith("/demo-x")])
    assert c.get("/demo-x/static/app.css").status_code == 200
    assert c.get("/demo-x/look-back").headers["location"] == "/demo-x/results#before"
    r = c.post("/demo-x/cases/tremblay/assert", data={"criterion_id": "ferrule_1_5mm", "value": "met"})
    assert r.headers["location"] == "/demo-x/cases/tremblay?done=criteria"
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
    r = client.post("/cases/tremblay/assert", data={"criterion_id": "ferrule_1_5mm", "value": "met", "note": "on the PA"})
    assert r.status_code == 303
    page = client.get("/cases/tremblay").text
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
    assert "Review and sign" in client.get("/cases/tremblay").text

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

    assert client.post("/cases/tremblay/submitted", data={"on": "2026-09-17"}).status_code == 303
    assert "Marked as sent on Sep 17, 2026" in client.get("/cases/tremblay/packet").text
    client.cookies.set("actor", "coordinator")
    assert "Waiting for the decision" in client.get("/").text


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


def test_results_report_and_the_old_look_back_link(seeded):
    assert seeded.get("/look-back").headers["location"] == "/results#before"
    r = seeded.get("/results")
    assert r.status_code == 200
    assert "missing or out-of-date documents" in r.text and "never resubmitted" in r.text


def test_record_decision_then_book(seeded):
    r = seeded.post("/cases/park/decision", data={"outcome": "approved", "decided_on": "2026-09-16", "reason": ""})
    assert r.status_code == 303 and "done=decision" in r.headers["location"]
    assert "Book by Sep 16, 2027" in seeded.get("/cases/park").text
    assert seeded.post("/cases/park/booked", data={"on": "2026-10-05"}).status_code == 303
    assert "Crown booked for" in seeded.get("/cases/park").text


def test_decision_needs_an_outcome_and_a_date(seeded):
    assert seeded.post("/cases/park/decision", data={"outcome": "", "decided_on": ""}).status_code == 400


def test_undo_the_latest_step(seeded):
    assert seeded.post("/cases/nguyen/undo", data={"step": "decision"}).status_code == 303
    assert "Record decision" in seeded.get("/cases/nguyen").text
    assert seeded.post("/cases/nguyen/undo", data={"step": "booked"}).status_code == 409


def test_resubmit_keeps_the_denied_attempt(seeded):
    assert seeded.post("/cases/marchand/resubmit").status_code == 303
    page = seeded.get("/cases/marchand").text
    assert "Attempt 1" in page and "Denied as per the plan criteria." in page


def test_recover_call_list_records_a_follow_up(seeded):
    page = seeded.get("/recover").text
    assert "never resubmitted" in page
    row = seeded.app.state.svc.recover_rows()[0]["row"].case_id
    assert seeded.post(f"/recover/{row}", data={"status": "left_message", "note": ""}).status_code == 303
    assert "Left a message" in seeded.get("/recover").text


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
    client.post("/cases/tremblay/assert", data={"criterion_id": "ferrule_1_5mm", "value": "met"})
    assert client.post("/reset").status_code == 303
    assert 'value="met" checked' not in client.get("/cases/tremblay").text
    assert client.app.state.svc.store.audit_log() == []


class _OphiVoice(HTMLParser):
    """Text of a page, and its readable attributes, minus anything inside an element marked data-voice="payer"
    (Sun Life's recorded decisions and words). Void elements never close, so they never change the depth."""

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__()
        self.depth, self.parts = 0, []

    def handle_starttag(self, tag, attrs):
        if not self.depth:
            self.parts += [v for k, v in attrs if k in ("aria-label", "placeholder", "title") and v]
        if tag in self.VOID:
            return
        if self.depth or ("data-voice", "payer") in attrs:
            self.depth += 1

    def handle_endtag(self, tag):
        if self.depth and tag not in self.VOID:
            self.depth -= 1

    def handle_data(self, data):
        if not self.depth:
            self.parts.append(data)


def _ophi_voice(html: str) -> str:
    p = _OphiVoice()
    p.feed(html)
    return " ".join(p.parts)


def test_copy_law_parser_sees_past_void_tags_inside_payer_text():
    html = '<fieldset data-voice="payer"><label><input type="radio">Approved</label></fieldset><p>This will be approved.</p>'
    assert FORBIDDEN.findall(_ophi_voice(html)) == ["will be approved"]


def test_copy_law_in_ophi_voice(seeded):
    as_dentist(seeded)
    seeded.post("/cases/park/decision", data={"outcome": "approved", "decided_on": "2026-09-16", "reason": ""})
    pages = ["/", "/cases/singh", "/cases/deng", "/cases/rosco", "/cases/tremblay", "/cases/nguyen", "/cases/marchand", "/cases/park", "/cases/okafor",
             "/cases/whitfield/packet", "/recover", "/results", "/settings"]
    for actor in ("dentist", "coordinator"):
        seeded.cookies.set("actor", actor)
        for path in pages:
            text = _ophi_voice(seeded.get(path).text)
            hits = [m.group(0) for m in FORBIDDEN.finditer(text)]
            assert not hits, f"{actor} {path}: {hits}"


def test_fix_chart_step_shows_denial_risk_and_applies_ophis_fixes(seeded):
    assert "Risk <b class=\"lvl lvl-high\">High</b>" in seeded.get("/").text
    page = seeded.get("/cases/deng").text
    assert "Denial risk" in page and "Replace lab code 99333 with 99113" in page and "Apply it" in page
    assert "Lowers denial risk the most" in page and "For Dr. Priya Lau" in page  # the plan's ranking and its clinical/timing calls
    r = seeded.post("/cases/deng/fixes", data={"all": "1"})
    assert r.status_code == 303 and r.headers["location"].endswith("/cases/deng?done=fixed#now")
    page = seeded.get("/cases/deng").text
    assert "Apply it" not in page and "applied by Kim Osei" in page and "Denial risk" in page


def test_unknown_case_is_404(client):
    assert client.get("/cases/nobody").status_code == 404
