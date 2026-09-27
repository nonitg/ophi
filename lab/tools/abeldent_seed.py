#!/usr/bin/env python3
"""Seed test patients and appointments into the ABELDent lab VM (Fictional Data only).

    abeldent_seed.py patient Zztest Second 1990-05-15 F T           # dry run: inserts, rolls back
    abeldent_seed.py patient Zztest Second 1990-05-15 F T --commit
    abeldent_seed.py appointment 169 2026-09-28 10:40 30 2 T [--work "..."] [--commit]

Lab tooling, not product: Ophi itself never writes to a PMS. Ported from AF-Hacks
(client/lib/abeldent/sql.ts); table semantics in docs/research/abeldent-schema.md.
Validation failures THROW 'VALIDATION: ...' and surface as VmSqlError.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chart_dump import VmSqlError, sql  # noqa: E402

_PATIENT_COLUMNS = """
  p.pid AS id, p.plname AS lastName, p.pfname AS firstName, p.pbirth AS birthDate, p.pgender AS gender,
  NULLIF(RTRIM(p.pphone), '') AS phone, NULLIF(RTRIM(i.infmobile), '') AS mobile, NULLIF(i.infemail, '') AS email,
  RTRIM(p.pdentist) AS dentistId, p.pinactive AS inactive"""

# Deleted patients leave rows in child tables, so the next pid must clear every pid-bearing table.
# pat + inf are always created together (1:1), mirroring ABELDent-created rows.
CREATE_PATIENT = f"""
SET XACT_ABORT ON;
BEGIN TRAN;
IF NOT EXISTS (SELECT 1 FROM dnt WHERE RTRIM(did) = @dentistId) THROW 50002, 'VALIDATION: Unknown dentist', 1;
DECLARE @pid int = 1 + (SELECT MAX(id) FROM (
  SELECT MAX(pid) id FROM pat WITH (UPDLOCK, HOLDLOCK) UNION ALL SELECT MAX(infpid) FROM inf
  UNION ALL SELECT MAX(apid) FROM apt UNION ALL SELECT MAX(apid) FROM aptdel UNION ALL SELECT MAX(apnpid) FROM apn
  UNION ALL SELECT MAX(cpid) FROM cnt UNION ALL SELECT MAX(rpid) FROM rcl UNION ALL SELECT MAX(PatientID) FROM AppointmentLog) m);
INSERT INTO pat (pid, plname, pfname, pinitial, pdentist, phygienist, pbirth, pgender, pmrmrs, pstatus,
  pchargeto, paptinvl, pnormunits, plnamcase, pfnamcase, pnativetongue, psince, pphone, pworkphn, paltid)
VALUES (@pid, UPPER(@lastName), UPPER(@firstName), '', @dentistId, '', @birthDate, @gender,
  CASE @gender WHEN 'F' THEN 'Ms.' WHEN 'M' THEN 'Mr.' ELSE '' END, ' ',
  0, 6, 3, 1, 1, ' ', CAST(GETDATE() AS date), LEFT(@phone + SPACE(10), 10), SPACE(10), SPACE(12));
