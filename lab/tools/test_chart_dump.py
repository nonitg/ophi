#!/usr/bin/env python3
"""Happy-path test for chart_dump.build over a hand-made raw dict (no VM access)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chart_dump import build  # noqa: E402

FF = "FF" * 192


def tx(trans_id, typ, code, chart_code, tooth, **over):
    row = {"TransID": trans_id, "Date": "2024-01-10", "patID": 60, "ChartNum": 3, "Grp": 0, "ToothNum": tooth,
           "ProvID": "T ", "Code": code, "ChartCode": chart_code, "Descr": "desc", "Billed": 58100,
           "Surfaces": "", "Deleted": 0, "PlanNum": 0, "MatID": None, "Phase": 1, "Type": typ, "Appt": 1,
           "Applied": 0, "RespProvID": "T", "ItemNum": 0, "PlanDate": None, "PlanDescr": None, "PlanState": None}
    row.update(over)
    return row


def tdi(itrid, itype, code, tooth, date="2024-01-10", fee=58100):
    return {"ipid": 60, "itrid": itrid, "idate": date, "ijcode": code, "jdesc1": "desc", "jneedsxrays": "Y",
            "itooth": tooth, "isurf": "", "idid": "T", "iresppvdr": "T", "iefee": fee, "ilabfee": 0, "itype": itype}


RAW = {
    "pat": [{"pid": 60, "plname": "Doe", "pfname": "Jane", "pbirth": "1980-01-01", "pgender": "F", "pdentist": "T",
             "pinactive": 0, "pnonpatient": 0}],
    "tx": [
        tx(233, "P", "27211", 203, 26, PlanNum=1, PlanDate="2004-07-13", PlanDescr="Crowns", PlanState=1, Billed=0),
        tx(1409, "P", "27211", 203, 16, PlanNum=1, PlanDate="2004-07-13", PlanDescr="Crowns", PlanState=1),
        tx(300, " ", "02142", 242, 0, Billed=4500),
        tx(301, " ", "21221", 200, 36, Surfaces="MO", Billed=12000),
        tx(302, " ", None, 116, 36, Surfaces="O", MatID="XX", Billed=0),
        tx(303, "T", "27211", 203, 46),
    ],
    "tdi": [tdi(99999998, "P", "27211", 16), tdi(500, "", "21221", 36),
            tdi(502, "", "02142", 0, date="2024-03-01", fee=4500)],
    "ixi": [], "sub_ixi": [],
    "perio": [{"patID": 60, "ExamNum": 1, "Date": "2024-01-10", "ProvID": "T", "DateCertified": None,
               "Pocket": FF, "Bleeding_Suppuration": FF, "Recession": FF, "Attachment": FF,
               "Furcation": "FF" * 96, "Mobility": "FF" * 32, "MAG": "FF" * 64}],
    "notes": [], "notes_excluded": [],
}
IMG = {"AImage": 0, "AImageVersion": 0, "TDIImageLink": 0, "Imaging": 0, "Document": 0, "AImageToothNumber_orphans": 9}


def test_build_shapes():
    case = build(60, RAW, IMG)

    planned = case["planned_procedures"]["items"]
    assert [p["trans_id"] for p in planned] == [233, 1409]
    old, new = planned
    assert old["tooth_fdi"] == 26 and old["tooth_universal"] == 14 and old["financial_mirror"] is None
    assert old["plan"] == {"date": "2004-07-13", "description": "Crowns", "state": 1} and old["plan_num"] == 1
    assert new["financial_mirror"]["itrid"] == 99999998 and new["fee"] == 581.0 and new["status"] == "planned"
    assert new["financial_mirror_match"] == "code_tooth" and old["financial_mirror_match"] is None
    assert "Transactions" in case["planned_procedures"]["source_assurance"]["detail"]

    done = case["completed_procedures"]["items"]
    assert [c["code"] for c in done] == ["02142", "21221"]
    filling = done[1]
    assert filling["surfaces"] == "MO" and filling["chart_num"] == 3 and filling["financial_mirror"]["itrid"] == 500
    assert filling["financial_mirror_match"] == "code_tooth_date"
    assert done[0]["financial_mirror"]["itrid"] == 502 and done[0]["financial_mirror_match"] == "code_tooth_fee"

    cond = case["odontogram_conditions"]["items"]
    assert len(cond) == 1 and cond[0]["chart_code"] == 116 and cond[0]["material"] == "XX" and cond[0]["tooth_fdi"] == 36

    events = case["imaging"]["procedure_events"]
    assert len(events) == 1 and events[0]["code"] == "02142" and events[0]["tooth_fdi"] is None
    assert case["imaging"]["items"] == [] and case["imaging"]["source_assurance"]["status"] == "indeterminate"
    assert "not locate the image" in case["imaging"]["source_assurance"]["detail"]

    assert [o["status"] for o in case["other_ledger_rows"]] == ["unverified_T"]
    assert case["perio_exams"]["items"][0]["point_count"] == 0


if __name__ == "__main__":
    test_build_shapes()
    print("ok")
