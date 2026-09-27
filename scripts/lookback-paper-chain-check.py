#!/usr/bin/env python3
"""A request answered on paper, then resent and answered electronically: is it reported at all?"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "tests"))

from test_lookback_pms import ROWS, fetch_charts  # noqa: E402

from ophi.lookback import report  # noqa: E402
from ophi.sources.abeldent import list_predeterminations  # noqa: E402
from ophi.sources.pms_lookback import lookback_rows  # noqa: E402

DENIED = "A04=23|G05=E|G15-1=0|G26-1=Denied as per the plan criteria."
PAPER = "A04=13|G05=H|G07=Response will be mailed to the office."

def run(label, raw):
    rows, undecided = lookback_rows(list_predeterminations(lambda q, p: raw), fetch_charts)
    rep = report(rows, "test", undecided)
    call = [r for r in rows if r.decision == "denied" and not r.resubmitted]
    print(f"{label:34} submitted={rep.submitted} denied={rep.denied} ${rep.denied_dollars:>7,.0f} "
          f"undecided={rep.undecided} on_call_list={len(call)}")

paper = dict(ROWS[0], claim_id=9101, sent_on="2026-08-01", status="Q", received=PAPER)
elec2 = dict(ROWS[0], claim_id=9102, sent_on="2026-09-10", status="P", received=DENIED)
elec1 = dict(ROWS[0], claim_id=9100, sent_on="2026-08-01", status="P", received=DENIED)

run("both electronic (denied, denied)", [elec1, elec2])
run("first paper, second denied", [paper, elec2])
run("single denial, never resent", [elec2])
