"""Print each demo case's stage, verdict and blocking chart actions (for designing flows over the demo set)."""
from ophi.service import CaseService, Store
import tempfile
from pathlib import Path
from ophi import demo
from ophi.workflow import chart_actions

svc = CaseService(store=Store(Path(tempfile.mkdtemp()) / "s"))
demo.seed(svc)
for v in svc.queue():
    acts = chart_actions(v.assessment)
    print(f"{v.case.case_id:10} {v.stage.value:10} {v.assessment.verdict.value:22} {v.assessment.schedule.disposition}")
    for a in acts:
        print(f"    {a.action_type:18} {a.unblocks} {a.title}")
