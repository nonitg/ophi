"""abeldent_162 (approved): mark booked, then check the board and /recover reflect it."""
from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sunlife_lib import dump, goto, new_context, page_with_log, shot, text

CID = "abeldent_162"
out = {}
with sync_playwright() as pw:
    browser, ctx = new_context(pw)
    page, errs = page_with_log(ctx)
    goto(page, f"/cases/{CID}")
    out["book_form"] = page.eval_on_selector(
        "form[action$='/booked'] input[name=on]",
        "el => ({value: el.value, min: el.min, max: el.max})")
    page.click("form[action$='/booked'] button[type=submit]")
    page.wait_for_load_state("load", timeout=60000)
    out["after_booked"] = {"url": page.url, "text": text(page), "console": list(errs)}
    errs.clear()
    shot(page, "162-after-booked-1440.png")

    goto(page, "/")
    board = text(page)
    out["board"] = board
    out["board_has_randal"] = "Kris Randal" in board
    shot(page, "162-board-1440.png")

    goto(page, "/recover")
    out["recover"] = {"text": text(page), "console": list(errs)}
    browser.close()

print(dump("162.json", out))
print("book form:", out["book_form"])
print("URL:", out["after_booked"]["url"])
