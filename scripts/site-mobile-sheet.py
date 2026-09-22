#!/usr/bin/env python3
"""Full-page phone captures of the page under each query string (such as layout variants behind a temporary
switch), joined side by side into one contact sheet per width.

Usage: site-mobile-sheet.py [base_url] [out_dir] [queries] [widths] [xray]
  queries:  comma list such as "-,?m=a,?m=b"; "-" is the page as it is  (default "-")
  widths:   comma list of phone widths                              (default "393,360")
  xray:     "xray" to capture with the page switched to X-ray mode
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "outputs/site-mobile")
VARIANTS = (sys.argv[3] if len(sys.argv) > 3 else "-").split(",")
WIDTHS = [int(w) for w in (sys.argv[4] if len(sys.argv) > 4 else "393,360").split(",")]
XRAY = len(sys.argv) > 5 and sys.argv[5] == "xray"
HEIGHTS = {320: 640, 360: 800, 375: 667, 393: 852, 430: 932}
OUT.mkdir(parents=True, exist_ok=True)
suffix = "-xray" if XRAY else ""

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
    for width in WIDTHS:
        shots = []
        for variant in VARIANTS:
            page = browser.new_page(viewport={"width": width, "height": HEIGHTS.get(width, 800)}, device_scale_factor=1,
                                    is_mobile=True, has_touch=True, reduced_motion="reduce")
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(BASE + ("" if variant == "-" else variant), wait_until="networkidle")
            page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=30000)
            page.add_style_tag(content="nextjs-portal { display: none !important; }")
            if XRAY:
                page.click(".view-mode")
                page.wait_for_selector(":root[data-xray]")
            page.wait_for_timeout(500)
            overflow = page.evaluate("document.documentElement.scrollWidth - innerWidth")
            path = OUT / f"{'current' if variant == '-' else variant.strip('?').replace('=', '-').replace('&', '_')}-{width}{suffix}.png"
            page.screenshot(path=str(path), full_page=True)
            shots.append((variant, path))
            print(f"{width} {variant}: height {page.evaluate('document.documentElement.scrollHeight')} overflow {overflow} errors {errors or 'none'}")
            page.close()
        images = [(v, Image.open(p)) for v, p in shots]
        gap, label = 24, 34
        sheet = Image.new("RGB", (sum(im.width for _, im in images) + gap * (len(images) + 1), max(im.height for _, im in images) + label + gap), "#ffffff")
        draw = ImageDraw.Draw(sheet)
        x = gap
        for variant, im in images:
            draw.text((x, 10), "current" if variant == "-" else variant, fill="#193a30", font_size=20)
            sheet.paste(im, (x, label))
            x += im.width + gap
        sheet_path = OUT / f"sheet-{width}{suffix}.png"
        sheet.save(sheet_path)
        print(f"sheet: {sheet_path}")
    browser.close()
