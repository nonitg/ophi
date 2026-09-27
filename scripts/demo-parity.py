"""Render every demo page from the code tree on PYTHONPATH into <out_dir>, one file per page, so two trees can be
diffed (e.g. this branch against main) to prove a change leaves the demo's output alone.

Usage: OPHI_VAR_DIR=<fresh scratch dir> PYTHONPATH=<tree> .venv/bin/python scripts/demo-parity.py <out_dir>
Run from <tree>. Uses a fresh var dir, so there is no rules-watch status and live ML is off.
"""
import inspect
import re
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from ophi.web.app import create_app

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
# no network: the automatic rules check stays off (a ref that predates it has no such switch)
off = {"auto_rules_check": False} if "auto_rules_check" in inspect.signature(create_app).parameters else {}
with TestClient(create_app(live_ml=False, **off)) as c:
    board = c.get("/").text
    ids = sorted(set(re.findall(r'href="/cases/([\w-]+)"', board)))
    pages = ["/", "/recover", "/results", "/outcomes", "/settings", "/settings/audit.csv"]
    pages += [p for i in ids for p in (f"/cases/{i}", f"/cases/{i}/packet", f"/api/cases/{i}/assessment.json")]
    for page in pages:
        r = c.get(page)
        # ids and stamps minted per run are not output differences
        body = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "<uuid>", r.text)
        body = re.sub(r"\d{2}:\d{2}(:\d{2}(\.\d+)?)?", "<time>", body)
        body = re.sub(r"\?v=\d+", "?v=<mtime>", body)
        body = re.sub(r'"elapsed_ms": \d+', '"elapsed_ms": <n>', body)
        (out / (page.strip("/").replace("/", "__") or "board")).write_text(f"{r.status_code}\n{body}")
print(f"{out}: {len(pages)} pages")
