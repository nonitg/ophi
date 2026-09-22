#!/usr/bin/env python3
"""Render X-ray mode in Firefox and WebKit (Safari's engine) to catch engine-specific breakage.

Without WebGL the X-ray button never appears, so the mode is switched on directly in that case.
Usage: site-xray-engines.py [base_url] [out_dir]
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "outputs/site-xray")
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    for engine in (p.firefox, p.webkit):
        browser = engine.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(1500)
        button = page.get_by_role("button", name="X-ray")
        webgl = button.count() > 0
        if webgl:
            button.click()
        else:
            page.evaluate("document.documentElement.setAttribute('data-xray', '')")
        page.wait_for_timeout(700)
        page.screenshot(path=str(OUT / f"{engine.name}-xray.png"))
        vt = page.evaluate("typeof document.startViewTransition === 'function'")
        print(f"{engine.name}: webgl={webgl} view-transitions={vt} errors={errors or 'none'}")
        browser.close()
