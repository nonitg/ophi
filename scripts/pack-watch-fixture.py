"""Draft a pack update from the fake April 2027 factsheet fixture, into a scratch dir, and print report.md.

Usage: PYTHONPATH=. .venv/bin/python scripts/pack-watch-fixture.py <scratch_dir> [--approve "Name"]
Shows what `ophi pack draft` would write if CDCP published fixtures/pack_watch/new-factsheet.html. Serves the
same fake web as the tests (ophi.rules.fixture_web).
"""
import shutil
import sys
from datetime import date
from pathlib import Path

from ophi.rules import approve, draft, watch
from ophi.rules.fixture_web import WATCH, fetcher, served
from ophi.rules.loader import CDCP_DIR, pack_in_force

BASE = "2026-01-26"

out = Path(sys.argv[1])
shutil.rmtree(out, ignore_errors=True)
shutil.copytree(CDCP_DIR / BASE, out / "cdcp" / BASE)
cdcp, today = out / "cdcp", date.today()
get = fetcher(served(cdcp / BASE))
d = draft.draft(watch.check(cdcp / BASE, today, get, config=WATCH), today, get, drafts_dir=cdcp / "drafts")
print(d.report_md)
if "--approve" in sys.argv:
    target = approve.approve(d.dir, sys.argv[sys.argv.index("--approve") + 1], today, cdcp_dir=cdcp,
                             status=out / "status.json")
    print(f"approved -> {target}")
    for day in (today, date(2027, 3, 31), date(2027, 4, 1)):
        print(f"  in force {day}: {pack_in_force(day, cdcp).version}")
