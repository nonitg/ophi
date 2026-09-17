"""Recency arithmetic (docs/plan/02-reasoning.md §2 "Recency arithmetic — the boundary problem").

Both conventions are evaluated: 12 calendar months (inclusive) and 365 days. Agreement -> within/stale;
disagreement (the leap-year band) -> at_risk, never satisfied. Missing or future capture -> indeterminate.
"""

from __future__ import annotations

from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from hypothesis import given, settings, strategies as st

from colombus.engine.recency import check

# No Feb 29 falls between 2025-09-17 and 2026-09-17, so 12 months == 365 days here.
AS_OF = date(2026, 9, 17)
RANK = {"within": 0, "at_risk": 1, "stale": 2}


def test_364_days_within():
    r = check(AS_OF - timedelta(days=364), AS_OF, 12)
    assert r.status == "within"
    assert r.age_days == 364
    assert r.over_by_days is None


def test_365_days_is_inclusive_under_both_conventions():
    # The anniversary day itself still counts as "within the last 12 months" (Guide 4.0 rolling-window
    # example: a service on Apr 1 2025 is next eligible Apr 2 2026, so Apr 1 2026 is still inside).
    captured = date(2025, 9, 17)
    r = check(captured, AS_OF, 12)
    assert (AS_OF - captured).days == 365
    assert r.status == "within"
    assert r.expires_on == AS_OF


def test_366_days_stale_by_one_day():
    captured = date(2025, 9, 16)
    r = check(captured, AS_OF, 12)
    assert r.status == "stale"
    assert r.age_days == 366
    assert r.over_by_days == 1
    assert r.expires_on == date(2026, 9, 16)
    assert "2025-09-16" in r.detail and "366 days" in r.detail


def test_leap_band_is_at_risk():
    # 2027-03-01 -> 2028-03-01 spans 2028-02-29: 12 calendar months = 366 days. Calendar months says
    # current; 365 days says stale. The plan requires at_risk here, not satisfied.
    captured, as_of = date(2027, 3, 1), date(2028, 3, 1)
    assert (as_of - captured).days == 366
    r = check(captured, as_of, 12)
    assert r.status == "at_risk"
    assert r.expires_on == date(2028, 2, 29)  # last day both conventions agree
    assert "calendar months (yes)" in r.detail and "365 days (no)" in r.detail
    # One day either side of the band resolves cleanly.
    assert check(captured, date(2028, 2, 29), 12).status == "within"
    assert check(captured, date(2028, 3, 2), 12).status == "stale"


def test_none_is_indeterminate_never_pass():
    r = check(None, AS_OF, 12)
    assert r.status == "indeterminate"
    assert r.age_days is None and r.expires_on is None


def test_future_capture_is_indeterminate():
    r = check(AS_OF + timedelta(days=1), AS_OF, 12)
    assert r.status == "indeterminate"


def test_same_day_within():
    r = check(AS_OF, AS_OF, 12)
    assert r.status == "within" and r.age_days == 0


AS_OF_DATES = st.dates(min_value=date(1990, 1, 1), max_value=date(2150, 12, 31))


@settings(max_examples=300)
@given(as_of=AS_OF_DATES, months=st.integers(1, 60), ages=st.lists(st.integers(0, 3000), min_size=2, max_size=25))
def test_status_is_monotone_in_age(as_of, months, ages):
    # For a fixed as_of, moving captured_at earlier can only worsen the status: within -> at_risk -> stale.
    ranks = [RANK[check(as_of - timedelta(days=a), as_of, months).status] for a in sorted(ages)]
    assert ranks == sorted(ranks)


@settings(max_examples=300)
@given(as_of=AS_OF_DATES, age=st.integers(0, 3000))
def test_expires_on_and_agreement_invariants(as_of, age):
    captured = as_of - timedelta(days=age)
    r = check(captured, as_of, 12)
    by_months = captured + relativedelta(months=12)
    by_days = captured + timedelta(days=365)
    assert r.age_days == age
    assert r.expires_on == min(by_months, by_days)
    assert r.expires_on <= captured + relativedelta(months=12)
    assert (r.status == "within") == (as_of <= r.expires_on)
    assert (r.status == "stale") == (as_of > by_months and as_of > by_days)
    assert (r.status == "at_risk") == ((as_of <= by_months) != (as_of <= by_days))
    if r.status == "stale":
        assert r.over_by_days == (as_of - r.expires_on).days > 0


@settings(max_examples=200)
@given(as_of=AS_OF_DATES, age=st.integers(0, 3000))
def test_at_risk_band_is_exactly_366_days_across_feb_29(as_of, age):
    # The two conventions differ by at most one day, and only when the window contains a Feb 29.
    captured = as_of - timedelta(days=age)
    r = check(captured, as_of, 12)
    if r.status == "at_risk":
        assert age == 366
        assert captured + relativedelta(months=12) == as_of
