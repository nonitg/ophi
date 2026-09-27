"""Past outcomes list and one past request, read from Supabase."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests import _pg
from tests.test_web import FORBIDDEN, _ophi_voice
from ophi.outcomes import past_store, past_view, store
from ophi.rules.loader import default_pack
from ophi.service import CaseService, Store
from ophi.web.app import create_app


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    name, url = _pg.start()
    try:
        with store.connect(url) as c:
            store.migrate(c)
            past_store.save_all(c, default_pack())
            resent = c.execute("select preauth_id from outcomes.past_request where followup_type = 'resubmission' "
                               "and followup_outcome = 'approved' order by preauth_id limit 1").fetchone()[0]
        app = create_app(svc=CaseService(store=Store(tmp_path_factory.mktemp("s"))))
        app.state.past = past_store.Cached(lambda: store.connect(url))
        client = TestClient(app)
        client.resent_id = resent
        yield client
    finally:
        _pg.stop(name)


def test_outcomes_lists_approved_and_denied_and_filters(client):
    page = client.get("/outcomes").text
    assert "<b class=\"num\">720</b>All" in page and "Approved</span>" in page and "plist-no" in page
    assert not FORBIDDEN.findall(_ophi_voice(page))
    denied = client.get("/outcomes", params={"status": "denied", "tooth": "molar"}).text
    assert "plist-no" in denied and "plist-ok" not in denied and "Molar" in denied


def test_past_request_shows_letter_and_resend(client):
    r = client.get(f"/past/{client.resent_id}")
    assert r.status_code == 200 and "What the clinic sent" in r.text and "Resent" in r.text and "Sun Life approved it." in r.text
    assert not FORBIDDEN.findall(_ophi_voice(r.text))
    assert client.get("/past/PA-NOPE").status_code == 404


def test_a_scoped_clinic_reads_only_its_own_past_requests(client):
    row = past_view.find(client.app.state.past.rows(), client.resent_id)
    other = next(r for r in client.app.state.past.rows() if r["clinic_id"] != row["clinic_id"])
    client.app.state.clinic = row["clinic_id"]
    try:
        assert client.get(f"/past/{client.resent_id}").status_code == 200
        assert client.get(f"/past/{other['preauth_id']}").status_code == 404
        page = client.get("/outcomes").text
        assert row["clinic_id"] in page and other["clinic_id"] not in page
        assert "All clinics" not in page  # one clinic: the filter has nothing to choose between
    finally:
        client.app.state.clinic = None
