"""The demo app on a throwaway store, so browser runs never touch var/ state. Usage: e2e-ml-serve.py <state_dir> <port>"""
import sys
from pathlib import Path

import uvicorn

from ophi.outcomes.weights import load as load_weights
from ophi.service import CaseService, Store
from ophi.web.app import create_app

app = create_app(svc=CaseService(store=Store(Path(sys.argv[1])), weights=load_weights()), seed_demo=True, live_ml=True)
uvicorn.run(app, host="127.0.0.1", port=int(sys.argv[2]))
