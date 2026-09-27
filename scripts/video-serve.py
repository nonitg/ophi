"""Serve the seeded demo for video capture with a fixed morning clock, so on-screen activity times read
"Sep 17, 10:12 AM" onward instead of whatever the real time of day is.

Usage: .venv/bin/python scripts/video-serve.py <port> <state_dir> [demo|recorded]
  demo      the fictional demo cases (Teresa Kowalchuk and the rest), clock Sep 17, 2026
  recorded  the clinic's own ABELDent PMS as recorded in mocks/pms/snapshot.json, with the PMS sync that marks
            requests sent and reads Sun Life's answers; clock Sep 27, 2026, after the recording
Past requests (similar requests, Past outcomes) need SUPABASE_DB_URL; scripts/video-capture.sh starts a local one.
"""
import shutil
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import uvicorn

from ophi.outcomes.weights import load as load_weights
from ophi.rules import auto
from ophi.service import CaseService, Store
from ophi.sources.pms_repository import create_repository
from ophi.web.app import create_app

port, root = int(sys.argv[1]), Path(sys.argv[2])
mode = sys.argv[3] if len(sys.argv) > 3 else "demo"
day = datetime(2026, 9, 27 if mode == "recorded" else 17, 14, 12, tzinfo=UTC)  # 10:12 AM in Toronto
t0 = time.monotonic()


def clock() -> datetime:
    # Real elapsed time keeps the audit log in click order.
    return day + timedelta(seconds=time.monotonic() - t0)


repo = create_repository("recorded") if mode == "recorded" else None
svc = CaseService(store=Store(root / "state"), clock=clock, weights=load_weights(), repository=repo)
# The weekly CDCP source check reads and drafts against a copy of the rule packs, so a capture never writes the repo's.
cdcp = root / "cdcp"
if not cdcp.exists():
    shutil.copytree(Path(__file__).resolve().parent.parent / "packs" / "cdcp", cdcp)
rules = auto.PackEnv(cdcp_dir=cdcp, status=root / "rules-status.json")
print(f"Ophi video server ({mode}) on http://127.0.0.1:{port}  state: {root}", flush=True)
uvicorn.run(create_app(svc=svc, packets_dir=root / "packets", seed_demo=True, rules_env=rules), host="127.0.0.1", port=port, log_level="warning")
