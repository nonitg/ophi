"""Simulate staff use: open the board, pause as a reader would, then click into cases. Times each page."""
import time, logging, sys
from fastapi.testclient import TestClient
from ophi import demo
from ophi.service import CaseService
from ophi.outcomes.weights import load as load_weights
from ophi.web.app import create_app

logging.basicConfig(level=logging.WARNING)
svc = CaseService(weights=load_weights())
demo.seed(svc)
app = create_app(svc=svc, seed_demo=False, live_ml=True, auto_rules_check=False)

PAUSE = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
with TestClient(app) as c:
    t = time.perf_counter(); r = c.get("/"); print(f"board (cold)   {time.perf_counter()-t:.2f}s  {r.status_code}")
    time.sleep(PAUSE)  # staff reading the board while the warmer runs
    for cid in svc.case_ids()[:5]:
        t = time.perf_counter(); r = c.get(f"/cases/{cid}")
        print(f"case {cid:<12} {time.perf_counter()-t:.2f}s  {r.status_code}")
    t = time.perf_counter(); r = c.get("/"); print(f"board (warm)   {time.perf_counter()-t:.2f}s  {r.status_code}")
