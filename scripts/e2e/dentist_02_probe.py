"""Probe one case page as the dentist, to learn the DOM before driving all seven."""
from __future__ import annotations

import sys

sys.path.insert(0, "/home/arch/Desktop/code/colombus/scripts/e2e")
from dentist_lib import Lane, save  # noqa: E402

cid = sys.argv[1] if len(sys.argv) > 1 else "abeldent_5"
with Lane() as l:
    st = l.go(f"/cases/{cid}")
    out = {
        "status": st,
        "url": l.page.url,
        "text": l.page.inner_text("body"),
        "crit_form": l.page.locator("#crit-form").count(),
        "radios": l.page.locator("#crit-form input[type=radio]").count(),
        "radio_names": l.page.eval_on_selector_all("#crit-form input[type=radio]", "els => [...new Set(els.map(e=>e.name))]"),
        "checked": l.page.eval_on_selector_all("#crit-form input[type=radio]:checked", "els => els.map(e=>e.name+'='+e.value)"),
        "proposals": l.page.eval_on_selector_all("form[action*='/proposals/']", "els => els.map(e=>e.getAttribute('action'))"),
        "console": l.console,
        "pageerrors": l.pageerrors,
    }
    save(f"02_probe_{cid}", out)
    print(out["status"], out["crit_form"], out["radios"], out["radio_names"])
    print("checked:", out["checked"])
    print("proposals:", out["proposals"])
    print(out["text"][:3000])
