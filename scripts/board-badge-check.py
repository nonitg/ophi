"""Risk badges on the board: how many show cold (before warming) vs warm, so the non-blocking board
isn't silently dropping what staff rely on."""
import re, time, logging
from fastapi.testclient import TestClient
from ophi import demo
from ophi.service import CaseService
from ophi.outcomes.weights import load as load_weights
from ophi.web.app import create_app

logging.basicConfig(level=logging.WARNING)
svc = CaseService(weights=load_weights()); demo.seed(svc)
app = create_app(svc=svc, seed_demo=False, live_ml=True, auto_rules_check=False)

def badges(html):
    return len(re.findall(r'class="[^"]*risk[^"]*"', html))

with TestClient(app) as c:
    cold = c.get("/").text
    print("cold badges:", badges(cold))
    time.sleep(25)
    warm = c.get("/").text
    print("warm badges:", badges(warm))
