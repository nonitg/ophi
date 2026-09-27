"""Step 2a: answer the clinical criteria on each assigned case (single assert + bulk assert)."""
from __future__ import annotations

import sys

sys.path.insert(0, "/home/arch/Desktop/code/colombus/scripts/e2e")
from dentist_lib import BASE, CASES, Lane, save  # noqa: E402

res: dict = {}
with Lane() as l:
    for cid in CASES:
        r: dict = {"case": cid}
        r["status"] = l.go(f"/cases/{cid}")
        r["h1"] = l.page.locator("h1").first.inner_text()
        r["step_owner"] = l.page.locator(".now-head, .now").first.inner_text()[:200]
        names = l.page.eval_on_selector_all("#crit-form input[type=radio]", "els => [...new Set(els.map(e=>e.name))]")
        checked = l.page.eval_on_selector_all("#crit-form input[type=radio]:checked", "els => els.map(e=>e.name)")
        r["criteria"] = len(names)
        r["unchecked"] = [n for n in names if n not in checked]

        if cid == "abeldent_5" and r["unchecked"]:
            # Exercise the single-criterion endpoint the way the page's own action does.
            crit = r["unchecked"][0].removeprefix("value_")
            resp = l.page.request.post(f"{BASE}/cases/{cid}/assert",
                                       form={"criterion_id": crit, "value": "met", "note": "Judged on the film at the exam."})
            r["single_assert"] = {"criterion": crit, "status": resp.status, "url": resp.url}
            l.go(f"/cases/{cid}")
            names = l.page.eval_on_selector_all("#crit-form input[type=radio]", "els => [...new Set(els.map(e=>e.name))]")
            checked = l.page.eval_on_selector_all("#crit-form input[type=radio]:checked", "els => els.map(e=>e.name)")
            r["unchecked_after_single"] = [n for n in names if n not in checked]

        if l.page.locator("#crit-form").count():
            # Answer every group the dentist has not answered; keep Laya's pre-fills as-is.
            for n in [x for x in names if x not in checked]:
                l.page.locator(f"#crit-form input[name='{n}'][value='met']").check(force=True)
            l.page.locator("#crit-form button[type=submit]").click()
            l.page.wait_for_load_state("load", timeout=60000)
            r["after_bulk_url"] = l.page.url
            r["after_bulk_h1"] = l.page.locator("h1").first.inner_text()
            r["banner"] = l.page.locator(".done, .flash, [class*=done]").first.inner_text()[:200] if l.page.locator(".done, .flash, [class*=done]").count() else None
        vr = l.page.request.get(f"{BASE}/api/cases/{cid}/assessment.json")
        r["verdict"] = vr.json().get("verdict")
        res[cid] = r
        print(cid, r["status"], "crit", r["criteria"], "unchecked", r["unchecked"], "->", r["verdict"])
    res["console"] = l.console
    res["pageerrors"] = l.pageerrors

save("03_criteria", res)
print("console:", res["console"], res["pageerrors"])
