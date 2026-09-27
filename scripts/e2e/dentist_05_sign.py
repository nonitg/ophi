"""Steps 2b/4/5/6: edit the narrative, sign off, build + download the packet, reload the signed case."""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, "/home/arch/Desktop/code/colombus/scripts/e2e")
from dentist_lib import BASE, CASES, OUT, Lane, save  # noqa: E402

res: dict = {}
with Lane() as l:
    for cid in CASES:
        r: dict = {}
        r["packet_status"] = l.go(f"/cases/{cid}/packet")
        r["h1"] = l.page.locator("h1").first.inner_text()
        r["provider_block"] = l.page.inner_text("body")[:60]
        body = l.page.inner_text("body")
        r["sign_as"] = next((s for s in body.splitlines() if s.startswith("Sign as")), None)
        r["verifier_fail"] = "packet check failed" in body.lower()
        r["verifier_text"] = body[body.lower().find("packet check failed"):][:300] if r["verifier_fail"] else None

        # Edit and save the narrative through the UI (append a grounded sentence).
        if l.page.locator("#narrative").count():
            txt = l.page.locator("#narrative").input_value()
            edit = txt.rstrip() + "\n\nReviewed by the treating dentist before signing."
            l.page.locator("#narrative-fold > summary").click()
            l.page.locator("#narrative").fill(edit)
            l.page.locator("#narrative-form button[type=submit]").click()
            l.page.wait_for_load_state("load", timeout=60000)
            r["narrative_saved"] = l.page.locator("h1").first.inner_text()
            r["narrative_banner"] = next((s for s in l.page.inner_text("body").splitlines() if "saved" in s.lower()), None)

        # Sign off.
        l.go(f"/cases/{cid}/packet")
        if l.page.locator("#signoff-form button[type=submit]").count():
            l.page.locator("#signoff-form button[type=submit]").click()
            l.page.wait_for_load_state("load", timeout=60000)
        r["after_sign_h1"] = l.page.locator("h1").first.inner_text()
        sbody = l.page.inner_text("body")
        r["signed_headline"] = next((s for s in sbody.splitlines() if s.startswith("Signed by")), None)
        r["signed_by_dd"] = l.page.locator("dt:text('Signed by') + dd").inner_text() if l.page.locator("dt:text('Signed by')").count() else None
        r["when_dd"] = l.page.locator("dt:text('When') + dd").inner_text() if l.page.locator("dt:text('When')").count() else None
        r["shot_packet"] = l.shot(f"{cid}_packet_signed_1440")

        # preview.pdf
        pr = l.page.request.get(f"{BASE}/cases/{cid}/packet/preview.pdf")
        pdf = pr.body()
        r["preview"] = {"status": pr.status, "ctype": pr.headers.get("content-type"), "bytes": len(pdf),
                        "magic": pdf[:5].decode("latin1")}
        (OUT / f"{cid}_preview.pdf").write_bytes(pdf)

        # download
        dl = l.page.request.get(f"{BASE}/cases/{cid}/packet/download")
        r["download"] = {"status": dl.status, "ctype": dl.headers.get("content-type"),
                         "disposition": dl.headers.get("content-disposition"), "bytes": len(dl.body())}
        if dl.status == 200 and "zip" in (dl.headers.get("content-type") or ""):
            z = zipfile.ZipFile(io.BytesIO(dl.body()))
            r["download"]["names"] = z.namelist()
            r["download"]["bad"] = z.testzip()
            (OUT / f"{cid}_packet.zip").write_bytes(dl.body())
            r["download"]["index"] = z.read("00_index.txt").decode("utf-8", "replace")[:1500]
        else:
            r["download"]["body"] = dl.text()[:600]

        # reload the signed case page: does the signed state persist?
        l.go(f"/cases/{cid}")
        cb = l.page.inner_text("body")
        r["case_after_sign"] = next((s for s in cb.splitlines() if "Signed" in s or "signed" in s), None)
        r["case_h1"] = l.page.locator("h1").first.inner_text()
        r["shot_case"] = l.shot(f"{cid}_case_signed_1440")
        r["overflow_1440"] = l.overflow()
        res[cid] = r
        print(cid, r["after_sign_h1"], "|", r["signed_headline"], "| pdf", r["preview"]["bytes"], "| zip", r["download"]["status"], r["download"]["bytes"])
    res["console"] = l.console
    res["pageerrors"] = l.pageerrors

save("05_sign", res)
print("console:", res["console"][:10], res["pageerrors"][:5])
