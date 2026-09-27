"""The recorded PMS: the demo's board without the VM."""

from datetime import date

from ophi.service import CaseService
from ophi.sources.pms_repository import RecordedPmsRepository, create_repository


def _repo(**kw) -> RecordedPmsRepository:
    repo = RecordedPmsRepository(**kw)
    repo.vm_path = "/nonexistent/vm"  # a live query would fail loudly
    return repo


def test_recorded_repository_rebuilds_the_clinic_cases_offline():
    cases = _repo(walkthrough=None).get_cases()
    assert len(cases) > 10
    assert all(c.case_id.startswith("abeldent_") for c in cases)
    assert all(c.treatment.code.startswith("27") for c in cases)


def test_the_walkthrough_patient_joins_the_recorded_board_as_of_today():
    case = _repo().get_case("patel")
    assert case.patient.display_name == "Jinay Patel" and case.as_of == date.today()
    assert case.in_chair is not None


def test_an_unrecorded_query_answers_empty_rather_than_reaching_for_the_vm():
    assert _repo().sql("SELECT 1 AS n FROM pat WHERE pid = @pid", {"pid": -1}) == []


def test_the_mock_toggle_selects_the_recording(monkeypatch):
    monkeypatch.setenv("USE_MOCK_PMS_API", "true")
    monkeypatch.delenv("USE_ABELDENT_PMS", raising=False)
    assert isinstance(create_repository("auto"), RecordedPmsRepository)
    assert isinstance(CaseService().repository, RecordedPmsRepository)
