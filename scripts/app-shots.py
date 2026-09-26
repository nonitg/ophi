"""Screenshot the internal app's screens for design review.

Usage: .venv/bin/python scripts/app-shots.py <base_url> <out_dir> [path ...]
Default paths: queue, every demo case, one packet, look-back, settings. Desktop 1440 wide and phone 390.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

base, out = sys.argv[1].rstrip("/"), Path(sys.argv[2])
paths = sys.argv[3:] or ["/", "/cases/singh", "/cases/whitfield", "/cases/deng", "/cases/kowalchuk",
                         "/cases/rosco", "/cases/tremblay", "/cases/whitfield/packet", "/look-back", "/settings"]
out.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch()
    for label, vw in (("desk", 1440), ("phone", 390)):
        page = b.new_page(viewport={"width": vw, "height": 900})
        for path in paths:
            page.goto(base + path)
            page.wait_for_load_state("networkidle")
            name = (path.strip("/").replace("/", "_") or "queue") + f"-{label}.png"
            page.screenshot(path=str(out / name), full_page=True)
            print(out / name)
        page.close()
    b.close()
