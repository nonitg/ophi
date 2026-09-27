"""How long live fix plans take: model load once, then one plan per demo case (all what-ifs), as a board load would."""
import time

from ophi.outcomes.case_export import to_export
from ophi.outcomes.fixer import plan_fixes
from ophi.outcomes.risk import RiskModel
from ophi.rules.loader import default_pack
from ophi.service import CaseService

t = time.time(); m = RiskModel.load(); print(f"load {time.time() - t:.1f}s")
svc, pack = CaseService(), default_pack()
cases = [svc.base_case(cid) for cid in svc.case_ids()]
plan_fixes(to_export(cases[0]), cases[0].as_of, pack, m)  # warm-up
for c in cases:
    t = time.time(); p = plan_fixes(to_export(c), c.as_of, pack, m)
    print(f"{c.case_id:10} {1000 * (time.time() - t):5.0f}ms  now={p.now.score}")
