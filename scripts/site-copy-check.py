#!/usr/bin/env python3
"""Check both copy-email buttons copy, reset after 2 s, and capture both dialog headers."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else ".impeccable/review")
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, vp in {"desktop": (1440, 900), "mobile": (390, 844)}.items():
        ctx = browser.new_context(viewport={"width": vp[0], "height": vp[1]}, permissions=["clipboard-read", "clipboard-write"])
        page = ctx.new_page()
        page.goto(BASE, wait_until="networkidle")
        for i, btn in enumerate(page.locator(".copy-email-button").all()):
            page.evaluate("navigator.clipboard.writeText('')")
            btn.scroll_into_view_if_needed()
            box = btn.bounding_box()
            hit = page.evaluate(f"(() => {{ const el = document.elementFromPoint({box['x'] + box['width'] / 2}, {box['y'] + box['height'] / 2}); return el && el.closest('.copy-email-button') ? 'ok' : (el ? el.outerHTML.slice(0, 120) : 'none'); }})()")
            btn.click()
            state = btn.locator(".pill-tag").inner_text()
            clip = page.evaluate("navigator.clipboard.readText()")
            page.wait_for_timeout(2300)
            after = btn.locator(".pill-tag").inner_text()
            print(f"{name} copy#{i}: hit={hit} state={state!r} clipboard={clip!r} after2s={after!r}")
        for kind, label in (("why", "Why Ophi?"), ("privacy", "Your email & privacy")):
            page.get_by_role("button", name=label).click()
            page.wait_for_timeout(350)
            page.locator(f".{kind}-panel").screenshot(path=str(OUT / f"{kind}-{name}.png"))
            page.keyboard.press("Escape")
        ctx.close()
    browser.close()
