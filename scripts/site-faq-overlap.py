#!/usr/bin/env python3
"""At tablet widths the copy pill overflows its narrow column into the questions; check the questions stay on top
and keep their clicks, with every answer open.

Usage: site-faq-overlap.py [base_url] [out.png]
"""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = sys.argv[2] if len(sys.argv) > 2 else "outputs/site-faq-overlap-740.png"
HIT = """() => { const pill = document.querySelector('.copy-email-button').getBoundingClientRect();
  const items = document.querySelector('.faq-items').getBoundingClientRect();
  if (pill.right <= items.left) return null;
  // The middle of the overlap: whatever sits on top there takes the click.
  const x = (items.left + pill.right) / 2, y = (pill.top + pill.bottom) / 2;
  const el = document.elementFromPoint(x, y); return el.closest('.faq-items') ? 'questions' : el.closest('.contact') ? 'copy pill' : el.tagName; }"""

failed = False
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 740, "height": 900}, reduced_motion="reduce")
    page.goto(BASE, wait_until="networkidle")
    for width in range(701, 781, 3):
        page.set_viewport_size({"width": width, "height": 900})
        page.evaluate("document.querySelectorAll('.faq-items details').forEach(d => d.open = true)")
        page.locator(".faq").scroll_into_view_if_needed()
        top = page.evaluate(HIT)
        if top not in (None, "questions"):
            failed = True
            print(f"FAIL {width}px: the {top} sits on top of the questions")
    page.set_viewport_size({"width": 740, "height": 900})
    page.locator(".faq").screenshot(path=OUT)
    browser.close()
print("FAIL" if failed else "PASS: questions stay on top of the overflowing copy pill at 701–780px", f"({OUT})")
sys.exit(1 if failed else 0)
