#!/usr/bin/env python3
"""Check the signup success state fits small phones: no overflow past the band, survey pill inside the column."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("outputs/site-success/small")
OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    for w, h in ((320, 640), (360, 800)):
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2, is_mobile=True, has_touch=True, reduced_motion="reduce")
        pg.goto("http://localhost:3111", wait_until="networkidle")
        pg.locator("#email").fill("preview@example.com"); pg.locator("#hp_ref").evaluate("el => el.value = 'x'")
        pg.locator("button[type=submit]").click(); pg.wait_for_selector(".survey-link")
        r = pg.evaluate("""() => { const box = s => document.querySelector(s).getBoundingClientRect();
            const band = box('.entry-row'), pill = box('.survey-link'), line = box('.success-line');
            return { overflow: document.documentElement.scrollWidth - innerWidth, bandRight: Math.round(band.right - 20),
                     pillRight: Math.round(pill.right), pillH: Math.round(pill.height), lineRight: Math.round(line.right) }; }""")
        print(w, r)
        pg.locator(".entry-row").screenshot(path=str(OUT / f"{w}.png"))
        pg.close()
    b.close()
