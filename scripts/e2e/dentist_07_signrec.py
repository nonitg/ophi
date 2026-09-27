"""Step 5 detail: the Sign-off record fold — signer, licence, timestamp — on a fresh load."""
from __future__ import annotations

import sys

sys.path.insert(0, "/home/arch/Desktop/code/colombus/scripts/e2e")
from dentist_lib import CASES, Lane, save  # noqa: E402

res = {}
with Lane() as l:
    for cid in CASES:
        l.go(f"/cases/{cid}/packet")
        rec = l.page.locator("details.fold", has=l.page.locator("summary", has_text="Sign-off record"))
        if rec.count():
            rec.first.locator("summary").click()
            res[cid] = rec.first.inner_text()
        else:
            res[cid] = None
        print(cid, "->", repr(res[cid]))
    res["console"] = l.console + l.pageerrors
save("07_signrec", res)
