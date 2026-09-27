"""Read-only views of a live ABELDent's providers, patients, schedule and sent predeterminations.

Queries run through `AbelDentPmsRepository.sql`, so the lab read-only rails apply and every value
binds as an `@param`. Table semantics: docs/research/abeldent-schema.md ("Scheduling and patient tables").
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Literal

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


AnswerAt = Literal["reviewing", "mailbox", "paper", "back", "rejected"]


class Predetermination(BaseModel):
    """A predetermination ABELDent sent, where Sun Life's answer is, and the answer when it came back electronically."""

    claim_id: int
    patient_id: int
    patient_name: str | None = None
    code: str
    tooth: int | None
    trans_id: int | None = None  # the chart row this claim was for; the way back into the chart dump
    fee_cents: int | None = None  # the clinic's fee, not Sun Life's payable (that is benefit_cents)
    sent_on: date
    status: str  # Claim.Status letter
    status_label: str  # ABELDent's own wording for the letter
    answer_at: AnswerAt
    carrier: str | None
    carrier_ref: str | None  # Sun Life's number for this request, for phone follow-up
    outcome: Literal["approved", "denied"] | None = None
    decided_on: date | None = None
    benefit_cents: int | None = None
    reason: str | None = None  # Sun Life's note text, verbatim


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

# Claim.Status letters with ABELDent's labels (its ANetTransactionResultType resources) and where the answer is.
CLAIM_STATUS: dict[str, tuple[str, AnswerAt]] = {
    "S": ("Pred. Sent successfully", "reviewing"), "C": ("Received by Carrier", "reviewing"),
    "N": ("Batched by Network", "mailbox"),
    "Q": ("Pred. Sent, expect paper response", "paper"), "H": ("Held at Carrier, expect paper response", "paper"),
    "B": ("Batched by Network, expect paper response", "paper"),
    "P": ("Pred. Explanation of Benefits received", "back"), "A": ("Explanation of Benefits received", "back"),
    "R": ("Rejected", "rejected"), "M": ("Rejected, must be sent manually", "rejected"),
    "*": ("Rejected, could not be sent", "rejected"),
}

# One row per predetermination: its first line's planned procedure, and the network message its status came from.
# `trans_id` is the chart row the claim was for -- the only unambiguous way back to it across a year of history,
# where the same tooth may be submitted more than once. Bounded to 12 months: the look-back claims that window,
# and the bound is what keeps the chart pull behind it finite.
LIST_PREDETERMINATIONS = """
SELECT c.ClaimID AS claim_id, c.PatientID AS patient_id, RTRIM(t.Code) AS code, t.ToothNum AS tooth,
  t.TransID AS trans_id, t.Billed AS fee_cents,
  RTRIM(p.pfname) + ' ' + RTRIM(p.plname) AS patient_name,
  CONVERT(varchar(10), c.BillingDate, 23) AS sent_on, RTRIM(c.Status) AS status,
  NULLIF(RTRIM(c.CarrierClaimNumber), '') AS carrier_ref, RTRIM(i.insname) AS carrier,
  CONVERT(varchar(10), n.Timestamp, 23) AS answered_on, n.ReceivedMessage AS received
FROM Claim c
JOIN ClaimItem ci ON ci.ClaimID = c.ClaimID AND ci.ClaimItemNumber = 1
JOIN Transactions t ON t.TransID = ci.ServiceTransaction
LEFT JOIN pat p ON p.pid = c.PatientID
LEFT JOIN ins i ON i.inscoid = c.CarrierID
LEFT JOIN NetLog n ON n.LogEventID = c.LogEventID
WHERE c.IsPredetermination = 1 AND c.ClaimID > 0
  AND c.BillingDate >= DATEADD(month, -12, CAST(GETDATE() AS date))
ORDER BY c.BillingDate DESC"""


def list_providers(sql: Sql) -> list[Provider]:
    return [Provider(**r) for r in sql(LIST_PROVIDERS, None)]


def search_patients(sql: Sql, q: str = "") -> list[Patient]:
    return [Patient(**r) for r in sql(SEARCH_PATIENTS, {"q": q})]


def get_patient(sql: Sql, pid: int) -> Patient | None:
    rows = sql(GET_PATIENT, {"pid": pid})
    return Patient(**rows[0]) if rows else None


def list_appointments(sql: Sql, day: date) -> list[Appointment]:
    return [Appointment(**r) for r in sql(LIST_APPOINTMENTS, {"date": day.isoformat()})]


def parse_response(message: str | None) -> dict[str, list[str]]:
    """A carrier response as CDAnet field id -> values in line order ("G26-2" is line 2 of G26).
    Reads the lab's `id=value|...` form (lab/fixtures/fake-sunlife-responses.sql): the real wire layout isn't
    public, so this is the one function to replace once a real response is on hand."""
    fields: dict[str, list[str]] = {}
    for part in (message or "").split("|"):
        key, sep, value = part.partition("=")
        if sep:
            fields.setdefault(key.split("-")[0], []).append(value)
    return fields


def _predetermination(row: dict) -> Predetermination:
    label, answer_at = CLAIM_STATUS.get(row["status"], (f"Status {row['status']}", "reviewing"))
    decision = {}
    if answer_at == "back":
        f = parse_response(row["received"])
        benefit = sum(int(v or 0) for v in f.get("G15", []))  # benefit per procedure, cents
        decision = {"outcome": "approved" if benefit > 0 else "denied", "decided_on": row["answered_on"],
                    "benefit_cents": benefit, "reason": " ".join(f.get("G26", [])) or next(iter(f.get("G07", [])), None)}
    return Predetermination(**{k: row[k] for k in ("claim_id", "patient_id", "code", "tooth", "sent_on", "status",
                                                    "carrier", "carrier_ref")},
                            # A mock PMS may not carry these; the look-back skips a claim it can't place in a chart.
                            **{k: row.get(k) for k in ("trans_id", "fee_cents", "patient_name")},
                            status_label=label, answer_at=answer_at, **decision)


def list_predeterminations(sql: Sql, pid: int | None = None) -> list[Predetermination]:
    rows = sql(LIST_PREDETERMINATIONS, None)
    return [_predetermination(r) for r in rows if pid is None or r["patient_id"] == pid]
