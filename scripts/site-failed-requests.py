#!/usr/bin/env python3
"""List failed or 4xx/5xx requests and page errors on one page load, to trace "network error" findings.

usage: site-failed-requests.py [BASE]
"""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--mute-audio"])
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.on("requestfailed", lambda r: print("failed:", r.url, r.failure))
    page.on("response", lambda r: print(r.status, r.url) if r.status >= 400 else None)
    page.on("pageerror", lambda e: print("pageerror:", e))
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(2000)
    browser.close()
