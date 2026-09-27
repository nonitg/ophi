"""Roles lane: screenshot the role-denied error page at desktop and phone width."""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
OUT = "var/e2e/roles"

with sync_playwright() as p:
    b = p.chromium.launch()
    for w, h, tag in ((1440, 900, "desktop"), (390, 844, "phone")):
        ctx = b.new_context(viewport={"width": w, "height": h})
        ctx.add_cookies([{"name": "actor", "value": "coordinator", "url": BASE}])
        pg = ctx.new_page()
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        # POST the dentist-only form by submitting from the case page context
        pg.goto(f"{BASE}/cases/abeldent_166", wait_until="load", timeout=30000)
        pg.evaluate("""() => {
            const f = document.createElement('form');
            f.method='post'; f.action='/cases/abeldent_166/sign-off';
            const i=document.createElement('input'); i.name='narrative'; i.value='roles lane'; f.appendChild(i);
            document.body.appendChild(f); f.submit();
        }""")
        pg.wait_for_load_state("load", timeout=30000)
        pg.screenshot(path=f"{OUT}/denied-signoff-{tag}.png", full_page=True)
        over = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        body = pg.inner_text("main")
        print(tag, "| overflow px:", over, "| console errors:", errs)
        print(tag, "| copy:", " ".join(body.split())[:200])
        ctx.close()
    b.close()
