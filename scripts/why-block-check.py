"""Print a step's Why block so we can see what is left under it on the case page."""
import re
import sys

from fastapi.testclient import TestClient

from ophi.web.app import create_app

case = sys.argv[1] if len(sys.argv) > 1 else "kowalchuk"
app = create_app(live_ml=False, seed_demo=True)
with TestClient(app) as c:
    html = c.get(f"/cases/{case}").text
for block in re.findall(r'<details class="why">.*?</details>', html, re.S):
    print(block, "\n---")
