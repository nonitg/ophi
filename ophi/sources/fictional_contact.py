"""Fictional stand-ins for the contact details ABELDent's sample data carries.

The Fictional Data set ships phone numbers and a handful of addresses at real-world domains. They are the
vendor's inventions, but a hotmail address is plausibly deliverable to a real person, so nothing committed to
this repo -- chart fixtures, the recorded demo snapshot -- keeps them. A live read is untouched: the desk
needs the number that actually reaches the patient.

555-01xx and example.ca are reserved for fiction. The substitution is keyed by patient id, so a patient's
number is the same in every file and across re-recordings.
"""

from __future__ import annotations

# The columns each write site carries contact in: the built chart's patient block, and the raw rows
# SEARCH_PATIENTS returns into the snapshot.
CHART_FIELDS = ("phone", "email")
SQL_FIELDS = ("phone", "mobile", "email")


def fictional_phone(pid: int) -> str:
    return f"905-555-{pid % 10000:04d}"


def fictional_email(pid: int, given: str | None, surname: str | None) -> str:
    name = ".".join(p.strip().lower() for p in (given, surname) if p and p.strip())
    return f"{name or f'patient{pid}'}@example.ca"


def scrub_chart(chart: dict) -> dict:
    """A built chart with its patient's contact replaced, where the source had any. Absence stays absence:
    a patient with no email on file must still read as one, or the fixtures stop testing that path."""
    pat = chart.get("patient")
    if not isinstance(pat, dict):
        return chart
    pid = pat.get("pid") or 0
    if pat.get("phone"):
        pat["phone"] = fictional_phone(pid)
    if pat.get("email"):
        pat["email"] = fictional_email(pid, pat.get("given"), pat.get("surname"))
    return chart


def scrub_sql_rows(rows: list[dict]) -> list[dict]:
    """Raw patient rows, as SEARCH_PATIENTS returns them."""
    for r in rows:
        pid = r.get("id") or 0
        for f in ("phone", "mobile"):
            if r.get(f):
                r[f] = fictional_phone(pid)
        if r.get("email"):
            r["email"] = fictional_email(pid, r.get("first_name"), r.get("last_name"))
    return rows
