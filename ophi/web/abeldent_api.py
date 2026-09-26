"""Read-only JSON over the live ABELDent VM. Never writes: Ophi does not write back to the PMS."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException

from ophi.sources import abeldent
from ophi.sources.pms_repository import AbelDentPmsRepository

router = APIRouter(prefix="/api/abeldent")
_repo = AbelDentPmsRepository()


def _pms(query, *args):
    try:
        return query(_repo.sql, *args)
    except RuntimeError as e:  # chart_dump.VmSqlError: VM unreachable or query rejected
        raise HTTPException(502, str(e)) from e


@router.get("/providers", response_model=list[abeldent.Provider])
def providers():
    return _pms(abeldent.list_providers)


@router.get("/patients", response_model=list[abeldent.Patient])
def patients(q: str = ""):
    return _pms(abeldent.search_patients, q)


@router.get("/patients/{pid}", response_model=abeldent.Patient)
def patient(pid: int):
    found = _pms(abeldent.get_patient, pid)
    if found is None:
        raise HTTPException(404, "patient not found")
    return found


@router.get("/appointments", response_model=list[abeldent.Appointment])
def appointments(date: date):
    return _pms(abeldent.list_appointments, date)
