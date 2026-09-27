"""The Look-Back over saved ABELDent rows, for a deployment with no PMS behind it.

Same claims, charts and code path as a live clinic (`ophi/sources/pms_lookback.py`); only the transport differs.
The demo therefore shows past denials the way the product derives them, never from casegen's own history.
Regenerate the fixtures with `scripts/lookback-to-pms.py`.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ophi.lookback import LookBackReport, report
from ophi.sources.abeldent import list_predeterminations
from ophi.sources.pms_lookback import lookback_rows

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "abeldent" / "lookback"


def _charts(pids: list[int]) -> dict[int, dict]:
    return {p: json.loads((FIXTURES / "charts" / f"{p}.json").read_text()) for p in pids}


@lru_cache(maxsize=1)
def fixture_lookback(clinic: str = "ABELDent") -> LookBackReport:
    claims = list_predeterminations(lambda q, p: json.loads((FIXTURES / "claims.json").read_text()))
    providers = json.loads((FIXTURES / "providers.json").read_text())
    rows, undecided = lookback_rows(claims, _charts, providers, clinic)
    return report(rows, "last 12 months", undecided)
