"""Print each case's stage on the board, for comparing before/after a demo reset."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ophi import db_store
from ophi.outcomes.weights import load as load_weights
from ophi.service import CaseService

svc = db_store.service_from_env(weights=load_weights()) or CaseService(weights=load_weights())
for cid in sorted(svc.case_ids()):
    v = svc.view(cid)
    print(f"{cid:<16} {v.stage:<16} {v.case.patient.display_name}")
