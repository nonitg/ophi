#!/usr/bin/env python3
"""Capture Ophi at phone widths: first screen and full page, plus the vertical order of key blocks.

Usage: site-mobile.py [base_url] [out_dir] [query]
  query is appended to the URL, e.g. "?m=b" to capture a layout variant.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "outputs/site-mobile")
QUERY = sys.argv[3] if len(sys.argv) > 3 else ""
OUT.mkdir(parents=True, exist_ok=True)
PHONES = {"iphone-15": (393, 852), "android": (360, 800), "iphone-se": (375, 667), "small": (320, 640), "pro-max": (430, 932)}
BLOCKS = [".site-header", ".wordmark", ".view-mode", ".launch-status", ".poster-title > span", ".poster-title > em",
          ".sculpture", ".tooth-canvas", ".entry-row", ".introduction > p", ".why-button", ".signup-head > h2",
          ".email-row", ".pms-field", ".waitlist-consent", ".faq", ".faq-head > h2", ".contact", ".faq-items",
          ".site-footer", ".footer-wordmark", ".footer-bottom"]
tag = QUERY.strip("?").replace("=", "-").replace("&", "_") or "current"

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
    for name, (width, height) in PHONES.items():
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2,
                                is_mobile=True, has_touch=True, reduced_motion="reduce")
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE + QUERY, wait_until="networkidle")
        page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=30000)
        page.wait_for_timeout(600)
        overflow = page.evaluate("document.documentElement.scrollWidth - innerWidth")
        page.screenshot(path=str(OUT / f"{tag}-{name}-fold.png"))
        page.screenshot(path=str(OUT / f"{tag}-{name}-full.png"), full_page=True)
        rows = page.evaluate("""(sels) => sels.map(s => { const el = document.querySelector(s); if (!el) return [s, null];
            const r = el.getBoundingClientRect(); return [s, [Math.round(r.left), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)]]; })""", BLOCKS)
        total = page.evaluate("document.documentElement.scrollHeight")
        print(f"\n{name} {width}x{height}  page height {total}  overflow {overflow}  errors {errors or 'none'}")
        for sel, rect in rows:
            if rect:
                fold = " (below fold)" if rect[1] >= height else ""
                print(f"  {sel:<24} x={rect[0]:<4} y={rect[1]:<5} w={rect[2]:<4} h={rect[3]}{fold}")
            else:
                print(f"  {sel:<24} missing")
        page.close()
    browser.close()
print(f"\nScreens in {OUT}")
