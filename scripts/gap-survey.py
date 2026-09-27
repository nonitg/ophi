#!/usr/bin/env python
"""Which blocking gaps the ABELDent lab charts raise, and what the coordinator is told to do about each.

Reads the saved chart dumps (fixtures/abeldent/fictional) rather than the VM, so it runs anywhere.
Usage: scripts/gap-survey.py [--why]
"""
import json
import pathlib
import sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ophi.engine.assess import assess
from ophi.rules.loader import pack_for
from ophi.sources.chart_case import chart_to_case

FIX = pathlib.Path(__file__).resolve().parents[1] / "fixtures/abeldent/fictional"


def main() -> None:
    show_why = "--why" in sys.argv
    counts: dict[str, int] = {}
    for f in sorted(FIX.glob("*.json"), key=lambda p: int(p.stem)):
        chart = json.loads(f.read_text())
        crowns = [p for p in chart["planned_procedures"]["items"] if p["code"].startswith("27") and p["tooth_fdi"]]
        if not crowns:
            continue
        crown = next((p for p in crowns if p["status"] == "planned"), crowns[0])
        cid = f"abeldent_{f.stem}"
        case = chart_to_case(chart, crown, case_id=cid, as_of=date.today(), clinic="lab")
        a = assess(case, pack_for(case))
        print(f"{cid:14} {case.patient.display_name:18} {a.verdict.value}")
        for x in a.actions:
            if not x.blocking:
                continue
            counts[x.unblocks[0]] = counts.get(x.unblocks[0], 0) + 1
            print(f"   [{x.action_type:18}] {x.title}")
            if show_why:
                print(f"      {x.why}")
    print("\nblocking gaps by requirement:", dict(sorted(counts.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main()
