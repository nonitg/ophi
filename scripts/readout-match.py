"""Which demo cases still have a fix plan (cases/demo/laya) that matches the chart as it reads now.

Usage: .venv/bin/python scripts/readout-match.py
A case whose chart changed after its plan was made shows no denial risk until scripts/laya-demo-predict.py is rerun.
"""
import tempfile
from pathlib import Path

from ophi.outcomes import readout
from ophi.service import CaseService, Store

svc = CaseService(store=Store(Path(tempfile.mkdtemp()) / "s"))
for cid in svc.case_ids():
    rd = readout.load(cid)
    v = svc.view(cid)
    plan = rd.matching(v.case) if rd else None
    print(f"{cid:10} {'plan' if rd else 'none':5} {'MATCH' if plan else 'stale':6} {plan['now']['level'] + ' -> ' + plan['after_fixes']['level'] if plan else ''}")
