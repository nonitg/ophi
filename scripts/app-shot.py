"""Screenshot one internal-app page quickly while iterating on the design.

Usage: .venv/bin/python scripts/app-shot.py <url> <out.png> [--w=1440] [--h=900] [--full] [--dentist] [--scroll=selector] [--open=selector]
Fails loudly on a non-200 response or on template errors, so a broken page never passes as a picture.
"""
import sys

from playwright.sync_api import sync_playwright

url, out = sys.argv[1], sys.argv[2]
opts = dict(a.lstrip("-").split("=", 1) if "=" in a else (a.lstrip("-"), "1") for a in sys.argv[3:])
w, h = int(opts.get("w", 1440)), int(opts.get("h", 900))

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
    if "dentist" in opts:
        ctx.add_cookies([{"name": "actor", "value": "dentist", "url": url}])
    page = ctx.new_page()
    resp = page.goto(url, wait_until="networkidle")
    if resp is None or resp.status != 200:
        sys.exit(f"{url}: HTTP {resp.status if resp else 'no response'}")
    page.evaluate("document.fonts.ready")
    if "open" in opts:  # <details> panels are shut by default; a screenshot of the copy inside needs them open
        page.eval_on_selector_all(opts["open"], "els => els.forEach(e => e.open = true)")
    if "scroll" in opts:
        page.locator(opts["scroll"]).first.scroll_into_view_if_needed()
    page.screenshot(path=out, full_page="full" in opts)
    overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    print(f"{out} ok{'  HORIZONTAL OVERFLOW ' + str(overflow) + 'px' if overflow > 0 else ''}")
    b.close()