INSERT INTO inf (infpid, infnote, infmedical, infothphn, infothphndesc, infemail, infmobile, inflocation)
VALUES (@pid, '', '', SPACE(10), '', @email, LEFT(@mobile + SPACE(10), 10), 1);
COMMIT;
SELECT {_PATIENT_COLUMNS} FROM pat p LEFT JOIN inf i ON i.infpid = p.pid WHERE p.pid = @pid;"""

# atime is a time-of-day on the 1899-12-30 zero date; durations are in scheduler units (sys.sunitmins).
CREATE_APPOINTMENT = """
SET XACT_ABORT ON;
DECLARE @atime datetime = CAST('1899-12-30' AS datetime) + CAST(CAST(@start AS time) AS datetime);
DECLARE @unit int = (SELECT TOP 1 sunitmins FROM sys WHERE sunitmins > 1);
DECLARE @units smallint = CEILING(@durationMinutes * 1.0 / @unit);
BEGIN TRAN;
IF NOT EXISTS (SELECT 1 FROM pat WHERE pid = @patientId) THROW 50001, 'VALIDATION: Unknown patient', 1;
IF NOT EXISTS (SELECT 1 FROM dnt WHERE RTRIM(did) = @providerId) THROW 50002, 'VALIDATION: Unknown provider', 1;
IF NOT EXISTS (SELECT 1 FROM apt WHERE RTRIM(achair) = @chair) THROW 50005, 'VALIDATION: Unknown chair', 1;
IF DATEDIFF(MINUTE, 0, CAST(@start AS time)) % @unit <> 0 THROW 50003, 'VALIDATION: Start is off the scheduler grid', 1;
-- Overlap: an existing [atime, atime + units) in the same chair intersects the new slot
IF EXISTS (SELECT 1 FROM apt WITH (UPDLOCK, HOLDLOCK) WHERE adate = @date AND RTRIM(achair) = @chair
  AND atime < DATEADD(MINUTE, @units * @unit, @atime) AND DATEADD(MINUTE, atimereq * @unit, atime) > @atime)
  THROW 50004, 'VALIDATION: Slot overlaps an existing appointment', 1;
DECLARE @id uniqueidentifier = NEWID();
INSERT INTO apt (apid, adate, achair, atime, astatus, atimereq, apxfee, apwork, apwrk2, adid, apallocate,
  aconfstat, alabstat, ashortstat, afuture, aduedate, aidentifier, UpdateInfo)
VALUES (@patientId, @date, @chair, @atime, ' ', @units, 0, @work, '', @providerId, CAST(@units AS varchar(10)),
  ' ', ' ', ' ', SPACE(4), @date, @id, 0);
COMMIT;
SELECT CAST(a.aidentifier AS varchar(36)) AS id, a.apid AS patientId, CONVERT(char(10), a.adate, 23) AS date,
  CONVERT(char(5), a.atime, 108) AS start, a.atimereq * @unit AS durationMinutes, RTRIM(a.achair) AS chair,
  RTRIM(a.adid) AS providerId, a.apwork AS work
FROM apt a WHERE a.aidentifier = @id;"""


def create_patient(last_name, first_name, birth_date, gender, dentist_id,
                   phone="", mobile="", email="", commit=False) -> dict:
    params = dict(lastName=last_name, firstName=first_name, birthDate=birth_date, gender=gender,
                  dentistId=dentist_id, phone=phone, mobile=mobile, email=email)
    return sql(CREATE_PATIENT, params, mode="write" if commit else "dry-run")[0]


def create_appointment(patient_id, date, start, duration_minutes, chair, provider_id,
                       work="", commit=False) -> dict:
    params = dict(patientId=patient_id, date=date, start=start, durationMinutes=duration_minutes,
                  chair=chair, providerId=provider_id, work=work)
    return sql(CREATE_APPOINTMENT, params, mode="write" if commit else "dry-run")[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="kind", required=True)
    p = sub.add_parser("patient")
    p.add_argument("last_name"); p.add_argument("first_name")
    p.add_argument("birth_date", help="YYYY-MM-DD"); p.add_argument("gender", choices=["F", "M", ""])
    p.add_argument("dentist_id", help="dnt.did, e.g. T")
    p.add_argument("--phone", default=""); p.add_argument("--mobile", default=""); p.add_argument("--email", default="")
    a = sub.add_parser("appointment")
    a.add_argument("patient_id", type=int); a.add_argument("date", help="YYYY-MM-DD")
    a.add_argument("start", help="HH:MM on the scheduler grid"); a.add_argument("duration_minutes", type=int)
    a.add_argument("chair"); a.add_argument("provider_id"); a.add_argument("--work", default="")
    for s in (p, a):
        s.add_argument("--commit", action="store_true", help="really write (default: dry run, rolled back)")
    args = vars(ap.parse_args())
    kind = args.pop("kind")
    try:
        row = (create_patient if kind == "patient" else create_appointment)(**args)
    except VmSqlError as e:
        sys.exit(f"error: {e}")
    print(json.dumps(row, indent=2))
    print("committed" if args["commit"] else "dry run: rolled back (pass --commit to write)", file=sys.stderr)


if __name__ == "__main__":
    main()
