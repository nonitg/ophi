#!/usr/bin/env python3
"""On phones, raise both X-ray notes and check each clears the headline, the introduction and the tooth.

"Film's in backwards" comes from turning the tooth away; the ALARA note from five exposures.
Usage: site-xray-note.py [base_url] [out_dir]
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "outputs/site-xray-note")
OUT.mkdir(parents=True, exist_ok=True)
WIDTHS = {320: 640, 345: 700, 360: 800, 361: 800, 375: 667, 393: 852, 414: 896, 430: 932, 479: 900, 480: 900, 600: 900, 700: 900}
# Boxes of the note, each headline line's glyphs, and the introduction, in page coordinates.
MEASURE = """() => {
  const box = r => [r.left, r.top + scrollY, r.right, r.bottom + scrollY];
  const glyphs = el => { const range = document.createRange(); range.selectNodeContents(el); return box(range.getBoundingClientRect()); };
  const em = document.querySelector('.poster-title > em');
  const range = document.createRange(); range.selectNodeContents(em);
  const lines = [...range.getClientRects()].map(box);
  return { note: box(document.querySelector('.xray-note').getBoundingClientRect()), lines,
           care: glyphs(document.querySelector('.poster-title > span')),
           intro: glyphs(document.querySelector('.introduction > p')) };
}"""


def overlap(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) > 0 and max(0, min(a[3], b[3]) - max(a[1], b[1]))


failed = False
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
    for width, height in WIDTHS.items():
        for kind in ("backwards", "alara"):
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2, reduced_motion="reduce")
            page.goto(BASE, wait_until="networkidle")
            page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=30000)
            page.add_style_tag(content="nextjs-portal { display: none !important; }")
            xray = page.get_by_role("button", name="X-ray")
            if kind == "backwards":
                xray.click()
                page.locator(".tooth-canvas").focus()
                for _ in range(10):
                    page.keyboard.press("ArrowRight")
            else:
                for _ in range(9):  # on, off, ... on: five exposures
                    xray.click()
                    page.wait_for_timeout(120)
            page.wait_for_function("document.querySelector('.xray-note').textContent.length > 0")
            page.wait_for_timeout(600)
            m = page.evaluate(MEASURE)
            clashes = [name for name, rect in [("Good care.", m["care"]), ("introduction", m["intro"])] + [(f"headline line {i + 1}", r) for i, r in enumerate(m["lines"])] if overlap(m["note"], rect)]
            n = m["note"]
            status = "PASS" if not clashes else "FAIL"
            failed |= bool(clashes)
            print(f"{status} {width}px {kind:<9} note x{n[0]:.0f}-{n[2]:.0f} y{n[1]:.0f}-{n[3]:.0f}  {'clears text' if not clashes else 'hits ' + ', '.join(clashes)}")
            top = m["care"][1] - 10
            page.screenshot(path=str(OUT / f"{width}-{kind}.png"), full_page=True, clip={"x": 0, "y": top, "width": width, "height": m["intro"][3] - top + 16})
            page.close()
    browser.close()
print(f"Screens in {OUT}. The tooth is WebGL, so check the screens for note-over-tooth by eye.")
sys.exit(1 if failed else 0)
