"""Serve the app with the April 2027 fixture draft waiting on /rules, for screenshots of the review page.

Usage: PYTHONPATH=. .venv/bin/python scripts/rules-review-serve.py <scratch_dir> <port> [--effective YYYY-MM-DD]
--effective re-dates the fixture draft (pack.yaml and draft.json) so the demo's requests fall under it and the
"Your open requests" list has rows; such a draft cannot be used (its date is past), it is for looking only.
Copies the current pack to <scratch_dir>, drafts from the fixture web (ophi.rules.fixture_web), and serves with
the source check pointed there and the automatic check off. Nothing touches packs/, var/ or the network.
"""
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import uvicorn

from ophi.rules import auto, draft, watch
from ophi.rules.fixture_web import WATCH, fetcher, served
from ophi.rules.loader import CDCP_DIR
from ophi.service import CaseService, Store
from ophi.web.app import create_app

BASE = "2026-01-26"
out, port = Path(sys.argv[1]), int(sys.argv[2])
shutil.rmtree(out, ignore_errors=True)
shutil.copytree(CDCP_DIR / BASE, out / "cdcp" / BASE)
cdcp, today = out / "cdcp", date.today()
env = auto.PackEnv(fetcher=fetcher(served(cdcp / BASE)), cdcp_dir=cdcp, config=WATCH, status=out / "status.json", today=today)
r = watch.check(cdcp / BASE, today, env.fetcher, WATCH)
watch.save_status(r, env.status)
d = draft.draft(r, today, env.fetcher, drafts_dir=cdcp / "drafts")
if "--effective" in sys.argv:
    eff = sys.argv[sys.argv.index("--effective") + 1]
    text = (d.dir / "pack.yaml").read_text()
    (d.dir / "pack.yaml").write_text(re.sub(r"^effective_from: \S+", f"effective_from: {eff}", text, count=1, flags=re.M))
    meta = json.loads((d.dir / "draft.json").read_text())
    (d.dir / "draft.json").write_text(json.dumps({**meta, "effective_from": eff}))
app = create_app(svc=CaseService(store=Store(out / "state")), packets_dir=out / "packets", seed_demo=True,
                 auto_rules_check=False, rules_env=env)
uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
