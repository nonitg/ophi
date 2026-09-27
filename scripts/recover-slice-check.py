"""Drive the Recover slice end to end against a TestClient: call-back dates, call history, and a denial
that comes back onto the board. No browser; the page is checked by what it says."""

from __future__ import annotations

import re
import sys
from datetime import timedelta

from fastapi.testclient import TestClient

from ophi.service import CaseService, Store
from ophi.web.app import create_app


def text(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def main(tmp: str) -> int:
    from pathlib import Path
    svc = CaseService(store=Store(Path(tmp) / "state"))
    app = create_app(auto_rules_check=False, svc=svc, packets_dir=Path(tmp) / "packets")
    c = TestClient(app, follow_redirects=True)

    rows = svc.recover_rows()
    print(f"{len(rows)} past denials never resubmitted, ${sum(x['row'].fee_dollars for x in rows):,.2f}")
    row_id = rows[0]["row"].case_id
    linked = [x for x in rows if x["case_id"]]
    print(f"already back on the board: {len(linked)}")

    due = (svc.today() - timedelta(days=2)).isoformat()
    r = c.post(f"/recover/{row_id}", data={"status": "left_message", "note": "no answer", "callback_on": due})
    assert r.status_code == 400, f"a past call-back date was accepted: {r.status_code}"
    print("past call-back date refused:", text(r.text)[:80].strip())

    soon = (svc.today() + timedelta(days=3)).isoformat()
    c.post(f"/recover/{row_id}", data={"status": "left_message", "note": "no answer", "callback_on": svc.today().isoformat()})
    c.post(f"/recover/{row_id}", data={"status": "rebooking", "note": "wants to come in", "callback_on": soon})
    page = text(c.get("/recover").text)
    assert "2 calls logged" in page, "the call history is not shown"
    assert "to call back today" not in page, "a future call-back still reads as due"
    print("call history and call-back date render")

    # A denial whose crown the clinic re-planned: same patient, code and tooth as a live board case.
    from tests.test_recover import a_report, a_row  # the same fixture the tests use
    svc.lookback_report = lambda: a_report([a_row(svc)])
    page = text(c.get("/recover").text)
    assert "back on the board" in page, "a re-planned crown did not link to its board case"
    print("re-planned crown links to the board:", [x["case_id"] for x in svc.recovered_rows()])

    res = text(c.get("/results").text)
    assert "back on the board" in res, "the results page does not count what the call list won back"
    print("results page counts what came back")
    return 0


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        sys.exit(main(tmp))
