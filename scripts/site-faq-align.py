#!/usr/bin/env python3
"""Measure and screenshot the signup card + FAQ edges: answers should start where the form starts, end at the card edge."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://localhost:3111"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/faq-align")
VIEWPORTS = {"1440": (1440, 900), "1024": (1024, 800), "390": (390, 844)}
SELECTORS = {"card": ".entry-row", "intro": ".introduction > p", "form": ".signup", "faq": ".faq", "heading": "#faq-title", "items": ".faq-items"}
RECT = "s => { const r = document.querySelector(s).getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right), Math.round(r.top + scrollY), Math.round(r.bottom + scrollY)]; }"

OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    for vp, (w, h) in VIEWPORTS.items():
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(BASE, wait_until="networkidle")
        rects = {k: page.evaluate(RECT, s) for k, s in SELECTORS.items()}
        print(vp, " ".join(f"{k}={r[0]}-{r[1]}" for k, r in rects.items()))
        top, bottom = rects["card"][2] - 24, rects["faq"][3] + 24
        page.screenshot(path=OUT / f"{vp}.png", full_page=True, clip={"x": 0, "y": top, "width": w, "height": bottom - top})
        page.close()
    browser.close()
