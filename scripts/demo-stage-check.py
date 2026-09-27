#!/usr/bin/env python3
"""The staged demo (outputs/ophi-demo) must serve the board under its own base path, from the recording alone."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1] / "outputs" / "ophi-demo"
SLUG = "demo-4ajsmu"

os.environ["OPHI_BASE_PATH"] = f"/{SLUG}"
os.environ["OPHI_VAR_DIR"] = "/tmp/ophi-stage-check"
os.environ["USE_MOCK_PMS_API"] = "true"
os.environ.pop("USE_ABELDENT_PMS", None)
os.environ.pop("SUPABASE_DB_URL", None)  # the check reads the staged files, not the demo's database
sys.path.insert(0, str(STAGE))

from fastapi.testclient import TestClient  # noqa: E402

from ophi.web.app import app  # noqa: E402

assert Path(app.state.svc.repository.snapshot_path).is_relative_to(STAGE), "the app read the repo's snapshot, not the staged one"
with TestClient(app) as client:
    for path in [f"/{SLUG}", f"/{SLUG}/recover", f"/{SLUG}/results"]:
        r = client.get(path)
        title = re.search(r"<h1[^>]*>(.*?)</h1>", r.text, re.S)
        print(f"{path:24} {r.status_code}  {(title.group(1).strip() if title else '')[:50]}")
        r.raise_for_status()

# Every patient the board showed from the live VM must still be on the staged demo's board.
EXPECTED = ["Jeanette Smith", "Valerie Espenhain", "Yathu Gargyyyy", "Lenny Jones", "Christa Galatio",
            "John Provost", "Bob Miller", "Charles Watson", "Betty Martin", "Patrica Rosco", "Claude Zztest",
            "Norma Bruhhhhh Please", "Mathew Cherski", "Susan Goertsen", "Kris Randal", "Sumi Yokoyama"]
with TestClient(app) as client:
    html = client.get(f"/{SLUG}").text
missing = [n for n in EXPECTED if n not in html]
print(f"patients on the board: {len(EXPECTED) - len(missing)}/{len(EXPECTED)}")
if missing:
    print("MISSING:", missing)
    raise SystemExit(1)
