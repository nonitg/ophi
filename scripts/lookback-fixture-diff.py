#!/usr/bin/env python3
"""Prove the PMS-shaped fixtures re-derive the same Look-Back as cases/lookback/*.yaml did."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from ophi.lookback import run_lookback
from ophi.sources.fixture_lookback import fixture_lookback

FIELDS = ("patient_name", "code", "tooth_fdi", "submitted_on", "decision", "fee_dollars",
          "gaps", "unverifiable", "other_open", "resubmitted", "resubmitted_decision", "denial_text")

a, b = run_lookback(), fixture_lookback()
ok = True
for name in ("submitted", "denied", "denied_dollars", "approved", "denied_with_doc_gap",
             "denied_with_doc_gap_dollars", "never_resubmitted", "never_resubmitted_dollars", "undecided"):
    x, y = getattr(a, name), getattr(b, name)
    ok &= x == y
    print(f"  {'ok  ' if x == y else 'DIFF'} {name}: yaml={x} pms={y}")

key = lambda r: (r.patient_name, r.submitted_on)
for ra, rb in zip(sorted(a.rows, key=key), sorted(b.rows, key=key), strict=True):
    for f in FIELDS:
        x, y = getattr(ra, f), getattr(rb, f)
        if x != y:
            ok = False
            print(f"  DIFF {ra.patient_name} {f}: yaml={x!r} pms={y!r}")
print("MATCH" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
