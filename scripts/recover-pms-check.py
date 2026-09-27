#!/usr/bin/env python3
"""Check /recover in ABELDent mode: real predeterminations, the orphan note, and what happens when the VM drops.

Uses the saved Fictional Data charts, so it needs no lab VM.
"""
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[1] / "tests"))
from test_lookback_pms import ROWS, _FakeRepo, _followup, fetch_charts  # noqa: E402

from ophi.service import CaseService, Store  # noqa: E402
from ophi.sources import abeldent  # noqa: E402
from ophi.sources.pms_lookback import PmsLookBack  # noqa: E402
from ophi.web.app import create_app  # noqa: E402

claims = abeldent.list_predeterminations(lambda q, p: ROWS)
tmp = Path(tempfile.mkdtemp())
repo = _FakeRepo(claims)
lb = PmsLookBack(repo)
svc = CaseService(store=Store(tmp / "state"), clock=lambda: datetime(2026, 9, 27, 12), lookback_report=lb.report)
c = TestClient(create_app(auto_rules_check=False, svc=svc, packets_dir=tmp / "packets", live_ml=False),
               follow_redirects=False)

ok = True
page = c.get("/recover").text
for want in ("Aiko Yokoyama", "periapical", "$1,285"):
    hit = want in page; ok &= hit
    print(f"  {'ok ' if hit else 'MISS'} {want}")
print(f"  undecided (paper answers) = {svc.lookback().undecided}  (expect 1)")
ok &= svc.lookback().undecided == 1

# A follow-up left over from the fictional history must be surfaced, not silently dropped.
svc.store.add_followup("lb07", _followup())
page = c.get("/recover").text
hit = "no longer listed here" in page; ok &= hit
print(f"  {'ok ' if hit else 'MISS'} orphan note rendered (orphans={svc.orphan_followups()})")

# VM drops after a good pull: staff keep the last list rather than meeting an error.
def dead_sql(query, params=None):
    raise RuntimeError("VM unreachable")
repo.sql = dead_sql
lb._cache = (0.0, lb._cache[1])  # force the change-check path
r = c.get("/recover")
hit = r.status_code == 200 and "Aiko Yokoyama" in r.text; ok &= hit
print(f"  {'ok ' if hit else 'MISS'} VM down -> last good list still served ({r.status_code})")

# Cold cache with no VM: the page says so rather than rendering an empty, misleading list.
cold = PmsLookBack(_FakeRepo(claims)); cold.repo.sql = dead_sql
svc2 = CaseService(store=Store(tmp / "s2"), clock=lambda: datetime(2026, 9, 27, 12), lookback_report=cold.report)
c2 = TestClient(create_app(auto_rules_check=False, svc=svc2, packets_dir=tmp / "p2", live_ml=False),
                follow_redirects=False)
r2 = c2.get("/recover")
hit = r2.status_code == 503; ok &= hit
print(f"  {'ok ' if hit else 'MISS'} cold cache + no VM -> {r2.status_code} (expect 503, not an empty list)")

print("\nPASS" if ok else "\nFAIL")
sys.exit(0 if ok else 1)
