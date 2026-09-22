#!/usr/bin/env python3
"""Render the page's light and paper art on their own, to tune them without the page on top."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "outputs/site-light")
OUT.mkdir(parents=True, exist_ok=True)
ART = {"light-wide": (1440, 900), "light-tall": (390, 844)}

with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, (width, height) in ART.items():
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_content(f'<body style="margin:0;height:100vh;background:#f4f2e9"><div style="height:100%;background:url({BASE}/{name}.svg) 50% 0/cover no-repeat"></div></body>')
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / f"art-{name}.png"))
        print(OUT / f"art-{name}.png")
        page.close()
    page = browser.new_page(viewport={"width": 700, "height": 400}, device_scale_factor=2)
    page.set_content(f'<body style="margin:0;height:100vh;background:#f4f2e9 url({BASE}/paper.svg) 0 0/256px"></body>')
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "art-paper.png"))
    print(OUT / "art-paper.png")
    browser.close()
