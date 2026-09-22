#!/usr/bin/env python3
"""Capture the page light and paper texture as a visitor sees them: viewport shots at the top, middle and end of the page."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "outputs/site-light")
OUT.mkdir(parents=True, exist_ok=True)
VIEWPORTS = {"desktop": (1440, 900, 1), "laptop": (1024, 768, 1), "mobile": (390, 844, 2)}

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    for name, (width, height, scale) in VIEWPORTS.items():
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=scale, reduced_motion="reduce")
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=30000)
        page.add_style_tag(content="nextjs-portal { display: none !important; }")
        end = page.evaluate("document.documentElement.scrollHeight - innerHeight")
        for label, y in {"top": 0, "middle": end // 2, "end": end}.items():
            page.evaluate(f"window.scrollTo(0, {y})")
            page.wait_for_timeout(500)
            path = OUT / f"{name}-{label}.png"
            page.screenshot(path=str(path))
            print(path)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Overflow at {width}px"
        assert not errors, errors
        page.close()
    # Close-up of the paper and headline at print-like density, to judge grain and light edges.
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2, reduced_motion="reduce")
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=30000)
    page.screenshot(path=str(OUT / "closeup.png"), clip={"x": 560, "y": 60, "width": 700, "height": 460})
    print(OUT / "closeup.png")
    browser.close()
