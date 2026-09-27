"""Past-outcome pipeline: export -> Case, denial map, weighted tie-break, and the store views."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import _pg
from tests._cases import ROOT, ready_dict
from ophi.casegen.dsl import build_case
from ophi.engine.assess import assess
from ophi.engine.models import Status, Verdict
from ophi.outcomes import store
from ophi.outcomes.adapter import load_export, to_case, to_submission
from ophi.outcomes.denial_map import load_denial_map
from ophi.outcomes.ingest import ingest_dir
from ophi.outcomes.weights import Weights, compute
from ophi.rules.loader import default_pack

FIXTURES = [ROOT / "fixtures" / "cdcp_approvals", ROOT / "fixtures" / "cdcp_denials"]


def test_export_becomes_case_as_submitted():
    d = load_export(ROOT / "fixtures" / "cdcp_denials" / "PA-SYN-100036.json")
    sub = to_submission(d)
    a = assess(to_case(d, sub), default_pack())
    status = {r.requirement_id: r.status for r in a.requirements}
    assert sub.member_hash != d["member"]["member_id"]
    assert sub.attachment_types == ["clinical_notes"]
    assert status["radiograph_pa"] == Status.UNSATISFIED  # denied for a missing radiograph; none attached
    assert status["radiograph_bw"] == Status.UNSATISFIED


def test_denial_map_names_only_pack_requirements():
    m = load_denial_map(default_pack())
    assert m["DOC_MISSING_RADIOGRAPH"] == ["radiograph_pa", "radiograph_bw"]
    assert m["NOT_COVERED"] == []


def test_lift_breaks_ties_only():
    pack = default_pack()
    d = ready_dict()
    d["radiographs"] = []  # PA and BW both missing: same blocking, severity and effort
    case = build_case(d, "tie")
    base = [a.title for a in assess(case, pack).actions]
    w = Weights(pack_version=pack.version, lift={"radiograph_pa": 0.4}, content_hash="sha256:x")
    weighted = assess(case, pack, w)
    assert base[0].startswith("Take bitewings")  # unweighted tie falls to requirement id
    assert weighted.actions[0].title.startswith("Take a periapical")
    assert weighted.verdict == Verdict.BLOCKED and weighted.ruleset.weights_hash == "sha256:x"


def test_compute_floors_small_samples():
    w = compute("v", [{"requirement_id": "a", "n_missing": 10, "denied_missing": 8, "n_present": 20, "denied_present": 4},
                      {"requirement_id": "b", "n_missing": 3, "denied_missing": 3, "n_present": 27, "denied_present": 9}])
    assert w.lift == {"a": 0.6, "b": 0.0}


@pytest.fixture(scope="module")
def conn():
    name, url = _pg.start()
    try:
        with store.connect(url) as c:
            store.migrate(c)
            yield c
    finally:
        _pg.stop(name)


def test_ingest_fills_lift_and_blind_spots(conn):
    pack = default_pack()
    assert ingest_dir(conn, FIXTURES, pack) == {"submissions": 120, "assessed": 30}
    assert ingest_dir(conn, FIXTURES, pack)["submissions"] == 120  # idempotent re-run
    lift = {r["requirement_id"]: r for r in store.denial_lift(conn, pack.version)}
    assert lift["radiograph_pa"]["n_missing"] + lift["radiograph_pa"]["n_present"] == 30
    kinds = {r["reason_code"]: r["kind"] for r in store.blind_spots(conn)}
    assert kinds["NOT_COVERED"] == "no_requirement"
    assert "DOC_MISSING_RADIOGRAPH" not in kinds  # the engine saw that gap


def test_outcomes_page_without_database(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from ophi.service import CaseService, Store
    from ophi.web.app import create_app

    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    r = TestClient(create_app(svc=CaseService(store=Store(tmp_path / "s")))).get("/outcomes")
    assert r.status_code == 200 and "Past outcomes are unavailable." in r.text and "SUPABASE_DB_URL" not in r.text
