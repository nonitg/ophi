#!/usr/bin/env python3
"""Sample the FAQ answer mid-open and mid-close to confirm it eases rather than snaps."""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
SAMPLE = """() => { const d = document.querySelector('.faq-items details'); const p = d.querySelector('p');
  return { open: d.open, h: Math.round(d.getBoundingClientRect().height), op: +getComputedStyle(p).opacity }; }"""

with sync_playwright() as pw:
    for engine in (pw.chromium, pw.webkit):
        browser = engine.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE, wait_until="networkidle")
        summary = page.locator(".faq-items summary").first
        summary.scroll_into_view_if_needed()
        closed = page.evaluate(SAMPLE)
        summary.click()
        samples = []
        for _ in range(6):
            page.wait_for_timeout(60)
            samples.append(page.evaluate(SAMPLE))
        summary.click()
        page.wait_for_timeout(120)
        mid_close = page.evaluate(SAMPLE)
        page.wait_for_timeout(500)
        print(engine.name, "closed", closed, "\n  opening", samples, "\n  mid-close", mid_close, "\n  end", page.evaluate(SAMPLE))
        browser.close()
