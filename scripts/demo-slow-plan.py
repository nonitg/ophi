#!/usr/bin/env python
"""Run the demo with the fix plan deliberately slow, to see the case page's skeleton do its job.

The real models take seconds on a cold case; this stands in for them without a GPU.
Usage: PYTHONPATH=. .venv/bin/python scripts/demo-slow-plan.py [seconds] [port]
"""

import sys
import time
from pathlib import Path

import uvicorn

from ophi.outcomes import readout
from ophi.service import CaseService, Store
from ophi.web.app import create_app

DELAY = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8099


class SlowScorer:
    def __init__(self):
        self._done = {}

    def cached(self, case):
        return self._done.get(case.case_id)

    def latest(self, case):
        if case.case_id not in self._done:
            time.sleep(DELAY)
            self._done[case.case_id] = readout.load(case.case_id)
        return self._done[case.case_id]

    def warm_cases(self, cases):
        pass


app = create_app(auto_rules_check=False, svc=CaseService(store=Store(Path("var/slow-demo"))),
                 packets_dir=Path("var/slow-demo/packets"), seed_demo=True, live_ml=False)
app.state.live = SlowScorer()
uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
