"""abeldent_160 (paper answer): the letter upload, valid and invalid, with timings."""
from __future__ import annotations

import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sunlife_lib import OUT, dump, goto, new_context, page_with_log, shot, text

CID = "abeldent_160"
out = {}


def upload(page, errs, path, tag):
    goto(page, f"/cases/{CID}")
    page.set_input_files("input[name=letter]", str(OUT / path))
    t0 = time.time()
    with page.expect_navigation(wait_until="load", timeout=180000):
        page.click("form[action$='/letter'] button[type=submit]")
    # what the browser shows mid-flight is captured by the navigation timing alone; note it
    secs = round(time.time() - t0, 1)
    body = text(page)
    form = page.eval_on_selector_all(
        "form[action$='/decision'] input, form[action$='/decision'] textarea",
        "els => els.map(e => ({name: e.name, type: e.type, value: e.value, checked: e.checked}))")
    out[tag] = {"seconds": secs, "url": page.url, "text": body, "decision_form": form, "console": list(errs)}
    errs.clear()
    shot(page, f"160-{tag}-1440.png")
    print(f"{tag}: {secs}s  {page.url}")


with sync_playwright() as pw:
    browser, ctx = new_context(pw)
    page, errs = page_with_log(ctx)
    upload(page, errs, "letter.txt", "txt")
    upload(page, errs, "empty.pdf", "empty_pdf")
    upload(page, errs, "not-a-letter.png", "wrong_image")
    upload(page, errs, "sunlife-denial.pdf", "valid_pdf")
    browser.close()

print(dump("160.json", out))
