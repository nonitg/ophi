"""Step 3: what the narrative validator does with non-ASCII text, an empty box, and a forbidden claim."""
from __future__ import annotations

import sys

sys.path.insert(0, "/home/arch/Desktop/code/colombus/scripts/e2e")
from dentist_lib import BASE, Lane, save  # noqa: E402

CID = "abeldent_168"  # Claude Zztest, the seeded test patient
res: dict = {}

with Lane() as l:
    l.go(f"/cases/{CID}/packet")
    original = l.page.locator("#narrative").input_value()
    res["original_len"] = len(original)
    res["original_head"] = original[:300]
    res["has_non_ascii_already"] = [c for c in set(original) if ord(c) > 127]

    def attempt(label: str, text: str) -> dict:
        l.go(f"/cases/{CID}/packet")
        l.page.locator("#narrative-fold > summary").click()
        l.page.locator("#narrative").fill(text)
        l.page.locator("#narrative-form button[type=submit]").click()
        l.page.wait_for_load_state("load", timeout=60000)
        body = l.page.inner_text("body")
        out = {"url": l.page.url, "h1": l.page.locator("h1").first.inner_text(),
               "visible": body[:900]}
        # what the box holds after the round trip
        l.go(f"/cases/{CID}/packet")
        out["stored"] = l.page.locator("#narrative").input_value() if l.page.locator("#narrative").count() else None
        out["stored_len"] = len(out["stored"] or "")
        out["stored_non_ascii"] = sorted({c for c in (out["stored"] or "") if ord(c) > 127})
        res[label] = out
        print(label, "->", out["h1"], "| stored", out["stored_len"], "non-ascii", out["stored_non_ascii"])
        return out

    attempt("non_ascii", "Crown narrative — café über naïve 40 % ± 3 °C — résumé of the tooth.\nSecond line.")
    attempt("empty", "")
    attempt("forbidden", "This crown is medically necessary and the treatment is covered.")
    attempt("bad_tooth", "Crown planned on #48 with a bad date 1999-01-01.")
    # Put a clean, grounded narrative back so the case can be signed.
    final = attempt("restore", original)
    res["restored_matches_original"] = final["stored"] == original

    res["console"] = l.console
    res["pageerrors"] = l.pageerrors

save("04_narrative", res)
print("console:", res["console"], res["pageerrors"])
