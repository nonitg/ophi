"""Quality floor for the internal app: no horizontal scroll at phone width on any screen, visible
keyboard focus, and WCAG AA contrast for every text/background token pair in app.css.

Usage: .venv/bin/python scripts/app-qa.py <base_url>
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

base = sys.argv[1].rstrip("/")
PAGES = ["/", "/cases/kowalchuk", "/cases/singh", "/cases/tremblay", "/cases/rosco", "/cases/deng", "/cases/fontaine",
         "/cases/okafor", "/cases/nguyen", "/cases/marchand", "/cases/whitfield/packet", "/cases/fontaine/packet",
         "/recover", "/results", "/settings", "/model"]


def lum(hex_):
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


css = (Path(__file__).resolve().parents[1] / "ophi/web/static/app.css").read_text()
tok = dict(re.findall(r"--([a-z-]+):\s*(#[0-9a-f]{6})", css))
fails = []
for fg in ("ink", "ink-soft", "muted", "gap", "person", "done", "payer"):
    for bg in ("paper", "stone", "linen"):
        r = ratio(tok[fg], tok[bg])
        if r < 4.5:
            fails.append(f"contrast {fg} on {bg}: {r:.2f}")
for fg, bg in (("gap", "gap-tint"), ("person", "person-tint"), ("done", "done-tint"), ("payer", "payer-tint")):
    r = ratio(tok[fg], tok[bg])
    if r < 4.5:
        fails.append(f"contrast {fg} on {bg}: {r:.2f}")

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 390, "height": 844})
    for path in PAGES:
        page.goto(base + path)
        over = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        if over > 0:
            wide = page.evaluate("""() => [...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1)
                .slice(0, 3).map(e => e.tagName + '.' + e.className)""")
            fails.append(f"overflow {path}: {over}px {wide}")
    page.goto(base + "/")
    page.keyboard.press("Tab")
    outline = page.evaluate("getComputedStyle(document.activeElement).outlineStyle")
    if outline == "none":
        fails.append("first Tab stop has no visible focus outline")
    b.close()

print("\n".join(fails) or "qa ok: no overflow at 390px, focus visible, all token pairs >= 4.5:1")
sys.exit(1 if fails else 0)
