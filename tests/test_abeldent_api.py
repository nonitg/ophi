"""Read-only ABELDent API against the live lab VM (Fictional Data). Skips when the VM is unreachable.

Expectations derive from the database itself rather than fixed ids, so any Fictional Data install passes.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ophi.service import CaseService, Store
from ophi.sources.pms_repository import AbelDentPmsRepository
from ophi.web.app import create_app

REPO = AbelDentPmsRepository()


def _vm_up() -> bool:
    try:
        return REPO.sql("SELECT 1 AS one") == [{"one": 1}]
    except (RuntimeError, OSError):
        return False


pytestmark = pytest.mark.skipif(not _vm_up(), reason="ABELDent lab VM unreachable (lab/vm/vm status)")


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("abeldent")
    return TestClient(create_app(auto_rules_check=False, svc=CaseService(store=Store(tmp / "state")), packets_dir=tmp / "packets"))


def test_providers(client):
    body = client.get("/api/abeldent/providers").json()
    assert body and all(p["id"] and p["name"] for p in body)


def test_patient_search_and_get(client):
    [row] = REPO.sql("SELECT TOP 1 pid, RTRIM(plname) AS plname FROM pat WHERE pnonpatient = 0 ORDER BY pid", None)
    found = client.get("/api/abeldent/patients", params={"q": row["plname"].lower()}).json()
    assert row["pid"] in [p["id"] for p in found]
    patient = client.get(f"/api/abeldent/patients/{row['pid']}").json()
    assert patient["id"] == row["pid"] and patient["last_name"] == row["plname"]


def test_patient_not_found(client):
    assert client.get("/api/abeldent/patients/-1").status_code == 404


def test_appointments_for_a_booked_day(client):
    [row] = REPO.sql("SELECT TOP 1 CONVERT(varchar(10), adate, 23) AS d, COUNT(*) AS n FROM apt WHERE apid > 0 "
                     "GROUP BY adate ORDER BY adate DESC", None)
    body = client.get("/api/abeldent/appointments", params={"date": row["d"]}).json()
    assert len(body) == row["n"]
    assert all(a["date"] == row["d"] and a["duration_minutes"] > 0 and len(a["start"]) == 5 for a in body)


def test_vm_errors_surface_as_502_with_the_database_message(client, monkeypatch):
    monkeypatch.setattr("ophi.sources.abeldent.LIST_PROVIDERS", "SELECT nope FROM dnt")
    res = client.get("/api/abeldent/providers")
    assert res.status_code == 502 and res.json()["detail"] == "Invalid column name 'nope'."


def test_predeterminations_carry_abeldents_status_label(client):
    [row] = REPO.sql("SELECT COUNT(*) AS n FROM Claim WHERE IsPredetermination = 1 AND ClaimID > 0", None)
    pids = [r["pid"] for r in REPO.sql("SELECT DISTINCT PatientID AS pid FROM Claim WHERE IsPredetermination = 1 AND ClaimID > 0", None)]
    found = [p for pid in pids for p in client.get(f"/api/abeldent/patients/{pid}/predeterminations").json()]
    assert len(found) == row["n"] and all(p["status_label"] and p["sent_on"] for p in found)
