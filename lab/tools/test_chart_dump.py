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
        # posting a planned crown: P row flips Applied, an Appt=1 posting appears, and a Phase=0/Appt=0
        # companion written at planning time survives -> must be marked duplicate_of the posting
        tx(1410, "P", "27215", 203, 36, PlanNum=1, Applied=1, Date="2024-02-01"),
        tx(1407, " ", "27215", 203, 36, Phase=0, Appt=0, Date="2024-02-01"),
        tx(2407, " ", "27215", 203, 36, Date="2024-02-01"),
        # two genuine same-day scaling units at equal fee: NOT duplicates (both Appt=1)
        tx(310, " ", "11111", 236, 0, Billed=5000, Date="2024-02-01"),
        tx(311, " ", "11111", 236, 0, Billed=5000, Date="2024-02-01"),
    ],
    "tdi": [tdi(99999998, "P", "27211", 16), tdi(500, "", "21221", 36),
            tdi(502, "", "02142", 0, date="2024-03-01", fee=4500),
            tdi(1269, "", "27215", 36, date="2024-02-01"),
            tdi(600, "", "11111", 0, date="2024-02-01", fee=5000)],
    "ixi": [], "sub_ixi": [],
    "perio": [{"patID": 60, "ExamNum": 1, "Date": "2024-01-10", "ProvID": "T", "DateCertified": None,
               "Pocket": FF, "Bleeding_Suppuration": FF, "Recession": FF, "Attachment": FF,
               "Furcation": "FF" * 96, "Mobility": "FF" * 32, "MAG": "FF" * 64}],
    "notes": [
        {"PatID": 60, "Date": "2024-01-10", "KeyType": 1, "KeyNumber": 3, "RefNumber": 0, "NoteType": 1,
         "ToothNumber": 0, "OperatorID": "T", "IsSignedOff": False, "IsViewOnly": True,
         "Note": "{" + chr(92) + "rtf1{" + chr(92) + "fonttbl{" + chr(92) + "f0{" + chr(92) + "*" + chr(92) + "panose 02}Segoe UI;}}"
                 + chr(92) + "f0 fractured MB cusp #16" + chr(92) + "par}",
         "ChartDate": "2024-01-10", "ChartCertified": None, "ChartDesc": None},
        {"PatID": 60, "Date": "2004-06-17", "KeyType": 1, "KeyNumber": 1, "RefNumber": 1, "NoteType": 1,
         "ToothNumber": 14, "OperatorID": "M", "IsSignedOff": None, "IsViewOnly": None, "Note": "plain [MH] note",
         "ChartDate": "2004-06-17", "ChartCertified": None, "ChartDesc": None},
    ],
    "notes_excluded": [{"PatID": 60, "n": 1}],
}
IMG = {"AImage": 0, "AImageVersion": 0, "TDIImageLink": 0, "Imaging": 0, "Document": 0, "AImageToothNumber_orphans": 9}


def test_build_shapes():
    case = build(60, RAW, IMG)

    planned = case["planned_procedures"]["items"]
    assert [p["trans_id"] for p in planned] == [233, 1409, 1410]
    old, new, applied = planned
    assert applied["status"] == "planned_applied" and applied["applied"] == 1
    assert old["tooth_fdi"] == 26 and old["tooth_universal"] == 14 and old["financial_mirror"] is None
    assert old["plan"] == {"date": "2004-07-13", "description": "Crowns", "state": 1} and old["plan_num"] == 1
    assert new["financial_mirror"]["itrid"] == 99999998 and new["fee"] == 581.0 and new["status"] == "planned"
    assert new["financial_mirror_match"] == "code_tooth" and old["financial_mirror_match"] is None
    assert "Transactions" in case["planned_procedures"]["source_assurance"]["detail"]

    done = {c["trans_id"]: c for c in case["completed_procedures"]["items"]}
    assert sorted(done) == [300, 301, 310, 311, 1407, 2407]
    filling = done[301]
    assert filling["surfaces"] == "MO" and filling["chart_num"] == 3 and filling["financial_mirror"]["itrid"] == 500
    assert filling["financial_mirror_match"] == "code_tooth_date"
    assert done[300]["financial_mirror"]["itrid"] == 502 and done[300]["financial_mirror_match"] == "code_tooth_fee_nearest"
    # companion row points at the posting; the posting owns the tdi mirror; the companion is unmatched
    assert done[1407]["duplicate_of"] == 2407 and done[2407]["duplicate_of"] is None
    assert done[2407]["financial_mirror"]["itrid"] == 1269 and done[1407]["financial_mirror_match"] == "unmatched"
    # one tdi row mirrors at most one clinical row: second scaling unit is unmatched, neither is a duplicate
    assert {done[310]["financial_mirror_match"], done[311]["financial_mirror_match"]} == {"code_tooth_date", "unmatched"}
    assert done[310]["duplicate_of"] is None and done[311]["duplicate_of"] is None

    notes = case["clinical_notes"]["items"]
    assert notes[0]["text"] == "fractured MB cusp #16" and notes[0]["text_format"] == "rtf" and notes[0]["view_only"] is True
    assert notes[1]["text"] == "plain [MH] note" and notes[1]["text_format"] == "plain" and notes[1]["tooth_fdi"] == 14
    assert case["clinical_notes"]["excluded_deleted_or_superseded"] == 1

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
