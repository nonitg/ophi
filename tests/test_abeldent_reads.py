"""The scheduling reads ophi-phone answers calls with, against the live lab VM (Fictional Data). Skips when the VM is
unreachable. Expectations derive from the database itself, so any Fictional Data install passes."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from abeldent import reads
from ophi.sources.pms_repository import AbelDentPmsRepository

REPO = AbelDentPmsRepository()


def _vm_up() -> bool:
    try:
        return REPO.sql("SELECT 1 AS one") == [{"one": 1}]
    except (RuntimeError, OSError):
        return False


pytestmark = pytest.mark.skipif(not _vm_up(), reason="ABELDent lab VM unreachable (lab/vm/vm status)")


@pytest.fixture(scope="module")
def booking():
    """The latest patient booking in the VM."""
    [row] = REPO.sql("SELECT TOP 1 CAST(aidentifier AS varchar(36)) AS id, apid AS pid, CONVERT(varchar(10), adate, 23) AS d "
                     "FROM apt WHERE apid > 0 ORDER BY adate DESC, atime DESC", None)
    return row


def test_patients_born_on_finds_the_patient():
    [row] = REPO.sql("SELECT TOP 1 pid, CONVERT(varchar(10), pbirth, 23) AS dob FROM pat "
                     "WHERE pnonpatient = 0 AND pbirth IS NOT NULL ORDER BY pid", None)
    found = reads.patients_born_on(REPO.sql, date.fromisoformat(row["dob"]))
    assert row["pid"] in [p.id for p in found]
    assert all(p.birth_date == date.fromisoformat(row["dob"]) for p in found)


def test_scheduler_unit_is_the_grid():
    assert reads.scheduler_unit_minutes(REPO.sql) > 1


def test_get_appointment_round_trips(booking):
    appt = reads.get_appointment(REPO.sql, booking["id"])
    assert appt is not None and appt.id.lower() == booking["id"].lower() and appt.patient_id == booking["pid"]


def test_patient_appointments_from_a_day(booking):
    day = date.fromisoformat(booking["d"])
    found = reads.patient_appointments(REPO.sql, booking["pid"], day)
    assert booking["id"].lower() in [a.id.lower() for a in found]
    assert all(a.date >= day for a in found)


def test_chair_time_holds_the_booking(booking):
    day = date.fromisoformat(booking["d"])
    spans = reads.list_chair_time(REPO.sql, day - timedelta(days=1), day + timedelta(days=1))
    assert booking["id"].lower() in [(s.id or "").lower() for s in spans]
    assert all(s.duration_minutes > 0 and len(s.start) == 5 for s in spans)
