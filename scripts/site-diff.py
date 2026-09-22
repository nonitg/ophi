#!/usr/bin/env python3
"""Pixel-compare the Ophi page before and after a change, per viewport.

Usage:
  site-diff.py capture <dir> [query] [widths]   full-page screens at each width (default: desktop and tablet widths)
  site-diff.py compare <before_dir> <after_dir>  report changed pixels per screen and write *-diff.png highlights
"""
import sys
from pathlib import Path

VIEWPORTS = {1440: 900, 1280: 800, 1024: 768, 768: 1024, 701: 900, 430: 932, 393: 852, 360: 800, 320: 640}
DESKTOP = "1440,1280,1024,768,701"


def capture(out: Path, query: str, widths: list[int]) -> None:
    from playwright.sync_api import sync_playwright
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
        for width in widths:
            page = browser.new_page(viewport={"width": width, "height": VIEWPORTS.get(width, 900)}, device_scale_factor=1, reduced_motion="reduce")
            page.goto("http://localhost:3111" + query, wait_until="networkidle")
            page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=30000)
            page.add_style_tag(content="nextjs-portal { display: none !important; }")
            page.wait_for_function("document.fonts.status === 'loaded'")
            page.wait_for_timeout(600)
            page.screenshot(path=str(out / f"{width}.png"), full_page=True)
            print(f"{width}: {out / f'{width}.png'}")
            page.close()
        browser.close()


def compare(before: Path, after: Path) -> None:
    from PIL import Image, ImageChops
    for a_path in sorted(before.glob("[0-9]*.png"), key=lambda p: -int(p.stem)):
        b_path = after / a_path.name
        if not b_path.exists():
            print(f"{a_path.stem}: missing in {after}")
            continue
        a, b = Image.open(a_path).convert("RGB"), Image.open(b_path).convert("RGB")
        if a.size != b.size:
            print(f"{a_path.stem}: SIZE CHANGED {a.size} -> {b.size}")
            continue
        diff = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 8 else 0)
        changed = sum(diff.histogram()[255:])
        box = diff.getbbox()
        print(f"{a_path.stem}: {'identical' if not changed else f'{changed} px changed, region {box}'}")
        if changed:
            highlight = Image.blend(b, Image.new("RGB", b.size, "#ff00ff"), 0.0)
            highlight.paste(Image.new("RGB", b.size, "#ff00ff"), mask=diff)
            highlight.save(after / f"{a_path.stem}-diff.png")


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "capture":
        capture(Path(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else "", [int(w) for w in (sys.argv[4] if len(sys.argv) > 4 else DESKTOP).split(",")])
    else:
        compare(Path(sys.argv[2]), Path(sys.argv[3]))
