#!/usr/bin/env python3
"""Rewrite the fictional Look-Back history as ABELDent would hold it: predetermination claims plus chart dumps.

The website reads past denials from the PMS and nothing else. A deployed demo has no lab VM, so the fictional
history is carried in the PMS's own shapes instead of casegen's -- same rows, same code path, no VM. Run this
when cases/lookback/*.yaml changes; the output is committed.
"""
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures" / "abeldent" / "lookback"

FULL_MOUTH = [t for q in (10, 20, 30, 40) for t in range(q + 1, q + 9)]
PA_CODE, BW_CODE = "02111", "02141"
# Charts hold no clinician assertions, so a case's answered criteria are dropped here; retrospectively they
# read as indeterminate either way and never count as a gap (ophi/lookback.py:gaps_of).


def _chart(case: dict, pid: int, dentist: str) -> dict:
    """One patient's chart in lab/tools/chart_dump.py's shape."""
    t, plan_date = case["treatment"], case["tx_plans"][0]["date"]
    missing = case["dentition"]["missing"]
    present = [x for x in FULL_MOUTH if x not in missing]
    trans = iter(range(pid * 100 + 1, pid * 100 + 99))

    planned = [{"trans_id": pid * 100, "plan_num": 1, "code": t["code"], "description": t.get("description"),
                "tooth_fdi": t["tooth"], "surfaces": "", "date": t["planned"], "fee": (t["fee_cents"] or 0) / 100,
                "provider": dentist, "responsible_provider": dentist, "status": "planned",
                "plan": {"date": plan_date, "description": None}}]
    planned += [{"trans_id": next(trans), "plan_num": 1, "code": c, "tooth_fdi": None, "date": plan_date,
                 "provider": dentist, "responsible_provider": dentist, "status": "planned_applied"}
                for c in case["tx_plans"][0].get("completed") or []]

    imaging = []
    for r in case.get("radiographs") or []:
        if r["view"] == "PA":
            imaging.append({"trans_id": next(trans), "code": PA_CODE, "tooth_fdi": r["tooth"], "date": r["date"],
                            "description": "Periapical film"})
    # A bitewing series is one chart row, and the reader takes any 0214x as covering both sides
    # (ophi/sources/chart_case.py:_POSTERIOR). A series that only ever covered one side therefore cannot be
    # written as a chart row without closing a gap that is really open, so it is left off.
    bw = {}
    for r in (case.get("radiographs") or []):
        if r["view"] == "BW":
            bw.setdefault(r["date"], set()).add(r["side"])
    for day, sides in sorted(bw.items()):
        if sides == {"right", "left"}:
            imaging.append({"trans_id": next(trans), "code": BW_CODE, "tooth_fdi": None, "date": day,
                            "description": "Bitewing series"})

    exams = []
    for i, pc in enumerate(case.get("perio_charts") or [], 1):
        depths = [pc.get("depth", 3)] * pc.get("sites", 6) + [None] * (6 - pc.get("sites", 6))
        exams.append({"exam_num": i, "date": pc["date"], "provider": dentist, "date_certified": pc["date"],
                      "pocket": {"teeth_no_value_fdi": missing,
                                 "by_tooth_fdi": {str(x): depths[:6] for x in present}}})
    if not exams:
        # No perio chart on file, but the odontogram still has to say which teeth are there: an exam with no
        # readings carries the missing teeth without standing in for the charting that was never done.
        exams.append({"exam_num": 1, "date": t["planned"], "provider": dentist, "date_certified": None,
                      "pocket": {"teeth_no_value_fdi": missing,
                                 "by_tooth_fdi": {str(x): [None] * 6 for x in FULL_MOUTH}}})

    p = case["patient"]
    given, _, surname = p["name"].partition(" ")
    return {
        "source": "lookback-fixture",
        "patient": {"pid": pid, "surname": surname.upper(), "given": given.upper(), "dob": p["dob"],
                    "gender": p.get("sex", "F"), "dentist": dentist, "inactive": False, "non_patient": False},
        "coverage": {"items": []},
        "planned_procedures": {"items": planned},
        "completed_procedures": {"items": [{"trans_id": next(trans), "code": h["code"], "tooth_fdi": h.get("tooth"),
                                            "surfaces": "", "date": h["date"], "description": None}
                                           for h in case.get("history") or []]},
        "perio_exams": {"items": exams},
        "clinical_notes": {"items": []},
        "imaging": {"procedure_events": imaging},
    }


def _claims(case: dict, pid: int, claim_id: int) -> list[dict]:
    """The predetermination as ABELDent sent it, plus the clinic's later attempt where there was one."""
    t, o = case["treatment"], case["outcome"]
    base = {"patient_id": pid, "code": t["code"], "tooth": t["tooth"], "trans_id": pid * 100,
            "fee_cents": t["fee_cents"], "patient_name": case["patient"]["name"],
            "carrier": "Sun Life Assurance Company of Canada", "status": "P"}

    def answered(decision: str, day: str, text: str | None) -> dict:
        benefit = t["fee_cents"] if decision == "approved" else 0
        reason = f"|G26-1={text}" if text else ""
        return {"answered_on": day, "received": f"A04=23|G05=E|G15-1={benefit}{reason}"}

    rows = [dict(base, claim_id=claim_id, sent_on=o["submitted"],
                 carrier_ref=f"SL{claim_id}{pid}",
                 **answered(o["decision"], o["submitted"], o.get("denial_text")))]
    if o.get("resubmitted"):
        # A second attempt on the same tooth. The engine reads the chain as one recoverable request, not two.
        again = _plus_days(o["submitted"], 45)
        rows.append(dict(base, claim_id=claim_id + 5000, sent_on=again, carrier_ref=f"SL{claim_id + 5000}{pid}",
                         **answered(o["resubmitted_decision"], again, None)))
    return rows


def _plus_days(day: str, n: int) -> str:
    from datetime import date, timedelta
    return (date.fromisoformat(str(day)) + timedelta(days=n)).isoformat()


def main() -> int:
    cases = [yaml.safe_load(f.read_text()) for f in sorted((ROOT / "cases" / "lookback").glob("*.yaml"))]
    dentists = {}
    for c in cases:
        dentists.setdefault(c["provider"]["name"], f"L{len(dentists) + 1}")

    claims, charts = [], {}
    for i, case in enumerate(cases):
        pid, dentist = 9000 + i, dentists[case["provider"]["name"]]
        charts[pid] = _chart(case, pid, dentist)
        claims += _claims(case, pid, 90000 + i)

    (OUT / "charts").mkdir(parents=True, exist_ok=True)
    (OUT / "claims.json").write_text(json.dumps(claims, indent=1, default=str) + "\n")
    (OUT / "providers.json").write_text(json.dumps({v: k for k, v in dentists.items()}, indent=1) + "\n")
    for pid, chart in charts.items():
        (OUT / "charts" / f"{pid}.json").write_text(json.dumps(chart, indent=1, default=str) + "\n")
    print(f"wrote {len(claims)} claims and {len(charts)} charts to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
