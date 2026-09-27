"""The deployed demo's past denials: saved ABELDent rows, read by the same code a live clinic uses."""
from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

from ophi.service import CaseService, Store
from ophi.sources.fixture_lookback import fixture_lookback
from ophi.web.app import create_app


def test_the_saved_pms_rows_carry_the_demo_history():
    rep = fixture_lookback()
    assert (rep.submitted, rep.denied, rep.undecided) == (34, 20, 0)
    assert (rep.never_resubmitted, rep.never_resubmitted_dollars) == (10, 11455.0)
    # Sun Life's wording is carried over, but the gap is the engine's own finding from the chart.
    row = next(r for r in rep.rows if r.decision == "denied" and r.gaps)
    assert row.patient_name and row.gaps


def test_a_tooth_sent_twice_is_one_request_not_two():
    """The fixtures hold both attempts, as ABELDent would; the page reports the chain once."""
    resent = [r for r in fixture_lookback().rows if r.resubmitted]
    assert len(resent) == 10 and all(r.resubmitted_decision in ("approved", "denied") for r in resent)


def test_recover_reads_the_pms_rows_without_a_service_of_its_own(tmp_path):
    svc = CaseService(store=Store(tmp_path / "state"), clock=lambda: datetime(2026, 9, 27, 12))
    client = TestClient(create_app(auto_rules_check=False, svc=svc, packets_dir=tmp_path / "packets", live_ml=False))
    page = client.get("/recover").text
    assert "10 past denials were never resubmitted" in page and "$11,455" in page
