#!/usr/bin/env python3
"""Render the board from the live VM and from the recording; the two pages must read the same."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def board(mode: str) -> str:
    os.environ.pop("USE_ABELDENT_PMS", None)
    os.environ.pop("USE_MOCK_PMS_API", None)
    os.environ[mode] = "true"
    for m in [m for m in sys.modules if m.startswith("ophi")]:
        del sys.modules[m]
    from ophi.service import CaseService
    from ophi.web.app import create_app
    app = create_app(svc=CaseService(), live_ml=False, auto_rules_check=False)
    with TestClient(app) as client:
        r = client.get("/")
        r.raise_for_status()
        return r.text


def main() -> None:
    out = Path("var/board-check")
    out.mkdir(parents=True, exist_ok=True)
    live, rec = board("USE_ABELDENT_PMS"), board("USE_MOCK_PMS_API")
    (out / "live.html").write_text(live)
    (out / "recorded.html").write_text(rec)
    names = lambda h: re.findall(r'class="case-name">([^<]+)<', h)
    print(f"live heading:     {re.search(r'<h1[^>]*>(.*?)</h1>', live, re.S).group(1).strip()}")
    print(f"recorded heading: {re.search(r'<h1[^>]*>(.*?)</h1>', rec, re.S).group(1).strip()}")
    print(f"identical html: {live == rec}")
    if live != rec:
        print(f"live names:     {names(live)}\nrecorded names: {names(rec)}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
