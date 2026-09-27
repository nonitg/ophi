"""Look-Back rows from the PMS's own predeterminations, instead of the fictional `cases/lookback/` history.

For each predetermination the PMS sent and Sun Life answered electronically, re-judge the chart as it stood on
the submission date and report the documentation gap. Sun Life's denial text is carried verbatim but never
trusted to classify: the engine finds the gap itself.

What a chart dump cannot faithfully reconstruct, and which the page must not overstate:
  - "In the chart" is not "attached to the submission". The honest claim is that no such document was in the
    chart on the day it was sent, never that we know what Sun Life received.
  - Answers that came back on paper (status Q/H/B) never reach the PMS, so they carry no outcome at all. They
    are counted as `undecided`, never as approvals -- at many clinics they are most of the denials.
  - The dump reads today's rows (`Deleted=0`, `IsLatest=1`). A radiograph deleted since, or a note revised
    since, is read at its current value; there is no audit table to read the true past from.
  - Coverage is current-state, so a patient whose plan changed is judged against the wrong one.
  - Clinician assertions were never answered retrospectively, so only *documentary* gaps are recoverable.
  - Resubmission is inferred from a later claim on the same tooth. One sent on paper, by portal, or from
    another PMS is invisible, so "never resubmitted" over-counts in the clinic's favour.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Iterable
from datetime import date

from ophi.casegen.dsl import build_case
from ophi.lookback import LookBackReport, LookBackRow, _initials, gaps_of, report
from ophi.rules.loader import default_pack
from ophi.sources.abeldent import Predetermination, list_predeterminations
from ophi.sources.chart_case import chart_to_dsl

log = logging.getLogger(__name__)

FetchCharts = Callable[[list[int]], dict[int, dict]]

# DSL sections whose entries carry their own date, so the chart can be cut back to the submission day.
DATED_SECTIONS = ("radiographs", "perio_charts", "history", "notes", "tx_plans")


def _as_date(value) -> date | None:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _upto(entries: Iterable[dict], day: date) -> list[dict]:
    return [e for e in entries if (d := _as_date(e.get("date"))) is not None and d <= day]


def _truncate(dsl: dict, chart: dict, day: date) -> dict:
    """Cut the chart back to the day it was sent. Done here rather than left to the engine: a film dated after
    the submission would come back `indeterminate` ("the PMS couldn't show it") instead of the real gap, and can
    hide an older film when the engine picks the newest matching artifact."""
    for section in DATED_SECTIONS:
        if isinstance(dsl.get(section), list):
            dsl[section] = _upto(dsl[section], day)
    exams = _upto((chart.get("perio_exams") or {}).get("items", []), day)
    latest = max(exams, key=lambda e: e["date"], default=None)
    dsl["dentition"] = {"missing": (latest.get("pocket") or {}).get("teeth_no_value_fdi", []) if latest else []}
    return dsl


def _chart_item(chart: dict, trans_id: int | None) -> dict | None:
    """The chart row a claim was for. Matched on trans_id: across a year the same tooth may be sent twice."""
    if trans_id is None:
        return None
    for section in ("planned_procedures", "completed_procedures"):
        for item in (chart.get(section) or {}).get("items", []):
            if item.get("trans_id") == trans_id:
                return item
    return None


def _attempts(claims: list[Predetermination]) -> list[list[Predetermination]]:
    """Claims grouped into attempts at the same thing -- same patient, code and tooth -- oldest first.

    A tooth sent twice is one recoverable request, not two: the clinic already tried again, so the chain is
    reported once, judged as the chart stood on the first attempt, carrying the last answer it got.
    """
    chains: dict[tuple, list[Predetermination]] = {}
    for c in claims:
        chains.setdefault((c.patient_id, c.code, c.tooth), []).append(c)
    return [sorted(v, key=lambda o: o.sent_on) for v in chains.values()]


def lookback_rows(claims: list[Predetermination], fetch_charts: FetchCharts,
                  providers: dict[str, str] | None = None,
                  clinic: str = "ABELDent") -> tuple[list[LookBackRow], int]:
    """Rows for the Look-Back, plus the count of predeterminations still waiting on an answer."""
    chains = _attempts(claims)
    # Judged from the earliest attempt Sun Life answered electronically, not the earliest attempt: one answered
    # on paper and then resent is an ordinary path, and the answer we can read is the one the gap has to explain.
    # A chain no attempt has answered is one request still waiting, however many times it was sent.
    answered = [(next((a for a in c if a.outcome), None), c[-1]) for c in chains]
    decided = [(first, last) for first, last in answered if first]
    undecided = len(chains) - len(decided)
    charts = fetch_charts(sorted({c.patient_id for c, _ in decided})) if decided else {}
    rows = []
    for claim, last in decided:
        chart = charts.get(claim.patient_id)
        item = _chart_item(chart, claim.trans_id) if chart else None
        if item is None:  # the chart row was deleted since, so the gap can't be re-derived
            undecided += 1
            continue
        case_id = f"pred_{claim.claim_id}"
        dsl = chart_to_dsl(chart, item, case_id=case_id, as_of=claim.sent_on, providers=providers, clinic=clinic)
        case = build_case(_truncate(dsl, chart, claim.sent_on), case_id)
        gaps, unverifiable, other = gaps_of(case, default_pack(claim.sent_on))  # the rules in force that day
        name = claim.patient_name or case.patient.display_name
        resub = last if last is not claim else None
        rows.append(LookBackRow(
            case_id=case_id, patient_label=_initials(name), patient_name=name, code=claim.code,
            tooth_fdi=claim.tooth, submitted_on=claim.sent_on, decision=claim.outcome,
            fee_dollars=(claim.fee_cents or 0) / 100, gaps=gaps, unverifiable=unverifiable, other_open=other,
            resubmitted=resub is not None, resubmitted_decision=resub.outcome if resub else None,
            denial_text=claim.reason,
        ))
    return rows, undecided


class PmsLookBack:
    """The clinic's own Look-Back, rebuilt only when ABELDent changed. A rebuild is a chart pull for every
    patient behind a decided predetermination, so it is far too slow to run per page; `/results` alone asks for
    it twice in one request. When the VM is unreachable the last good report still stands -- staff keep working
    from a list that is a few minutes old rather than meeting an error."""

    CHECK_SECONDS = 15

    # A new predetermination changes no chart table, so the chart stamp alone would miss it.
    _STAMP_SQL = ("SELECT (SELECT CONVERT(varchar(23), MAX(last_user_update), 126) FROM sys.dm_db_index_usage_stats "
                  "WHERE database_id = DB_ID()) AS charts, "
                  "(SELECT MAX(ClaimID) FROM Claim WHERE IsPredetermination = 1) AS claims")

    def __init__(self, repo, clinic: str = "ABELDent"):
        self.repo = repo
        self.clinic = clinic
        self._lock = threading.Lock()
        self._cache: tuple[float, LookBackReport] | None = None
        self._stamp: tuple | None = None

    def report(self) -> LookBackReport:
        if self._cache is not None and time.monotonic() - self._cache[0] < self.CHECK_SECONDS:
            return self._cache[1]
        with self._lock:
            if self._cache is not None and time.monotonic() - self._cache[0] < self.CHECK_SECONDS:
                return self._cache[1]  # another request rebuilt it while this one waited
            try:
                row = self.repo.sql(self._STAMP_SQL, None)[0]
                stamp = (row["charts"], row["claims"])
            except RuntimeError as e:  # VM unreachable: staff keep the last pull
                if self._cache is None:
                    raise
                log.warning(f"ABELDent look-back change check skipped: {e}")
                return self._cache[1]
            built = self._build() if self._cache is None or stamp != self._stamp else self._cache[1]
            self._cache, self._stamp = (time.monotonic(), built), stamp
            return built

    def _build(self) -> LookBackReport:
        claims = list_predeterminations(self.repo.sql)
        providers = {r["id"]: r["name"] for r in self.repo.sql("SELECT RTRIM(did) AS id, RTRIM(dname) AS name FROM dnt", None)}
        rows, undecided = lookback_rows(claims, self.repo.fetch_patient_charts, providers, self.clinic)
        return report(rows, "last 12 months", undecided)
