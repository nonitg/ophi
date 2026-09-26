"""Print the request text Laya reads for each demo case (cases/demo), via ophi.outcomes.case_export.

Usage: .venv/bin/python scripts/laya-demo-text.py [case_id ...]
"""
import sys
from datetime import date

from ophi.outcomes.case_export import to_export
from ophi.outcomes.training_set import Example, request_text
from ophi.service import CaseService

svc = CaseService()
for cid in sys.argv[1:] or svc.case_ids():
    case = svc.base_case(cid)
    e = Example(preauth_id=cid, clinic="demo", submitted_on=case.as_of, decided_on=None, sent=to_export(case), decision="UNSPECIFIED")
    print(f"== {cid}\n{request_text(e)}\n")
