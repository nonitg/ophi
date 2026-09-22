#!/usr/bin/env python3
"""Capture Ophi desktop/mobile views and verify the composition does not overflow."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else ".impeccable/review")
OUT.mkdir(parents=True, exist_ok=True)
VIEWPORTS = {"desktop": (1440, 900), "laptop": (1024, 768), "tablet": (768, 1024), "mobile": (390, 844), "small-mobile": (320, 740)}
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
    for name, (width, height) in VIEWPORTS.items():
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1, reduced_motion="reduce")
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_selector('.tooth-viewer[data-ready="true"]')
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Overflow at {width}px"
        page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
        assert not errors, errors
        print(f"{name}: rendered without horizontal overflow or page errors — {OUT / f'{name}.png'}")
        page.close()
    # Blocking only the art file must preserve readable content and the original SVG fallback.
    page = browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    page.route("**/tooth.bin", lambda route: route.abort())
    # Wait for the model request to actually fail; the fallback is also visible before it loads.
    with page.expect_event("requestfailed", lambda request: request.url.endswith("/tooth.bin"), timeout=30000):
        page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(500)
    assert page.locator(".tooth-fallback").is_visible()
    assert page.locator(".tooth-canvas canvas").count() == 0, "A failed model must not leave a canvas behind"
    assert page.locator("#email").is_visible()
    print("Artwork failure: fallback and signup remain available")
    page.close()
    page = browser.new_page(viewport={"width": 390, "height": 844}, java_script_enabled=False)
    page.goto(BASE, wait_until="networkidle")
    assert page.locator(".tooth-fallback").is_visible()
    assert page.locator("#email").is_visible()
    print("Without JavaScript: headline, fallback artwork and signup render")
    browser.close()
