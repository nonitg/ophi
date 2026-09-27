"""The weekly source check that runs on a page visit, and the /rules review page that replaces `ophi pack approve`.
Everything runs against the fixture web and scratch packs; nothing touches the network, packs/ or var/."""

from __future__ import annotations

import json
import re
import threading
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ophi.rules import auto, watch
from ophi.rules.loader import load_pack
from ophi.service import CaseService, Store
from ophi.web.app import create_app
from tests._pack_watch import (  # noqa: F401
    BASE,
    PAGE,
    TODAY,
    WATCH,
    cases,
    cdcp,
    draft_fixture,
    fetcher,
    served,
    status,
)
from tests.test_web import FORBIDDEN

NOW = datetime(2026, 9, 26, 15, 0, tzinfo=UTC)


def _env(cdcp: Path, cases: Path, status: Path, get=None) -> auto.PackEnv:
    return auto.PackEnv(fetcher=get or fetcher(served(cdcp / BASE)), cdcp_dir=cdcp, cases_dir=cases, config=WATCH,
                        status=status, today=TODAY)


def _stale(status: Path, days: int = 8, **extra) -> None:
    watch.write_json(status, {"checked_on": "2026-09-18", "attempted_at": (NOW - timedelta(days=days)).isoformat(), **extra})


def test_a_stale_status_starts_exactly_one_background_run_which_drafts_but_never_approves(cdcp, cases, status):
    web, gate, pages = served(cdcp / BASE), threading.Event(), []

    def slow(url: str) -> bytes:
        if url == PAGE:
            pages.append(url)
            gate.wait(10)  # hold the first run open while the second visit arrives
        return fetcher(web)(url)

    _stale(status)
    env = _env(cdcp, cases, status, slow)
    first = auto.maybe_start(env, NOW)
    assert first is not None
    assert auto.maybe_start(env, NOW) is None  # single flight
    gate.set()
    first.join(20)
    assert pages == [PAGE]
    s = watch.load_status(status)
    assert s["attempted_at"] == NOW.isoformat() and s["checking_since"] is None and s["pending"]
    assert auto.current_draft(cdcp) is not None and not (cdcp / "2026-09-26").exists()


def test_a_fresh_status_starts_nothing(cdcp, cases, status):
    _stale(status, days=6)
    assert auto.maybe_start(_env(cdcp, cases, status), NOW) is None


def test_a_running_marker_blocks_until_it_goes_stale(cdcp, cases, status):
    _stale(status, checking_since=(NOW - timedelta(minutes=5)).isoformat())
    assert not auto.due(watch.load_status(status), NOW)
    assert auto.due(watch.load_status(status), NOW + timedelta(minutes=40))


def test_a_failed_attempt_backs_off_a_day(cdcp, cases, status):
    _stale(status)
    assert auto.run(_env(cdcp, cases, status, fetcher({})), NOW) == "failed"
    s = watch.load_status(status)
    assert s["last_error"] and s["checked_on"] == "2026-09-18"  # the last good check still stands
    assert not auto.due(s, NOW + timedelta(hours=23))
    assert auto.due(s, NOW + timedelta(hours=25))


# --- /rules ----------------------------------------------------------------------------------------


def _app(tmp_path, env, **kw):
    return create_app(svc=CaseService(store=Store(tmp_path / "state")), packets_dir=tmp_path / "packets", rules_env=env,
                      seed_demo=True, **kw)


@pytest.fixture
def rules_client(tmp_path, cdcp, cases, status):
    with TestClient(_app(tmp_path, _env(cdcp, cases, status)), follow_redirects=False) as c:
        c.cookies.set("actor", "dentist")
        yield c


def _use(client, d: Path, **extra):
    sha = re.search(r'name="draft_sha" value="(\w+)"', client.get("/rules").text).group(1)
    return client.post("/rules/use", data={"draft": d.name, "draft_sha": sha, **extra})


def test_the_review_page_shows_the_clinics_requests_and_puts_a_draft_in_force(rules_client, cdcp, cases, status):
    d = draft_fixture(cdcp, cases).dir
    page = rules_client.get("/rules").text
    assert "Use this rule update" in page and "99112 is replaced by 99122" in page and not FORBIDDEN.search(page)
    assert "Your requests" in page and "Test cases" not in page and ".yaml" not in page and "lab_codes_current" not in page
    assert "None of your open requests change." in page  # every demo request is dated before Apr 1, 2027
    r = _use(rules_client, d)
    assert r.status_code == 303 and r.headers["location"] == "/rules?done=rules_used"
    assert load_pack(cdcp / "2026-09-26" / "pack.yaml").reviewed_by == "Dr. Priya Lau"
    assert "No rule update is waiting." in rules_client.get("/rules").text


