"""Print what an internal-app page logs to the browser console (e.g. the case page's Laya + LightGBM dump).

Usage: .venv/bin/python scripts/app-console.py <url>
"""
import sys

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.on("console", lambda m: print(f"[{m.type}] {m.text}"))
    page.on("pageerror", lambda e: print(f"[pageerror] {e}"))
    page.goto(sys.argv[1], wait_until="networkidle")
    b.close()
