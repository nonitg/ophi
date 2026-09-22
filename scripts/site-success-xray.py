#!/usr/bin/env python3
"""Capture the signup success state on the X-ray film (local honeypot submit, nothing stored)."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path("outputs/site-success")
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2, reduced_motion="reduce")
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=30000)
    page.get_by_role("button", name="X-ray").click()
    page.locator("#email").fill("preview@example.com")
    page.locator("#hp_ref").evaluate("el => el.value = 'preview'")
    page.locator("button[type=submit]").click()
    page.wait_for_selector(".waitlist-success")
    page.wait_for_timeout(500)
    page.locator(".entry-row").screenshot(path=str(OUT / "xray-success.png"))
    browser.close()
print(OUT / "xray-success.png")
