"""Apply Ophi's safe fixes on a case, build its packet, and report which lab codes each PDF shows.

Usage: PYTHONPATH=. .venv/bin/python scripts/check-fix-in-packet.py [case_id]
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from ophi import fixes
from ophi.packet.build import build_packet
from ophi.service import CaseService, Store

cid = sys.argv[1] if len(sys.argv) > 1 else "deng"
tmp = Path(tempfile.mkdtemp())
svc = CaseService(store=Store(tmp / "state"))
print("before:", svc.view(cid).case.treatment.lab_codes)
svc.apply_fixes(cid, fixes.open_on(svc.view(cid).assessment), "check")
v = svc.view(cid)
print("after: ", v.case.treatment.lab_codes)
build_packet(v.case, v.assessment, tmp / "packet")
for pdf in sorted((tmp / "packet").rglob("*.pdf")):
    text = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout
    hits = [c for c in ("99333", "99113") if c in text]
    print(f"{pdf.name}: {hits or '-'}")
