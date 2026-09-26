"""Read-only views of a live ABELDent's providers, patients and schedule.

Queries run through `AbelDentPmsRepository.sql`, so the lab read-only rails apply and every value
binds as an `@param`. Table semantics: docs/research/abeldent-schema.md ("Scheduling and patient tables").
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from pydantic import BaseModel

Sql = Callable[[str, dict | None], list[dict]]


class Provider(BaseModel):
    id: str
    name: str


class Patient(BaseModel):
    id: int
    last_name: str
    first_name: str
    birth_date: date | None
    gender: str
    phone: str | None
    mobile: str | None
    email: str | None
    dentist_id: str
    inactive: bool


class Appointment(BaseModel):
    id: str
    patient_id: int
    patient_name: str | None
    date: date
    start: str
    duration_minutes: int
    chair: str
    provider_id: str
    status_code: str
    status: str | None
    work: str


# '', '$' and '?' are ABELDent's placeholder provider rows, not people.
LIST_PROVIDERS = """
SELECT RTRIM(did) AS id, RTRIM(dname) AS name FROM dnt
WHERE dinactive = 0 AND RTRIM(did) NOT IN ('', '$', '?') ORDER BY did"""

_PATIENT_COLUMNS = """
  p.pid AS id, RTRIM(p.plname) AS last_name, RTRIM(p.pfname) AS first_name,
  CONVERT(varchar(10), p.pbirth, 23) AS birth_date, RTRIM(p.pgender) AS gender,
  NULLIF(RTRIM(p.pphone), '') AS phone, NULLIF(RTRIM(i.infmobile), '') AS mobile,
  NULLIF(RTRIM(i.infemail), '') AS email, RTRIM(p.pdentist) AS dentist_id, p.pinactive AS inactive"""

# Names are stored upper-case; LIKE is case-insensitive under ABELDent's collation.
SEARCH_PATIENTS = f"""
SELECT TOP 50 {_PATIENT_COLUMNS}
FROM pat p LEFT JOIN inf i ON i.infpid = p.pid
WHERE p.pnonpatient = 0
  AND (@q = '' OR p.plname LIKE @q + '%' OR p.pfname LIKE @q + '%' OR p.pphone LIKE '%' + @q + '%')
ORDER BY p.plname, p.pfname"""

GET_PATIENT = f"""
SELECT {_PATIENT_COLUMNS} FROM pat p LEFT JOIN inf i ON i.infpid = p.pid WHERE p.pid = @pid"""

# atime is a time of day on the 1899-12-30 zero date; atimereq counts scheduler units (sys.sunitmins).
# apid <= 0 rows are blocks (lunch, holds), not patient bookings.
LIST_APPOINTMENTS = """
SELECT CAST(a.aidentifier AS varchar(36)) AS id, a.apid AS patient_id,
  RTRIM(p.pfname) + ' ' + RTRIM(p.plname) AS patient_name,
  CONVERT(varchar(10), a.adate, 23) AS date, CONVERT(char(5), a.atime, 108) AS start,
  a.atimereq * u.mins AS duration_minutes, RTRIM(a.achair) AS chair, RTRIM(a.adid) AS provider_id,
  a.astatus AS status_code, RTRIM(s.apsdesc) AS status, RTRIM(a.apwork) AS work
FROM apt a
CROSS JOIN (SELECT TOP 1 sunitmins AS mins FROM sys WHERE sunitmins > 1) u
LEFT JOIN pat p ON p.pid = a.apid
LEFT JOIN aps s ON s.apsid = a.astatus
WHERE a.adate = @date AND a.apid > 0
ORDER BY a.atime, a.achair"""


def list_providers(sql: Sql) -> list[Provider]:
    return [Provider(**r) for r in sql(LIST_PROVIDERS, None)]


def search_patients(sql: Sql, q: str = "") -> list[Patient]:
    return [Patient(**r) for r in sql(SEARCH_PATIENTS, {"q": q})]


def get_patient(sql: Sql, pid: int) -> Patient | None:
    rows = sql(GET_PATIENT, {"pid": pid})
    return Patient(**rows[0]) if rows else None


def list_appointments(sql: Sql, day: date) -> list[Appointment]:
    return [Appointment(**r) for r in sql(LIST_APPOINTMENTS, {"date": day.isoformat()})]
