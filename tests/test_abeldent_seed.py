"""Lab seeding against the live ABELDent VM, dry-run only (rolled back). Skips when the VM is unreachable."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_path = Path(__file__).resolve().parents[1] / "lab" / "tools" / "abeldent_seed.py"
_spec = importlib.util.spec_from_file_location("abeldent_seed", _path)
seed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seed)


def _vm_up() -> bool:
    try:
        return seed.sql("SELECT 1 AS one") == [{"one": 1}]
    except (RuntimeError, OSError):
        return False


pytestmark = pytest.mark.skipif(not _vm_up(), reason="ABELDent lab VM unreachable (lab/vm/vm status)")


def _any_dentist() -> str:
    return seed.sql("SELECT TOP 1 RTRIM(did) AS did FROM dnt WHERE dinactive = 0 AND RTRIM(did) NOT IN ('', '$', '?')")[0]["did"]


def test_create_patient_dry_run_rolls_back():
    row = seed.create_patient("Zzseedtest", "Dry", "2000-02-02", "M", _any_dentist())
    assert row["lastName"] == "ZZSEEDTEST" and row["id"] > 0
    assert seed.sql("SELECT COUNT(*) AS n FROM pat WHERE plname = 'ZZSEEDTEST'") == [{"n": 0}]


def test_create_appointment_dry_run_rolls_back():
    pid = seed.sql("SELECT TOP 1 pid FROM pat WHERE pnonpatient = 0 ORDER BY pid")[0]["pid"]
    chair = seed.sql("SELECT TOP 1 RTRIM(achair) AS c FROM apt WHERE RTRIM(achair) <> '' ORDER BY achair")[0]["c"]
    # A far-future date keeps the slot free of real bookings
    row = seed.create_appointment(pid, "2099-01-05", "09:00", 30, chair, _any_dentist())
    assert row["patientId"] == pid and row["start"] == "09:00"
    assert seed.sql("SELECT COUNT(*) AS n FROM apt WHERE adate = '2099-01-05'") == [{"n": 0}]
