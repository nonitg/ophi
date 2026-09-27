"""Step 1: actor switch through the UI, and how the board differs for dentist vs coordinator."""
from __future__ import annotations

import sys

sys.path.insert(0, "/home/arch/Desktop/code/colombus/scripts/e2e")
from dentist_lib import DESKTOP, Lane, save  # noqa: E402

res = {}

# No cookie at all -> default actor.
with Lane(actor="", viewport=DESKTOP) as l:
    st = l.go("/")
    res["default"] = {
        "status": st,
        "me": l.page.locator("form.me").inner_text(),
        "pressed": l.page.locator("form.me button[aria-pressed=true]").inner_text(),
        "headline": l.page.locator("h1").first.inner_text(),
        "cookie": [c["value"] for c in l.ctx.cookies() if c["name"] == "actor"],
    }
    res["coordinator_board"] = l.page.inner_text("body")[:4000]
    res["coord_shot"] = l.shot("board_coordinator_1440")
    res["coord_columns"] = l.page.locator(".col, [class*=column]").count()

    # Switch via the UI control.
    l.page.click("form.me button[value=dentist]")
    l.page.wait_for_load_state("load", timeout=45000)
    res["after_ui_switch"] = {
        "url": l.page.url,
        "pressed": l.page.locator("form.me button[aria-pressed=true]").inner_text(),
        "cookie": [c["value"] for c in l.ctx.cookies() if c["name"] == "actor"],
        "headline": l.page.locator("h1").first.inner_text(),
    }
    res["dentist_board_after_ui"] = l.page.inner_text("body")[:4000]
    res["dentist_shot"] = l.shot("board_dentist_1440")
    res["console"] = l.console
    res["pageerrors"] = l.pageerrors
    res["overflow_1440"] = l.overflow()

# Cookie path (set before first load).
with Lane(actor="dentist", viewport=DESKTOP) as l:
    st = l.go("/")
    res["cookie_path"] = {
        "status": st,
        "pressed": l.page.locator("form.me button[aria-pressed=true]").inner_text(),
        "headline": l.page.locator("h1").first.inner_text(),
    }
    res["overflow_390"] = None

from dentist_lib import PHONE  # noqa: E402

with Lane(actor="dentist", viewport=PHONE) as l:
    l.go("/")
    res["overflow_390"] = l.overflow()
    res["phone_shot"] = l.shot("board_dentist_390")
    res["console_390"] = l.console + l.pageerrors

save("01_board", res)
print(res["default"]["pressed"], "|", res["default"]["headline"])
print(res["after_ui_switch"])
print(res["cookie_path"])
print("overflow1440", res["overflow_1440"]["docScroll"], res["overflow_1440"]["docClient"], res["overflow_1440"]["wide"][:3])
print("overflow390", res["overflow_390"]["docScroll"], res["overflow_390"]["docClient"], res["overflow_390"]["wide"][:3])
print("console", res["console"], res["pageerrors"], res["console_390"])
