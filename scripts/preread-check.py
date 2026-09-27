"""Print Ophi's pre-read of every demo case's clinical criteria, as the dentist would see it.
Usage: PYTHONPATH=. .venv/bin/python scripts/preread-check.py [case_id ...]
"""
import sys

from ophi.assertions.preread import pre_reads
from ophi.outcomes import readout
from ophi.service import CaseService

svc = CaseService()
for cid in sys.argv[1:] or svc.case_ids():
    view = svc.view(cid)
    rd = readout.load(cid)
    note = rd.note_answers(view.case) if rd else None
    reads = pre_reads(view.case, svc.pack, note)
    filled = sum(1 for r in reads.values() if r.suggest)
    print(f"\n{cid} #{view.case.requested_tooth} stage={view.stage.value} laya={'yes' if note else 'no'}  pre-filled {filled}/{len(reads)}")
    for r in reads.values():
        print(f"  {str(r.suggest or 'YOU'):15} {r.criterion_id:26} {'film ' if r.on_film else '     '}"
              + " | ".join(f"[{e.source}:{e.stance[0]}] {e.text}" for e in r.evidence))
