"""Recency arithmetic. CDCP says "within the last 12 months" and does not say whether that is
12 calendar months or 365 days. We evaluate both; where they disagree the answer is `at_risk`, never
`satisfied`. Every check also reports when the evidence goes stale so staff can submit before then.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from dateutil.relativedelta import relativedelta

RecencyStatus = Literal["within", "at_risk", "stale", "indeterminate"]


@dataclass(frozen=True)
class RecencyResult:
    status: RecencyStatus
    age_days: int | None
    expires_on: date | None  # last day on which BOTH conventions still pass
    over_by_days: int | None  # how far past the bound, when stale
    detail: str


def check(captured_at: date | None, as_of: date, months: int) -> RecencyResult:
    if captured_at is None:
        return RecencyResult("indeterminate", None, None, None, "no capture date on record")
    if captured_at > as_of:
        return RecencyResult("indeterminate", None, None, None, f"capture date {captured_at} is after the assessment date {as_of}")

    age_days = (as_of - captured_at).days
    by_months = captured_at + relativedelta(months=months)  # inclusive: still current on this day
    by_days = captured_at + timedelta(days=round(months * 365 / 12))
    expires_on = min(by_months, by_days)

    ok_months = as_of <= by_months
    ok_days = as_of <= by_days
    bound_txt = f"{months} months"
    if ok_months and ok_days:
        return RecencyResult("within", age_days, expires_on, None,
                             f"captured {captured_at}, {age_days} days before {as_of}; within {bound_txt}; current until {expires_on}")
    if ok_months != ok_days:
        return RecencyResult("at_risk", age_days, expires_on, None,
                             f"captured {captured_at}, {age_days} days old: inside {bound_txt} by calendar months "
                             f"({'yes' if ok_months else 'no'}) but by {round(months * 365 / 12)} days ({'yes' if ok_days else 'no'}). "
                             "CDCP has not published which convention applies.")
    over = (as_of - expires_on).days
    return RecencyResult("stale", age_days, expires_on, over,
                         f"captured {captured_at}, {age_days} days before {as_of}; {bound_txt} bound passed on {expires_on} ({over} days ago)")
