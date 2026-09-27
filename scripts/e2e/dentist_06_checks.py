"""Steps 5/6/7: signed-state persistence, re-sign after a changed answer, role guards, phone layout."""
from __future__ import annotations

import sys

sys.path.insert(0, "/home/arch/Desktop/code/colombus/scripts/e2e")
from dentist_lib import BASE, CASES, PHONE, Lane, save  # noqa: E402

res: dict = {}

with Lane() as l:
    # 5. signed state on a fresh load, with the signature fold opened
    cid = "abeldent_9"
    l.go(f"/cases/{cid}/packet")
    folds = l.page.locator("details.fold")
    for i in range(folds.count()):
        folds.nth(i).locator("summary").click()
    body = l.page.inner_text("body")
    res["signed_reload"] = {
        "h1": l.page.locator("h1").first.inner_text(),
        "headline": next((s for s in body.splitlines() if s.startswith("Signed by")), None),
        "detail_block": body[body.find("Signed by"):][:600],
        "shot": l.shot(f"{cid}_signed_folds_open_1440"),
    }

    # 6. what the signed case's audit trail shows on the case page
    l.go(f"/cases/{cid}")
    ab = l.page.inner_text("body")
    res["case_activity"] = ab[ab.find("Activity"):][:600] if "Activity" in ab else ab[-900:]

    # re-sign: change one answer on the test patient, confirm the signature is voided, sign again
    tc = "abeldent_168"
    l.go(f"/cases/{tc}")
    r = l.page.request.post(f"{BASE}/cases/{tc}/assert",
                            form={"criterion_id": "mesiodistal_space", "value": "met", "note": "Re-checked on the film."})
    res["re_assert_status"] = r.status
    l.go(f"/cases/{tc}/packet")
    pb = l.page.inner_text("body")
    res["after_answer_change"] = {"h1": l.page.locator("h1").first.inner_text(),
                                  "stale_note": next((s for s in pb.splitlines() if "no longer applies" in s), None),
                                  "shot": l.shot(f"{tc}_stale_signature_1440")}
    if l.page.locator("#signoff-form button[type=submit]").count():
        l.page.locator("#signoff-form button[type=submit]").click()
        l.page.wait_for_load_state("load", timeout=60000)
        res["re_sign"] = {"h1": l.page.locator("h1").first.inner_text(),
                          "headline": next((s for s in l.page.inner_text("body").splitlines() if s.startswith("Signed by")), None)}

    # bogus proposal id on one of my cases
    pr = l.page.request.post(f"{BASE}/cases/abeldent_5/proposals/does_not_exist", form={"decision": "confirmed"})
    res["bogus_proposal"] = {"status": pr.status, "title": pr.text()[pr.text().find("<title>"):][:60]}
    res["console"] = l.console
    res["pageerrors"] = l.pageerrors

# coordinator guard: can Kim Osei sign?
with Lane(actor="coordinator") as l:
    l.go("/cases/abeldent_5/packet")
    cb = l.page.inner_text("body")
    res["coordinator_packet"] = {"h1": l.page.locator("h1").first.inner_text(),
                                 "has_sign_button": l.page.locator("#signoff-form").count(),
                                 "text": cb[:500]}
    sr = l.page.request.post(f"{BASE}/cases/abeldent_6/sign-off", form={"narrative": "x"})
    res["coordinator_signoff_post"] = {"status": sr.status, "title": sr.text()[sr.text().find("<title>"):][:60]}
    ar = l.page.request.post(f"{BASE}/cases/abeldent_6/assert",
                             form={"criterion_id": "no_furcation", "value": "not_met", "note": "coordinator probe"})
    res["coordinator_assert_post"] = {"status": ar.status, "title": ar.text()[ar.text().find("<title>"):][:80]}
    res["coord_console"] = l.console + l.pageerrors

# 7. phone layout on every assigned case
with Lane(viewport=PHONE) as l:
    res["phone"] = {}
    for cid in CASES:
        l.go(f"/cases/{cid}")
        res["phone"][cid] = {"case_overflow": l.overflow(), "shot": l.shot(f"{cid}_case_390")}
        l.go(f"/cases/{cid}/packet")
        res["phone"][cid]["packet_overflow"] = l.overflow()
        res["phone"][cid]["packet_shot"] = l.shot(f"{cid}_packet_390")
        o1, o2 = res["phone"][cid]["case_overflow"], res["phone"][cid]["packet_overflow"]
        print(cid, "case", o1["docScroll"], o1["wide"][:2], o1["clipped"][:2], "| packet", o2["docScroll"], o2["wide"][:2], o2["clipped"][:2])
    res["phone_console"] = l.console + l.pageerrors

save("06_checks", res)
print("signed_reload:", res["signed_reload"]["headline"])
print("stale:", res["after_answer_change"])
print("re_sign:", res.get("re_sign"))
print("bogus proposal:", res["bogus_proposal"])
print("coord packet sign form count:", res["coordinator_packet"]["has_sign_button"], res["coordinator_signoff_post"], res["coordinator_assert_post"])
print("console:", res["console"], res["pageerrors"], res["coord_console"], res["phone_console"])
