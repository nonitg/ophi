"""Render every board and case page for both roles and report any Ophi 'O' monogram left."""
import re
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from ophi.web.app import create_app
from ophi.service import CaseService, Store

tmp = Path(tempfile.mkdtemp())
app = create_app(svc=CaseService(store=Store(tmp / "state")), packets_dir=tmp / "packets", seed_demo=True)
BADGE = re.compile(r'class="mono-mark"[^>]*>O<')

with TestClient(app) as c:
    board = c.get("/").text
    paths = ["/", "/settings", "/outcomes"] + sorted(set(re.findall(r'href="(/cases/[^"/]+)"', board)))
    for actor in ("coordinator", "dentist"):
        c.cookies.set("actor", actor)
        for p in paths:
            r = c.get(p)
            hits = len(BADGE.findall(r.text))
            print(f"{actor:12} {r.status_code} {p:40} badges={hits}")
