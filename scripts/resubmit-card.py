"""Print the resubmit card as staff see it when Sun Life's reason hasn't been classified yet."""
import re, sys, json, tempfile
from datetime import datetime
from pathlib import Path
sys.path.insert(0, ".")
from fastapi.testclient import TestClient
from ophi import letters
from ophi.service import CaseService, Store
from ophi.sources.pms_repository import AbelDentPmsRepository
from ophi.web.app import create_app
sys.path.insert(0, "tests")
from test_decision_followup import CHARTS, fake_vm_sql, fake_sql, CHERSKI
from ophi.sources import abeldent

repo = AbelDentPmsRepository()
repo.planned_patient_ids = lambda: [158, 160, 162]
repo.fetch_patient_charts = lambda pids: {p: json.loads((CHARTS / f"{p}.json").read_text()) for p in pids}
repo.sql = fake_vm_sql
tmp = Path(tempfile.mkdtemp())
svc = CaseService(store=Store(tmp / "state"), repository=repo, clock=lambda: datetime(2026, 9, 26, 12),
                  pms_claims=lambda: abeldent.list_predeterminations(fake_sql), note_reader=lambda t: "missing_radiograph")
svc.sync_from_pms()
letters.read_note = lambda text: letters.LetterReading(outcome="denied", reason_key=None)
c = TestClient(create_app(auto_rules_check=False, svc=svc, packets_dir=tmp / "packets"), follow_redirects=False)
c.post(f"/cases/{CHERSKI}/decision", data={"outcome": "denied", "decided_on": "2026-09-17", "reason": "As per the plan criteria."})
html = c.get(f"/cases/{CHERSKI}").text
card = html[html.index("Send a new request") - 200:html.index("Ask for reconsideration")]
print(re.sub(r"\n\s*\n", "\n", card))
