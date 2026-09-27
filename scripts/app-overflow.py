"""List the elements that stick out past the viewport on internal-app pages (phone-width layout checks).

Usage: .venv/bin/python scripts/app-overflow.py <base_url> [--w=390] [path ...]
Prints the deepest offending elements per page; exits 1 if any page scrolls sideways.
"""
import sys

from playwright.sync_api import sync_playwright

base = sys.argv[1].rstrip("/")
w = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--w=")), 390)
paths = [a for a in sys.argv[2:] if not a.startswith("--")] or [
    "/", "/cases/singh", "/cases/rosco", "/cases/tremblay", "/cases/whitfield", "/cases/whitfield/packet", "/look-back", "/settings", "/model"]

FIND = """(w) => {
  const out = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.right > w + 1 && r.width > 0 && !el.closest('.tbl-wrap, .chip-pop')) {
      if (![...el.children].some(c => c.getBoundingClientRect().right > w + 1))
        out.push(`${el.tagName.toLowerCase()}.${[...el.classList].join('.')} right=${Math.round(r.right)} "${(el.textContent||'').trim().slice(0, 50)}"`);
    }
  }
  return out.slice(0, 8);
}"""

bad = False
with sync_playwright() as p:
    b = p.chromium.launch()
    for cookie in (None, "dentist"):
        ctx = b.new_context(viewport={"width": w, "height": 844})
        if cookie:
            ctx.add_cookies([{"name": "actor", "value": cookie, "url": base}])
        page = ctx.new_page()
        for path in paths:
            page.goto(base + path, wait_until="networkidle")
            over = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            if over > 0:
                bad = True
                print(f"{path} [{cookie or 'coordinator'}] overflows by {over}px")
                for line in page.evaluate(FIND, w):
                    print("   ", line)
        ctx.close()
    b.close()
print("sideways scroll found" if bad else f"no sideways scroll at {w}px")
sys.exit(1 if bad else 0)
