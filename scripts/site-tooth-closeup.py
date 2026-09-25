#!/usr/bin/env python3
"""Close-up renders of the tooth sculpture on this Mac's GPU, to judge surface quality (faceting, noise artefacts).

Usage: site-tooth-closeup.py <out dir> [base] [query ...]
Each query (e.g. "" or "?t=nobump") gives <out>/<n>-full.png (sculpture at 1440@3x) and <n>-zoom.png (2x crop of the crown/root).
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
BASE = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:3201"
QUERIES = sys.argv[3:] or [""]

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--use-angle=metal", "--enable-gpu", "--ignore-gpu-blocklist"])
    for n, query in enumerate(QUERIES):
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=3, reduced_motion="reduce")
        page.goto(BASE + "/" + query, wait_until="networkidle")
        page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=30000)
        page.wait_for_timeout(600)
        box = page.locator(".tooth-canvas").bounding_box()
        page.screenshot(path=str(OUT / f"{n}-full.png"), clip=box)
        # The crown's side and the root fork, where the surface reads most clearly.
        zoom = {"x": box["x"] + box["width"] * .3, "y": box["y"] + box["height"] * .2, "width": box["width"] * .35, "height": box["height"] * .35}
        page.screenshot(path=str(OUT / f"{n}-zoom.png"), clip=zoom)
        print(f"{n} {query or '(default)'}: {OUT / f'{n}-zoom.png'}")
        page.close()
