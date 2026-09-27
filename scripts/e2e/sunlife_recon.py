"""Recon pass: open each assigned case, dump its visible text, links, forms and overflow."""
from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sunlife_lib import BASE, CASES, DESKTOP, MOBILE, dump, goto, new_context, overflow, page_with_log, shot, text


def main():
    out = {}
    with sync_playwright() as pw:
        browser, ctx = new_context(pw)
        page, errs = page_with_log(ctx)
        for path, name in [("/", "board"), ("/recover", "recover")] + [(f"/cases/{c}", c) for c in CASES]:
            status = goto(page, path)
            body = text(page)
            forms = page.eval_on_selector_all(
                "form", "els => els.map(e => ({action: e.getAttribute('action'), fields: [...e.elements].map(x => x.name || x.value).filter(Boolean)}))")
            links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
            out[name] = {"status": status, "text": body, "forms": forms,
                         "links": sorted(set(links)), "overflow": overflow(page), "console": list(errs)}
            errs.clear()
            shot(page, f"recon-{name}-1440.png")
        page.close()
        ctx.close()
        ctx2 = browser.new_context(viewport=MOBILE)
        ctx2.add_cookies([{"name": "actor", "value": "coordinator", "url": BASE}])
        p2, e2 = page_with_log(ctx2)
        for path, name in [("/", "board"), ("/recover", "recover")] + [(f"/cases/{c}", c) for c in CASES]:
            goto(p2, path)
            out[name]["overflow_390"] = overflow(p2)
            shot(p2, f"recon-{name}-390.png")
        browser.close()
    print(dump("recon.json", out))
    for k, v in out.items():
        print(f"== {k}: {v['status']} overflow1440={v['overflow']} overflow390={v.get('overflow_390')} console={v['console']}")


main()
