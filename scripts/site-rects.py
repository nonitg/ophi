#!/usr/bin/env python3
"""Print bounding rects for selectors on the local Ophi preview, per viewport."""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:3111"
SELECTORS = sys.argv[1:] or [".footer-bottom", ".copy-email-button", ".footer-wordmark", ".footer-wordmark > span:first-child"]
with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, (w, h) in {"desktop": (1440, 900), "mobile": (390, 844)}.items():
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(BASE, wait_until="networkidle")
        for sel in SELECTORS:
            rects = page.evaluate("s => [...document.querySelectorAll(s)].map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.top + scrollY), Math.round(r.bottom + scrollY), Math.round(r.left), Math.round(r.right), getComputedStyle(e).display]; })", sel)
            print(name, sel, rects)
        page.close()
    browser.close()
