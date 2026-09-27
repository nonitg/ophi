"""Reproduce the UI defects reported on the dentist lane: skipped-gap counts, stale 'Now' risk,
the unclickable pre-filled criterion, and the provider/actor name clash."""
from __future__ import annotations

import sys

sys.path.insert(0, "/home/arch/Desktop/code/colombus/scripts/e2e")
from dentist_lib import BASE, Lane  # noqa: E402

CASE = sys.argv[1] if len(sys.argv) > 1 else "abeldent_7"
SKIP = "--skip" in sys.argv


def report(l, when: str) -> None:
    print(f"--- {when} ---")
    print("step         :", l.page.locator(".now-head h2").first.inner_text())
    print("header actor :", l.page.locator(".me button[aria-pressed=true]").inner_text().replace("\n", " "))
    dd = l.page.locator("dl dt:text-is('Dentist') + dd")
    print("case dentist :", dd.inner_text() if dd.count() else "?")
    print("risk         :", l.page.locator(".risk-levels").first.inner_text().replace("\n", " ") if l.page.locator(".risk-levels").count() else None)
    print("fold summary :", l.page.locator("#requirements summary").inner_text().replace("\n", " "))
    rows = l.page.eval_on_selector_all("#requirements .req", "els => els.map(e => e.innerText.replace(/\\n/g, ' | ').slice(0, 90))")
    print("rows         :", len(rows))
    for r in rows:
        print("   ", r)


with Lane() as l:
    l.go(f"/cases/{CASE}")
    if SKIP:
        l.page.request.post(f"{BASE}/cases/{CASE}/test-skip")
        l.go(f"/cases/{CASE}")
    report(l, "as loaded")

    # The suggested answer is already checked: clicking it fires no change event, so the row keeps .is-pre.
    if l.page.locator(".crit.is-pre").count():
        # Hold the row itself: a locator would re-resolve to the next dotted row once this one clears.
        row = l.page.locator(".crit.is-pre").first.element_handle()
        inp = row.query_selector("input[type=radio]:checked")
        # Click where a person would: the option centred in the window, clear of the sticky header and footer.
        inp.evaluate("e => e.scrollIntoView({block: 'center'})")
        b = inp.bounding_box()
        l.page.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
        print("click suggested option:", "STILL DOTTED" if "is-pre" in (row.get_attribute("class") or "") else "cleared")
    else:
        print("click suggested option: no pre-filled row on this page")

    if l.page.locator("#crit-form button[type=submit]").count():
        names = l.page.eval_on_selector_all("#crit-form input[type=radio]", "els => [...new Set(els.map(e=>e.name))]")
        for n in names:
            l.page.locator(f"#crit-form input[name='{n}'][value='met']").check(force=True)
        l.page.locator("#crit-form button[type=submit]").click()
        l.page.wait_for_load_state("load", timeout=60000)
        report(l, "after every criterion is answered")
    print("console:", l.console, l.pageerrors)
