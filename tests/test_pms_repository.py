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


def test_abeldent_list_case_ids_not_implemented():
    repo = AbelDentPmsRepository()
    with pytest.raises(NotImplementedError):
        repo.list_case_ids()


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
