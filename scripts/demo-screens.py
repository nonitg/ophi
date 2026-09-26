"""Serve the demo on a side port with a throwaway state store, for UI work and screenshots.

Usage: .venv/bin/python scripts/demo-screens.py [port] [state_dir]
The demo timeline is seeded. State (assertions, sign-offs, packets) goes to state_dir (default: a scratch folder), so the
real var/ demo state is never touched.
"""
import sys
import tempfile
from pathlib import Path

import uvicorn

from ophi.service import CaseService, Store
from ophi.web.app import create_app

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8799
root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(tempfile.mkdtemp(prefix="ophi-screens-"))
svc = CaseService(store=Store(root / "state"))
print(f"Ophi screenshot server on http://127.0.0.1:{port}  state: {root}", flush=True)
uvicorn.run(create_app(svc=svc, packets_dir=root / "packets", seed_demo=True), host="127.0.0.1", port=port, log_level="warning")
