from pathlib import Path
import pytest
from ophi.sources.pms_repository import (
    FileSystemPmsRepository,
    AbelDentPmsRepository,
    create_repository,
)
from ophi.sources import PmsRepository

ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT / "cases" / "demo"


def test_list_case_ids():
    repo = FileSystemPmsRepository(CASES_DIR)
    ids = repo.list_case_ids()
    assert "singh" in ids
    assert ids == sorted(ids)


def test_get_case():
    repo = FileSystemPmsRepository(CASES_DIR)
    case = repo.get_case("singh")
    assert case.case_id == "singh"
    assert case.patient.display_name == "Amrit Singh"


def test_get_cases_all():
    repo = FileSystemPmsRepository(CASES_DIR)
    cases = repo.get_cases()
    assert len(cases) >= 6
    assert all(c.case_id for c in cases)


def test_get_cases_filtered():
    repo = FileSystemPmsRepository(CASES_DIR)
    cases = repo.get_cases(["singh", "deng"])
    assert {c.case_id for c in cases} == {"singh", "deng"}


def test_get_case_missing_raises():
    repo = FileSystemPmsRepository(CASES_DIR)
    with pytest.raises(FileNotFoundError):
        repo.get_case("nonexistent_xyz")


def test_create_repository_filesystem():
    repo = create_repository("filesystem", cases_dir=CASES_DIR)
    assert isinstance(repo, FileSystemPmsRepository)
    assert isinstance(repo, PmsRepository)


def test_create_repository_abeldent():
    repo = create_repository("abeldent")
    assert isinstance(repo, AbelDentPmsRepository)


def test_create_repository_unknown():
    with pytest.raises(ValueError):
        create_repository("unknown")


def test_filesystem_fetch_raw_not_implemented():
    repo = FileSystemPmsRepository(CASES_DIR)
    with pytest.raises(NotImplementedError):
        repo.fetch_raw([1])


def fake_vm_sql(query, params=None):
    """The VM queries a case pull makes besides the charts: last chart write, crown appointments, dentist names."""
    if "dm_db_index_usage_stats" in query:
        return [{"u": None}]
    if "FROM apt" in query:
        return [{"pid": 158, "day": "2026-10-06"}]
    return [{"id": "T", "name": "Dr. Terry Ackerman"}]


def test_abeldent_cases_are_the_planned_crowns_from_its_charts(monkeypatch):
    """A saved Fictional Data chart stands in for the VM: pid 158 plans a filling first, then a crown on #24."""
    import json
    from pathlib import Path
    chart = json.loads((Path(__file__).parents[1] / "fixtures/abeldent/fictional/158.json").read_text())
    repo = AbelDentPmsRepository()
    monkeypatch.setattr(repo, "planned_patient_ids", lambda: [158])
    monkeypatch.setattr(repo, "fetch_patient_charts", lambda pids: {158: chart})
    monkeypatch.setattr(repo, "sql", fake_vm_sql)
    assert repo.list_case_ids() == ["abeldent_158"]
    case = repo.get_case("abeldent_158")
    assert (case.patient.patient_id, case.treatment.code, case.requested_tooth) == ("158", "27211", 24)
    assert case.treatment.appointment_date.isoformat() == "2026-10-06"  # the booked crown visit


def test_service_uses_repository():
    try:
        from ophi.service import CaseService
    except ModuleNotFoundError as e:
        pytest.skip(f"service deps missing: {e}")
    repo = FileSystemPmsRepository(CASES_DIR)
    svc = CaseService(cases_dir=CASES_DIR, repository=repo)
    assert svc.case_ids() == repo.list_case_ids()
    assert svc.base_case("singh").case_id == "singh"


def test_load_raw_dict_and_build():
    repo = FileSystemPmsRepository(CASES_DIR)
    d = repo.load_raw_dict("singh")
    assert d["patient"]["name"] == "Amrit Singh"
    case = repo.build_case_from_dict(d, "singh")
    assert case.case_id == "singh"


def test_abeldent_repulls_only_when_charts_change(monkeypatch):
    repo = AbelDentPmsRepository()
    stamps, pulls = ["t1"], []
    monkeypatch.setattr(repo, "sql", lambda q, p=None: [{"u": stamps[0]}])
    monkeypatch.setattr(repo, "_pull", lambda: pulls.append(1) or {})
    monkeypatch.setattr(repo, "CHECK_SECONDS", -1)  # check on every ask

    repo.list_case_ids(); repo.list_case_ids()
    assert len(pulls) == 1  # unchanged: the cached pull serves
    stamps[0] = "t2"  # staff edited a chart in ABELDent
    repo.list_case_ids()
    assert len(pulls) == 2
