#!/usr/bin/env python3
"""Screenshot the signup band and the FAQ (which holds contact) at four widths; fail on overflow or page errors."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "outputs/entry-row")
OUT.mkdir(parents=True, exist_ok=True)
VIEWPORTS = {"desktop": (1440, 900), "laptop": (1024, 768), "mobile": (390, 844), "small-mobile": (320, 740)}
with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, (width, height) in VIEWPORTS.items():
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1, reduced_motion="reduce")
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE, wait_until="networkidle")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Overflow at {width}px"
        page.locator(".entry-row").screenshot(path=str(OUT / f"{name}.png"))
        page.locator(".faq").screenshot(path=str(OUT / f"{name}-faq.png"))
        assert not errors, errors
        print(f"{name}: {OUT / f'{name}.png'}")
        page.close()
    browser.close()
