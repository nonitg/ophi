"""Print the pre-read evidence sentences for demo cases, to check they read plainly."""
from ophi.assertions.preread import pre_reads
from ophi.service import CaseService

svc = CaseService()
for name in ("kowalchuk", "deng"):
    case = svc.view(name).case
    print(f"== {name} #{case.requested_tooth}")
    for cid, pr in pre_reads(case, svc.pack, note=None).items():
        for e in pr.evidence:
            print(f"  [{e.source}/{e.stance}] {e.text}.")
