"""How long a live fix plan takes: model load once, then one case's plan (all what-ifs)."""
import time
from ophi.outcomes.case_export import to_export
from ophi.outcomes.fixer import plan_fixes
from ophi.outcomes.risk import RiskModel
from ophi.rules.loader import default_pack
from ophi.service import CaseService

for dev in ("cpu", None):
    t = time.time(); m = RiskModel.load(device=dev); load = time.time() - t
    svc, pack = CaseService(), default_pack()
    c = svc.base_case("kowalchuk")
    plan_fixes(to_export(c), c.as_of, pack, m)  # warm-up
    t = time.time(); p = plan_fixes(to_export(c), c.as_of, pack, m); run = time.time() - t
    print(f"device={dev or 'auto'} load {load:.1f}s  plan {run*1000:.0f}ms  now={p.now.score}")
