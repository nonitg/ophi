#!/usr/bin/env python3
"""Screenshot the rendered welcome note at a desktop mail pane and a phone width."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("outputs/site-email")
with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, width in {"desktop": 760, "phone": 375}.items():
        page = browser.new_page(viewport={"width": width, "height": 900}, device_scale_factor=2)
        page.goto((OUT / "welcome.html").resolve().as_uri(), wait_until="networkidle")
        page.screenshot(path=str(OUT / f"welcome-{name}.png"), full_page=True)
        print(name, page.evaluate("document.documentElement.scrollWidth - innerWidth"), "px overflow")
    browser.close()