def test_only_the_named_dentist_uses_an_update_and_only_the_one_they_reviewed(rules_client, cdcp, cases):
    d = draft_fixture(cdcp, cases).dir
    sha = re.search(r'name="draft_sha" value="(\w+)"', rules_client.get("/rules").text).group(1)
    rules_client.cookies.set("actor", "coordinator")
    assert "puts rule updates into use" in rules_client.get("/rules").text
    assert rules_client.post("/rules/use", data={"draft": d.name, "draft_sha": sha}).status_code == 403
    rules_client.cookies.clear()
    assert rules_client.post("/rules/use", data={"draft": d.name, "draft_sha": sha}).status_code == 403
    rules_client.cookies.set("actor", "dentist")
    r = rules_client.post("/rules/use", data={"draft": d.name, "draft_sha": "0" * 64})  # re-drafted since
    assert r.status_code == 409 and "changed since you opened it" in r.text and not (cdcp / "2026-09-26").exists()


def test_every_needs_a_person_item_must_be_ticked(rules_client, cdcp, cases):
    d = draft_fixture(cdcp, cases).dir
    meta = json.loads((d / "draft.json").read_text())
    (d / "draft.json").write_text(json.dumps({**meta, "needs_person": ["Check the grid by hand."]}))
    page = rules_client.get("/rules").text
    assert 'name="ack-0" required' in page and "disabled>Use this rule update" in page
    r = _use(rules_client, d)
    assert r.status_code == 400 and "Tick each item" in r.text and not (cdcp / "2026-09-26").exists()
    assert _use(rules_client, d, **{"ack-0": "on"}).status_code == 303
    assert "acknowledged 1 open items: Check the grid by hand." in (cdcp / "CHANGELOG.md").read_text()


def test_check_now_runs_in_the_background_and_the_board_links_the_review(rules_client, status):
    r = rules_client.post("/rules/check")
    assert r.headers["location"] == "/rules?done=rules_checking"
    for t in threading.enumerate():
        if t.name == "rules-check":
            t.join(20)
    assert watch.load_status(status)["checked_on"] == TODAY.isoformat()
    assert 'href="/rules"' in rules_client.get("/").text


def test_the_page_says_when_a_check_is_running(rules_client, status):
    watch.write_json(status, {"checked_on": "2026-09-18", "checking_since": datetime.now(UTC).isoformat()})
    assert "Checking CDCP sources…" in rules_client.get("/rules").text


def test_the_proxied_demo_reads_rule_updates_but_never_changes_them(tmp_path, cdcp, cases, status):
    app = _app(tmp_path, _env(cdcp, cases, status), base_path="/demo-x")
    assert app.state.auto_rules is False  # the public demo never checks on its own
    with TestClient(app, follow_redirects=False) as c:
        c.cookies.set("actor", "dentist")
        assert c.get("/demo-x/rules").status_code == 200
        assert c.post("/demo-x/rules/check").status_code == 403 and c.post("/demo-x/rules/use").status_code == 403


def test_auto_check_is_off_for_a_callers_own_service(tmp_path, cdcp, cases, status):
    assert _app(tmp_path, _env(cdcp, cases, status)).state.auto_rules is False


def test_requests_dated_from_the_update_show_what_they_would_need(rules_client, cdcp, cases):
    from ophi.web import present

    svc = rules_client.app.state.svc
    proposed = load_pack(draft_fixture(cdcp, cases).dir / "pack.yaml").model_copy(update={"effective_from": date(2026, 9, 1)})
    rows = present.request_changes(svc.queue(), proposed, svc.assess_under)
    assert rows and all(set(r) == {"case_id", "patient", "tooth", "change"} for r in rows)
    assert any("would need: Replace lab code 99113 with 99123 (from Sep 1, 2026)" in r["change"] for r in rows)
    assert not any("lab_codes" in r["change"] or ".yaml" in r["change"] for r in rows)
