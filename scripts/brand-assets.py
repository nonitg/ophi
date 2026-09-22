#!/usr/bin/env python3
"""Render Ophi logo PNGs, social avatars and banners into assets/.

Logos and avatars come from assets/logo/*.svg (run brand-wordmark.py first) and site/app/icon.svg.
Banners are the live poster (type + tooth) reframed per platform, so the dev server must be up:
  cd site && pnpm dev --port 3111
  .venv/bin/python scripts/brand-assets.py [base_url]
"""
import re
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
IVORY = "#f4f2e9"

# Upload sizes per platform; each platform crops or masks the edges itself.
AVATAR_SIZES = {1080: "Instagram, Facebook, TikTok", 400: "X, LinkedIn, Google"}

# Only the poster, reframed. The profile photo covers each platform's bottom-left corner, so type
# stays clear of it; Facebook's phone crop keeps only the middle ~1110px, hence the narrow shell.
POSTER_ONLY = """
  #main > :not(.poster), .site-footer, .site-header, nextjs-portal { display: none !important; }
  .site-shell { margin-inline: auto; min-height: 100vh; }
"""
BANNERS = {
    "x-header-1500x500": (1500, 500, """
      .site-shell { width: 1380px; padding-top: 26px; }
      .poster { height: 440px; } .poster-title { font-size: 150px; }
    """),
    "facebook-cover-1640x624": (1640, 624, """
      .site-shell { width: 1060px; padding-top: 44px; }
      .poster { height: 520px; } .poster-title { font-size: 128px; }
    """),
    # Too thin for the stacked poster: one line with the tooth between the phrases.
    "linkedin-cover-1128x191": (1128, 191, """
      .site-shell { width: 100%; }
      .poster { height: 191px; }
      .poster-title { position: static; flex-direction: row; justify-content: center; align-items: center;
        gap: 190px; height: 100%; font-size: 76px; padding-left: 60px; }
      .poster-title > span, .poster-title > em { padding: 0; align-self: center; }
      .sculpture { width: 230px; height: 250px; top: -22px; left: calc(50% + 6px - 115px); right: auto; }
    """),
}


def page_html(body: str, background: str = "transparent") -> str:
    return f'<html><body style="margin:0;background:{background}">{body}</body></html>'


def svg_box(svg: str, width: int, height: int) -> str:
    """Stretch an SVG's own viewBox to width × height."""
    return svg.replace("<svg ", f'<svg width="{width}" height="{height}" style="display:block" ', 1)


def aspect(svg: str) -> float:
    """Height over width of an SVG's viewBox."""
    _, _, w, h = map(float, re.search(r'viewBox="([^"]+)"', svg).group(1).split())
    return h / w


def shoot(page, html: str, width: int, height: int, out: Path) -> None:
    page.set_viewport_size({"width": width, "height": height})
    page.set_content(html)
    out.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out), omit_background=True)
    print(out.relative_to(ROOT))


def avatar_mark(icon: str) -> str:
    """The favicon mark, full-bleed and shrunk so a circular crop keeps clear space."""
    bleed = re.sub(r' rx="[^"]*"', "", icon)
    head, rest = bleed.split("/>", 1)
    return f'{head}/><g transform="translate(32 32) scale(.8) translate(-33 -33)">{rest.replace("</svg>", "")}</g></svg>'


def logos(page) -> None:
    logo = ASSETS / "logo"
    shutil.copy(ROOT / "site/app/icon.svg", logo / "ophi-mark.svg")
    icon = (logo / "ophi-mark.svg").read_text()
    shoot(page, page_html(svg_box(icon, 1024, 1024)), 1024, 1024, logo / "ophi-mark-1024.png")
    for name in ("ophi-wordmark", "ophi-wordmark-ivory"):
        svg = (logo / f"{name}.svg").read_text()
        height = round(2400 * aspect(svg))
        shoot(page, page_html(svg_box(svg, 2400, height)), 2400, height, logo / f"{name}.png")


def avatars(page) -> None:
    mark = avatar_mark((ROOT / "site/app/icon.svg").read_text())
    word = (ASSETS / "logo/ophi-wordmark.svg").read_text()
    for size in AVATAR_SIZES:
        shoot(page, page_html(svg_box(mark, size, size)), size, size, ASSETS / f"profile/ophi-avatar-mark-{size}.png")
        width = round(size * .64)
        centred = f'<div style="display:grid;place-items:center;height:{size}px">{svg_box(word, width, round(width * aspect(word)))}</div>'
        shoot(page, page_html(centred, IVORY), size, size, ASSETS / f"profile/ophi-avatar-wordmark-{size}.png")


def banners(browser) -> None:
    for name, (width, height, css) in BANNERS.items():
        page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion="reduce")
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_selector('.tooth-viewer[data-ready="true"]')
        page.add_style_tag(content=POSTER_ONLY + css)
        page.wait_for_timeout(1500)
        out = ASSETS / f"banner/ophi-{name}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out))
        print(out.relative_to(ROOT))
        page.close()


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
        page = browser.new_page()
        logos(page)
        avatars(page)
        page.close()
        banners(browser)
        browser.close()


if __name__ == "__main__":
    main()
