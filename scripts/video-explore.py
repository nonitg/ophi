"""Print the visible text of app pages, to find the strings and states the pitch video should capture.

Usage: .venv/bin/python scripts/video-explore.py <base_url> <path> [<path> ...]   (a path may end in "#open" to open every <details>)
"""
import sys

from playwright.sync_api import sync_playwright

base = sys.argv[1].rstrip("/")
with sync_playwright() as p:
    page = p.chromium.launch().new_page(viewport={"width": 1440, "height": 900})
    for path in sys.argv[2:]:
        opened = path.endswith("#open")
        page.goto(base + path.removesuffix("#open"))
        page.wait_for_load_state("networkidle")
        if opened:
            page.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
        print(f"\n===== {path}  ({page.evaluate('document.documentElement.scrollHeight')}px)")
        print(page.locator("main, body").first.inner_text()[:6000])
