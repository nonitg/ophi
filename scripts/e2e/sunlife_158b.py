"""abeldent_158: resolve Sun Life's ask, then check where the case lands and what the board shows."""
from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sunlife_lib import dump, goto, new_context, overflow, page_with_log, shot, text

CID = "abeldent_158"
out = {}
with sync_playwright() as pw:
    browser, ctx = new_context(pw)
    page, errs = page_with_log(ctx)
    goto(page, f"/cases/{CID}")
    page.click("form[action$='/ask/done'] button[type=submit]")
    page.wait_for_load_state("load", timeout=60000)
    out["after_ask_done"] = {"url": page.url, "text": text(page), "console": list(errs)}
    shot(page, "158-after-ask-done-1440.png")
    out["forms"] = page.eval_on_selector_all("form", "els => els.map(e => e.getAttribute('action'))")
    goto(page, "/")
    out["board"] = {"text": text(page), "overflow": overflow(page)}
    browser.close()
print(dump("158b.json", out))
print(out["after_ask_done"]["url"])
print(out["forms"])
