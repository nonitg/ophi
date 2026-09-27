"""Case abeldent_158 (denied, periapical of #24 missing): resubmission."""
from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sunlife_lib import BASE, dump, goto, new_context, page_with_log, shot, text

CID = "abeldent_158"
out = {}

with sync_playwright() as pw:
    browser, ctx = new_context(pw)
    page, errs = page_with_log(ctx)

    goto(page, f"/cases/{CID}")
    out["before"] = {"text": text(page), "url": page.url}

    # the reason select: what is offered and what is preselected
    out["reason_select"] = page.eval_on_selector(
        "select[name=reason_key]",
        "el => ({value: el.value, selected: el.options[el.selectedIndex].text, n: el.options.length})")

    page.select_option("select[name=reason_key]", "missing_radiograph")
    page.click("form[action$='/resubmit'] button[type=submit]")
    page.wait_for_load_state("load", timeout=60000)
    out["after_resubmit"] = {"url": page.url, "text": text(page), "console": list(errs)}
    errs.clear()
    shot(page, "158-after-resubmit-1440.png")

    # open the Why details so the step reasoning is visible
    page.eval_on_selector_all("details", "els => els.forEach(d => d.open = true)")
    out["why_open_text"] = text(page)
    shot(page, "158-why-open-1440.png")

    browser.close()

print(dump("158.json", out))
print("SELECT:", out["reason_select"])
print("AFTER URL:", out["after_resubmit"]["url"])
