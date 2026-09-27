"""Render a two-dentist clinic whose case is an excluded code, and print the case page's words.

Reproduces the ABELDent lab shape from the worklist screenshot (a chart by one dentist while another is
first on the board) without needing the VM.
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from ophi.service import CaseService, Store
from ophi.web.app import create_app

tmp = Path(tempfile.mkdtemp())
cases = tmp / "cases"
cases.mkdir()
shutil.copy("cases/demo/kowalchuk.yaml", cases / "kowalchuk.yaml")  # first on the board, Dr. Priya Lau
src = Path("cases/adversarial/bridge_code_excluded.yaml").read_text()
(cases / "bridge.yaml").write_text(src.replace('name: "Dr. Priya Lau", licence: "ON-48213"',
                                               'name: "Dentist L", licence: null'))

svc = CaseService(store=Store(tmp / "state"), cases_dir=cases)
app = create_app(auto_rules_check=False, svc=svc, packets_dir=tmp / "packets")
client = TestClient(app, follow_redirects=False)
html = client.get(f"/cases/{sys.argv[1] if len(sys.argv) > 1 else 'bridge'}").text
text = re.sub(r"<[^>]+>", " ", html)
print(re.sub(r"[ \t]+", " ", text).replace("\n ", "\n").strip())
