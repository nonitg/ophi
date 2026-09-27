"""Add each demo readout's note fingerprint (ophi.outcomes.readout.note_fingerprint) without re-running the models.

laya-demo-predict.py writes it on every new run; this backfills files scored before the field existed.
Usage: PYTHONPATH=. .venv/bin/python scripts/readout-note-hash.py
"""
from ophi.outcomes.readout import READOUT_DIR, load, note_fingerprint
from ophi.service import CaseService

svc = CaseService()
for cid in svc.case_ids():
    rd, case = load(cid), svc.base_case(cid)
    if rd is None:
        continue
    # The note is the same in every scored state (safe fixes only change lab codes); check the plan still matches.
    assert rd.matching(case) is not None or any(p.state == "safe_fixes" for p in rd.plans), f"{cid}: chart changed since scoring"
    for p in rd.plans:
        p.note_sha256 = note_fingerprint(case)
    (READOUT_DIR / f"{cid}.json").write_text(rd.model_dump_json(indent=1) + "\n")
    print(cid, rd.plans[0].note_sha256[:12], "plan matches" if rd.matching(case) else "safe-fixes plan")
