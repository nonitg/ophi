#!/usr/bin/env python3
"""Check /recover and /results in the default (fixture) mode after the PMS look-back change.

The demo numbers are the sales instrument, so they must not move: 10 denials never resubmitted, $11,455.
"""
import re
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from ophi.service import CaseService, Store
from ophi.web.app import create_app

tmp = Path(tempfile.mkdtemp())
svc = CaseService(store=Store(tmp / "state"))
app = create_app(auto_rules_check=False, svc=svc, packets_dir=tmp / "packets", live_ml=False)
c = TestClient(app, follow_redirects=False)

ok = True
page = c.get("/recover")
rows = svc.recover_rows()
print(f"/recover              {page.status_code}  rows={len(rows)}  calls rendered={page.text.count('class=\"call ')}")
for want in ("10 past denials were never resubmitted", "$11,455", "Leila Farahani"):
    hit = want in page.text
    ok &= hit
    print(f"  {'ok ' if hit else 'MISS'} {want}")
print(f"  orphans={svc.orphan_followups()} (expect 0 on a fresh store)")

res = c.get("/results")
print(f"/results              {res.status_code}")
ok &= res.status_code == 200 and "$11,455" in res.text
print(f"  {'ok ' if '$11,455' in res.text else 'MISS'} $11,455 on Results")

board = c.get("/")
print(f"/ (board)             {board.status_code}")
ok &= board.status_code == 200

# a follow-up against a row the source no longer lists must be counted, not hidden
svc.record_followup(rows[0]["row"].case_id, "rebooking", "", "Kim Osei")
after = c.get("/recover").text
ok &= "Rebooking" in after
print(f"  {'ok ' if 'Rebooking' in after else 'MISS'} follow-up recorded and shown")

print("\nPASS" if ok else "\nFAIL")
sys.exit(0 if ok else 1)
