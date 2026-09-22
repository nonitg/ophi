#!/usr/bin/env python3
"""Crop one region of a phone variant at 2x, from one selector's top to another's bottom.

Usage: site-mobile-crop.py variant width from_selector to_selector out.png [xray]
  variant "-" means the current page without ?m=
"""
import sys
from playwright.sync_api import sync_playwright

VARIANT, WIDTH, FROM, TO, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
XRAY = len(sys.argv) > 6 and sys.argv[6] == "xray"
BASE = "http://localhost:3111" + ("" if VARIANT == "-" else f"?m={VARIANT}")

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
    page = browser.new_page(viewport={"width": WIDTH, "height": 800}, device_scale_factor=2, is_mobile=True, has_touch=True, reduced_motion="reduce")
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=30000)
    page.add_style_tag(content="nextjs-portal { display: none !important; }")
    if XRAY:
        page.click(".view-mode")
        page.wait_for_selector(":root[data-xray]")
    page.wait_for_timeout(500)
    top = page.evaluate("s => document.querySelector(s).getBoundingClientRect().top + scrollY", FROM)
    bottom = page.evaluate("s => document.querySelector(s).getBoundingClientRect().bottom + scrollY", TO)
    page.screenshot(path=OUT, full_page=True, clip={"x": 0, "y": max(0, top - 16), "width": WIDTH, "height": bottom - top + 32})
    print(OUT)
    browser.close()
