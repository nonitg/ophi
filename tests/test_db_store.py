"""The app on Supabase: patient charts and workflow state live in the `app` schema, not on disk."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from tests import _pg
from ophi import db_store
from ophi.outcomes import store
from ophi.service import CASES_DIR, CaseService, FollowUp
from ophi.web.app import create_app


@pytest.fixture(scope="module")
def url():
    name, url = _pg.start()
    try:
        with store.connect(url) as c:
            store.migrate(c)
            db_store.seed_cases(c, CASES_DIR)
        yield url
    finally:
        _pg.stop(name)


def test_workflow_state_round_trips_through_supabase(url, tmp_path):
    connect = lambda: store.connect(url)
    repo, st = db_store.SupabaseCaseRepository(connect), db_store.SupabaseStore(connect, tmp_path)
    svc = CaseService(store=st, repository=repo)
    assert "kowalchuk" in svc.case_ids() and svc.base_case("kowalchuk").case_id == "kowalchuk"

    svc.skip_gaps("kowalchuk", "Kim Osei")
    st.add_followup("r1", FollowUp(status="left_message", by="Kim Osei", at=datetime(2026, 9, 17, tzinfo=UTC)))
    fresh = db_store.SupabaseStore(connect, tmp_path)  # a new process sees the same state
    assert fresh.load("kowalchuk").test_skips and fresh.load("kowalchuk") == st.load("kowalchuk")
    assert [e.case_id for e in fresh.audit_log("kowalchuk")] and "r1" in fresh.load_followups()

    fresh.reset()
    assert fresh.audit_log() == [] and fresh.load_followups() == {} and repo.list_case_ids()  # charts stay


def test_app_serves_board_from_supabase(url, tmp_path, monkeypatch):
    monkeypatch.setenv("SUPABASE_DB_URL", url)
    monkeypatch.setenv("OPHI_VAR_DIR", str(tmp_path))
    svc = db_store.service_from_env()
    assert isinstance(svc.store, db_store.SupabaseStore)
    r = TestClient(create_app(svc=svc, seed_demo=True, live_ml=False)).get("/")
    assert r.status_code == 200 and "Kowalchuk" in r.text
