#!/usr/bin/env python3
"""M0 artifact: dump a Fictional Data patient's preauth-relevant chart as structured JSON.

One command, zero manual steps. For every patient with a planned procedure (or the pids
given), pull patient, coverage, planned + completed procedures, odontogram conditions,
perio exams (decoded to per-site millimetres and a point count), clinical notes, and
imaging — each section stamped with a source_assurance so "no perio chart recorded" and
"this driver cannot see perio charts" never collapse into the same answer.

ABELDent keeps two ledgers. `Transactions` is the clinical chart ledger the Treatment view
reads (planned items, charted procedures, odontogram conditions); `tdi` is the financial
ledger. Planned work is authoritative in `Transactions`: older fictional plans exist only
there, and items entered through the modern Treatment view are mirrored into `tdi` with a
sentinel itrid. Every procedure here is read from `Transactions` and carries its `tdi`
mirror when one exists.

Read-only. Runs the plan's canonical SELECTs through `vm sql`, so the same rails the lab
tooling enforces (no writes, no procs) apply here. Nothing here is per-patient chatter:
nine set-based queries per run, whatever the patient count.

Usage:
    lab/tools/chart_dump.py                       # all patients with planned work
    lab/tools/chart_dump.py --pids 5 6 33         # specific patients
    lab/tools/chart_dump.py --out fixtures/abeldent/fictional
"""
import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from perio_decode import UNIVERSAL_TO_FDI, decode, summarise  # noqa: E402

VM = HERE.parent / "vm" / "vm"
FDI_TO_UNIVERSAL = {fdi: i + 1 for i, fdi in enumerate(UNIVERSAL_TO_FDI)}

# Transactions.Type: ' ' charted/completed, 'P' planned. 'I' and 'T' are observed but
# unresolved; they are surfaced under other_ledger_rows and no rule may depend on them.
TX_TYPE = {"": "completed", "P": "planned", "T": "unverified_T", "I": "unverified_I"}
# tdi.itype uses the same letters; T rows carry sentinel itrid 99999999, P rows 99999998.
ITYPE = {"": "completed", "P": "planned", "T": "planned_unverified_T", "I": "unverified_I"}
RADIOGRAPH_CHART_CODE = 242

PERIO_COLS = {"Pocket": "pocket", "Bleeding_Suppuration": "bleeding", "Recession": "recession",
              "Attachment": "attachment", "Furcation": "furcation", "Mobility": "mobility",
              "MAG": "mag"}
PERIO_LEN = {"pocket": 192, "bleeding": 192, "recession": 192, "attachment": 192,
             "furcation": 96, "mobility": 32, "mag": 64}

LEDGER_NOTE = (
    "Transactions is the clinical chart ledger (what the Treatment view shows); tdi is the "
    "financial ledger. Planned items entered through the modern Treatment view are mirrored "
    "into tdi (itype 'P', sentinel itrid 99999998); older fictional plans exist only in "
    "Transactions, so financial_mirror is null for them.")
# Verified on pids 5/153/155/157: Grp restarts at 1 for every bridge, so it is a unit position, not an id.
GRP_NOTE = ("bridge_group is Transactions.Grp: 0/null for single units; for bridge units it is the 1..n "
            "position within the bridge (retainer, pontic, ...). Consecutive rows with ascending Grp "
            "starting at 1 form one bridge; Grp is not a shared bridge id.")


def sql(query):
    """Run one SELECT against the ABELDent database and return rows as dicts."""
    r = subprocess.run([str(VM), "sql", query, "", "json"], capture_output=True, text=True)
    body = r.stdout.strip()
    if not body:
        raise RuntimeError(f"empty response from vm sql (stderr: {r.stderr.strip()[:200]})")
    if body.startswith("REFUSED") or "Exception" in body[:200]:
        raise RuntimeError(body[:400])
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise RuntimeError(f"non-JSON from vm sql: {body[:300]}")
    if isinstance(data, dict):  # older q.ps1 shapes: {value,Count} wrapper or a bare single row
        data = data["value"] if "value" in data and "Count" in data else [data]
    return data


def d(col, alias=None):
    """ISO-date projection; sidesteps PowerShell's /Date(ms)/ JSON encoding."""
    return f"CONVERT(varchar(10), {col}, 23) AS {alias or col}"


def hexcol(col, n):
    return f"CONVERT(varchar({n * 2 + 2}), CAST({col} AS varbinary({n})), 2) AS {col}"


def in_list(pids):
    return ",".join(str(int(p)) for p in pids)


def assurance(status, detail):
    """Lab vocabulary -> CDM SourceAssurance (docs/plan/01-ingestion.md): present=Present,
    none_recorded=AbsentConfirmed, indeterminate=Unknown. No Degraded case arises in the lab yet.
    Provenance (query id, extractedAt) is added by the agent's mapper, not here."""
    return {"status": status, "detail": detail}


def fdi_or_none(t):
    return int(t) if t and int(t) > 0 else None


def s(v):
    """Trimmed string or None; ABELDent pads char columns with spaces."""
    return (v or "").strip() or None


def planned_pids():
    rows = sql("SELECT DISTINCT patID FROM Transactions WHERE Type='P' AND Deleted=0")
    return sorted(r["patID"] for r in rows)


def fetch(pids):
    P = in_list(pids)
    out = {}
    out["pat"] = sql(
        f"SELECT pid, plname, pfname, {d('pbirth')}, pgender, pdentist, pinactive, pnonpatient, "
        f"{d('plastckp')}, pstatus FROM pat WHERE pid IN ({P})")
    out["tx"] = sql(
        f"SELECT x.TransID, {d('x.Date', 'Date')}, x.patID, x.ChartNum, x.Grp, x.ToothNum, x.ProvID, "
        f"x.Code, x.ChartCode, x.Descr, x.Billed, x.Surfaces, x.Deleted, x.PlanNum, x.MatID, x.Phase, "
        f"x.Type, x.Appt, x.Applied, x.RespProvID, x.ItemNum, "
        f"{d('p.Date', 'PlanDate')}, p.Descr AS PlanDescr, p.State AS PlanState "
        f"FROM Transactions x LEFT JOIN Plans p ON p.PatID = x.patID AND p.PlanNum = x.PlanNum AND x.PlanNum > 0 "
        f"WHERE x.patID IN ({P}) ORDER BY x.patID, x.Date, x.TransID")
    out["tdi"] = sql(
        f"SELECT t.ipid, t.itrid, {d('t.idate', 'idate')}, t.ijcode, j.jdesc1, j.jneedsxrays, "
        f"t.itooth, t.isurf, t.idid, t.iresppvdr, t.iefee, t.ilabfee, t.itype "
        f"FROM tdi t LEFT JOIN jcf j ON j.jcode = t.ijcode WHERE t.ipid IN ({P}) "
        f"ORDER BY t.ipid, t.idate, t.itrid")
    out["ixi"], out["sub_ixi"] = fetch_coverage(P)
    hexes = ", ".join(hexcol(c, PERIO_LEN[a]) for c, a in PERIO_COLS.items())
    out["perio"] = sql(
        f"SELECT patID, ExamNum, {d('Date')}, ProvID, {d('DateCertified')}, {hexes} "
        f"FROM Perio WHERE patID IN ({P}) ORDER BY patID, ExamNum")
    out["notes"] = sql(
        f"SELECT n.PatID, {d('n.Date', 'Date')}, n.KeyType, n.KeyNumber, n.RefNumber, n.NoteType, "
        f"n.ToothNumber, n.OperatorID, n.IsSignedOff, n.IsViewOnly, n.Note, "
        f"{d('c.Date', 'ChartDate')}, {d('c.DateCertified', 'ChartCertified')}, c.ChartDesc "
        f"FROM Notes n LEFT JOIN Charts c ON c.patID = n.PatID AND c.ChartNum = n.KeyNumber AND n.KeyType = 1 "
        f"WHERE n.PatID IN ({P}) AND n.IsDeleted = 0 AND n.IsLatest = 1 ORDER BY n.PatID, n.Date")
    out["notes_excluded"] = sql(
        f"SELECT PatID, COUNT(*) n FROM Notes WHERE PatID IN ({P}) AND (IsDeleted = 1 OR IsLatest = 0) GROUP BY PatID")
    out["img"] = sql(
        "SELECT 'AImage' t, COUNT(*) n FROM AImage UNION ALL "
        "SELECT 'AImageVersion', COUNT(*) FROM AImageVersion UNION ALL "
        "SELECT 'TDIImageLink', COUNT(*) FROM TDIImageLink UNION ALL "
        "SELECT 'Imaging', COUNT(*) FROM Imaging UNION ALL "
        "SELECT 'Document', COUNT(*) FROM Document UNION ALL "
        "SELECT 'AImageToothNumber_orphans', COUNT(*) FROM AImageToothNumber a "
        "WHERE NOT EXISTS (SELECT 1 FROM AImage i WHERE i.ImageID = a.ImageID)")
    return out


def fetch_coverage(P):
    """ixi rows for the patients plus the active ixi rows of any subscriber they inherit from."""
    ixi = sql(
        f"SELECT x.ixipid, x.ixiplno, x.ixiplanid, n.nplanname, n.ninscoid, i.insname, "
        f"i.insSupportsMultipagePreds, x.ixicertno, x.ixigroupno, x.ixisubpid, x.ixireltosub, "
        f"x.ixiIsActive, {d('x.ixiExpiryDate', 'ixiExpiryDate')} "
        f"FROM ixi x LEFT JOIN nsp n ON n.nid = x.ixiplanid LEFT JOIN ins i ON i.inscoid = n.ninscoid "
        f"WHERE x.ixipid IN ({P}) ORDER BY x.ixipid, x.ixiplno")
    # Dependants carry a blank plan id and point at the subscriber; the plan lives on the
    # subscriber's own ixi row. Resolve it so a rule can see the carrier without a second hop.
    subs = sorted({r["ixisubpid"] for r in ixi if r["ixisubpid"] and not (r["ixiplanid"] or "").strip()})
    sub_ixi = sql(
        f"SELECT x.ixipid, x.ixiplno, x.ixiplanid, n.nplanname, n.ninscoid, i.insname, "
        f"i.insSupportsMultipagePreds, x.ixicertno, x.ixigroupno, x.ixisubpid, x.ixireltosub, x.ixiIsActive "
        f"FROM ixi x LEFT JOIN nsp n ON n.nid = x.ixiplanid LEFT JOIN ins i ON i.inscoid = n.ninscoid "
        f"WHERE x.ixipid IN ({in_list(subs)}) AND x.ixiIsActive = 1 ORDER BY x.ixipid, x.ixiplno") if subs else []
    return ixi, sub_ixi


def by_pid(rows, key):
    g = defaultdict(list)
    for r in rows:
        g[r[key]].append(r)
    return g


def decode_exam(row):
    exam = {"exam_num": row["ExamNum"], "date": row["Date"], "provider": (row["ProvID"] or "").strip(),
            "date_certified": row["DateCertified"]}
    for col, alias in PERIO_COLS.items():
        n = PERIO_LEN[alias]
        per_tooth = decode(row[col], n // 32)
        s = summarise(per_tooth)
        exam[alias] = {
            "point_count": s["point_count"],
            "sites_total": s["sites_total"],
            "teeth_no_value_fdi": s["teeth_no_value_fdi"],
            "value_min": s["value_min"],
            "value_max": s["value_max"],
            "by_tooth_fdi": {str(UNIVERSAL_TO_FDI[u - 1]): sites for u, sites in per_tooth.items()},
        }
        if alias == "pocket":
            exam[alias]["sites_5mm_plus"] = s["sites_5mm_plus"]
    pc = exam["pocket"]["point_count"]
    exam["point_count"] = pc
    exam["extent"] = "full_mouth" if pc >= 150 else "partial" if pc >= 24 else "spot_check"
    return exam


def tx_type(r):
    return (r["Type"] or "").strip()


def is_condition(r):
    """Odontogram condition: a charted row with no procedure code (ChartCode 100-160)."""
    return tx_type(r) == "" and not s(r["Code"])


def is_completed(r):
    return tx_type(r) == "" and bool(s(r["Code"])) and r["Deleted"] == 0


def build(pid, raw, img_counts):
    pat = next((p for p in raw["pat"] if p["pid"] == pid), None)
    if not pat:
        return None
    tx = [r for r in raw["tx"] if r["patID"] == pid]
    tdi = [r for r in raw["tdi"] if r["ipid"] == pid]
    return {
        "source": {"pms": "ABELDent", "version": "15.1.0 Freemium", "dataset": "Fictional Data (CA)",
                   "notation": {"Transactions.ToothNum": "FDI", "tdi.itooth": "FDI", "Notes.ToothNumber": "FDI",
                                "Perio arrays": "Universal 1-32, converted to FDI here"}},
        "patient": patient_section(pid, pat),
        "coverage": coverage_section(pid, raw),
        **ledger_sections(tx, tdi),
        "perio_exams": perio_section(pid, raw),
        "clinical_notes": notes_section(pid, raw),
        "imaging": imaging_section(tx, img_counts),
    }


def patient_section(pid, pat):
    return {
        "pid": pid, "surname": pat["plname"], "given": pat["pfname"], "dob": pat["pbirth"],
        "gender": (pat["pgender"] or "").strip(), "dentist": (pat["pdentist"] or "").strip(),
        "inactive": pat["pinactive"], "non_patient": pat["pnonpatient"],
        "source_assurance": assurance("present", "pat row"),
    }


def coverage_section(pid, raw):
    items = [cov_row(r, raw["sub_ixi"]) for r in raw["ixi"] if r["ixipid"] == pid]
    return {
        "items": items,
        "source_assurance": assurance(
            "present" if items else "none_recorded",
            "ixi joined to nsp (plan) and ins (carrier). Family members carry a blank plan id and point at the subscriber via ixisubpid."),
    }


def mark_same_day_duplicates(completed):
    """Posting a planned item from the Treatment view leaves two Type=' ' rows for one procedure:
    the appointment posting (Appt=1) and a chart companion (Appt=0, Phase=0) written at planning
    time. Same code, tooth, date and fee. Keep the Appt=1 row primary; point the other at it."""
    primary = {}
    for it in completed:
        it["duplicate_of"] = None
        if it["appt"]:
            primary.setdefault((it["code"], it["tooth_fdi"], it["date"], it["fee"]), it["trans_id"])
    for it in completed:
        if not it["appt"] and not it["phase"]:
            it["duplicate_of"] = primary.get((it["code"], it["tooth_fdi"], it["date"], it["fee"]))
    return completed


def ledger_sections(tx, tdi):
    used = set()  # one tdi row mirrors at most one clinical row
    planned = [planned_item(r, tdi, used) for r in tx if tx_type(r) == "P"]
    # Appointment postings (Appt=1) claim their tdi mirror before planning-time companions can.
    done_rows = sorted((r for r in tx if is_completed(r)), key=lambda r: 0 if r["Appt"] else 1)
    completed = [completed_item(r, tdi, used) for r in done_rows]
    completed.sort(key=lambda it: (it["date"], it["trans_id"]))
    completed = mark_same_day_duplicates(completed)
    conditions = [condition_item(r) for r in tx if is_condition(r)]
    other = [other_item(r) for r in tx if tx_type(r) not in ("", "P")]
    return {
        "planned_procedures": {
            "items": planned,
            "source_assurance": assurance(
                "present" if planned else "none_recorded",
                "Transactions WHERE Type='P' (all Deleted values, see deleted_raw), joined to Plans on PlanNum. "
                "status planned_applied = Applied=1: the item has been posted as completed and a Type=' ' row exists for it. "
                + LEDGER_NOTE + " " + GRP_NOTE),
        },
        "completed_procedures": {
            "items": completed,
            "source_assurance": assurance(
                "present" if completed else "none_recorded",
                "Transactions WHERE Type=' ' AND Code<>'' AND Deleted=0. financial_mirror is the tdi row "
                "(itype='') with the same code and tooth, matched on posting date first and equal fee second "
                "(financial_mirror_match: code_tooth_date, code_tooth_fee_nearest within 400 days, or unmatched); each tdi row mirrors at most one clinical row. duplicate_of points a same-day "
                "chart companion row (Appt=0, Phase=0) at its appointment posting; count only rows with duplicate_of null. " + GRP_NOTE),
        },
        "odontogram_conditions": {
            "items": conditions,
            "source_assurance": assurance(
                "present" if conditions else "none_recorded",
                "Transactions WHERE Type=' ' AND Code is empty: odontogram markings by ChartCode "
                "(116 Decay, 102 Crown, 114 Bridge, 106 Implant, 100/104/108/140 Existing Condition, ...). "
                "Not procedures and never billed."),
        },
        "other_ledger_rows": other,
    }


def perio_section(pid, raw):
    perio = [decode_exam(r) for r in raw["perio"] if r["patID"] == pid]
    return {
        "items": perio,
        "source_assurance": assurance("present" if perio else "none_recorded",
                                      "Perio table, positional byte arrays decoded per site. DateCertified blank in all Fictional Data rows."),
    }


def notes_section(pid, raw):
    notes = [note_row(r) for r in raw["notes"] if r["PatID"] == pid]
    excluded = next((r["n"] for r in raw["notes_excluded"] if r["PatID"] == pid), 0)
    return {
        "items": notes,
        "excluded_deleted_or_superseded": excluded,
        "source_assurance": assurance("present" if notes else "none_recorded",
                                      "Notes WHERE IsDeleted=0 AND IsLatest=1, joined to Charts on KeyNumber=ChartNum. Edits and 'make view only' create a new row and mark the old one IsDeleted=1/IsLatest=0, so the filter keeps current versions only. Modern notes are RTF and are converted to text here (text_format)."),
    }


def imaging_section(tx, img_counts):
    events = [radiograph_event(r) for r in tx
              if r["ChartCode"] == RADIOGRAPH_CHART_CODE and tx_type(r) == "" and r["Deleted"] == 0]
    detail = (
        "items: imaging tables are readable but hold zero rows database-wide "
        f"({', '.join(f'{k}={v}' for k, v in img_counts.items() if k != 'AImageToothNumber_orphans')}). "
        f"{img_counts.get('AImageToothNumber_orphans', 0)} AImageToothNumber rows reference images that "
        "no longer exist, so Fictional Data once had images and ships without them. Cannot distinguish "
        "'none recorded' from 'not visible to this driver'; treat as indeterminate until the imaging spike "
        "resolves it. Manual upload is the only radiograph source for now. "
        "procedure_events: charted Transactions rows (Type=' ', Deleted=0) with ChartCode 242 (radiograph "
        "procedure codes 02102-02601). "
        "An event proves a radiograph was taken and charted/billed on that date; it does not locate the "
        "image. The evidence matcher must not treat a procedure event as a retrievable artifact."
    )
    return {
        "items": [],
        "procedure_events": events,
        "source_assurance": assurance("indeterminate", detail),
    }


def tx_row(r):
    """Fields common to every Transactions-sourced item."""
    fdi = fdi_or_none(r["ToothNum"])
    return {
        "trans_id": r["TransID"], "date": r["Date"], "code": s(r["Code"]),
        "description": s(r["Descr"]) or "", "chart_code": r["ChartCode"],
        "tooth_fdi": fdi, "tooth_universal": FDI_TO_UNIVERSAL.get(fdi) if fdi else None,
        "surfaces": s(r["Surfaces"]),
        "provider": s(r["ProvID"]) or "", "responsible_provider": s(r["RespProvID"]) or "",
        "fee": (r["Billed"] or 0) / 100, "phase": r["Phase"], "item_num": r["ItemNum"],
        "bridge_group": r["Grp"] or None, "deleted_raw": r["Deleted"],
        "appt": r["Appt"], "applied": r["Applied"],
    }


def planned_item(r, tdi, used=None):
    plan = None
    if r["PlanNum"]:
        plan = {"date": r["PlanDate"], "description": s(r["PlanDescr"]), "state": r["PlanState"]}
    mirror, how = financial_mirror(r, tdi, planned=True, used=used)
    # Applied flips to 1 when the planned item is posted as done; the P row itself stays.
    status = "planned_applied" if r["Applied"] else "planned"
    return {**tx_row(r), "plan_num": r["PlanNum"], "plan": plan, "status": status,
            "financial_mirror": mirror, "financial_mirror_match": how}


def completed_item(r, tdi, used=None):
    mirror, how = financial_mirror(r, tdi, planned=False, used=used)
    return {**tx_row(r), "chart_num": r["ChartNum"], "status": "completed",
            "financial_mirror": mirror, "financial_mirror_match": how}


def condition_item(r):
    return {"trans_id": r["TransID"], "date": r["Date"], "chart_code": r["ChartCode"],
            "description": s(r["Descr"]) or "", "tooth_fdi": fdi_or_none(r["ToothNum"]),
            "surfaces": s(r["Surfaces"]), "material": s(r["MatID"]), "chart_num": r["ChartNum"],
            "deleted_raw": r["Deleted"]}


def radiograph_event(r):
    return {"trans_id": r["TransID"], "date": r["Date"], "code": s(r["Code"]),
            "description": s(r["Descr"]) or "", "tooth_fdi": fdi_or_none(r["ToothNum"]),
            "provider": s(r["ProvID"]) or "", "chart_num": r["ChartNum"]}


def other_item(r):
    t = tx_type(r)
    return {**tx_row(r), "plan_num": r["PlanNum"], "status": TX_TYPE.get(t, f"unknown_{t}"), "type_raw": t}


MIRROR_WINDOW_DAYS = 400  # Fictional Data charts up to ~5 months before tdi posts; be generous, not infinite


def days_between(a, b):
    from datetime import date
    return abs((date.fromisoformat(a) - date.fromisoformat(b)).days)


def financial_mirror(r, tdi, planned, used=None):
    """The tdi row mirroring a Transactions row, plus how it was matched.

    Same code and tooth always, and each tdi row mirrors at most one clinical row (`used`).
    Planned rows match tdi itype P/T. Completed rows take the same posting date, else the nearest
    posting within MIRROR_WINDOW_DAYS with the same fee (Fictional Data charts months before it
    posts: pid 8 charted 2003-06-27, posted 2003-11-21), else 'unmatched'."""
    used = used if used is not None else set()
    code, fdi = s(r["Code"]), fdi_or_none(r["ToothNum"])
    cands = [t for t in tdi if s(t["ijcode"]) == code and fdi_or_none(t["itooth"]) == fdi
             and (t["itrid"], t["idate"], t["ijcode"], t["itooth"]) not in used]
    if planned:
        hit = next((t for t in cands if t["itype"].strip() in ("P", "T")), None)
        return _take(hit, used, "code_tooth")
    posted = [t for t in cands if t["itype"].strip() == ""]
    hit = next((t for t in posted if t["idate"] == r["Date"]), None)
    if hit:
        return _take(hit, used, "code_tooth_date")
    same_fee = [t for t in posted if (t["iefee"] or 0) == (r["Billed"] or 0)
                and days_between(t["idate"], r["Date"]) <= MIRROR_WINDOW_DAYS]
    hit = min(same_fee, key=lambda t: days_between(t["idate"], r["Date"]), default=None)
    return _take(hit, used, "code_tooth_fee_nearest") if hit else (None, "unmatched")


def _take(hit, used, how):
    if not hit:
        return None, None
    used.add((hit["itrid"], hit["idate"], hit["ijcode"], hit["itooth"]))
    return proc_row(hit), how


def proc_row(r):
    """A tdi (financial ledger) row."""
    fdi = fdi_or_none(r["itooth"])
    return {
        "itrid": r["itrid"], "date": r["idate"], "code": r["ijcode"].strip(),
        "description": (r["jdesc1"] or "").strip(), "needs_xrays_flag": (r["jneedsxrays"] or "").strip() or None,
        "tooth_fdi": fdi, "tooth_universal": FDI_TO_UNIVERSAL.get(fdi) if fdi else None,
        "surfaces": (r["isurf"] or "").strip() or None,
        "provider": (r["idid"] or "").strip(), "responsible_provider": (r["iresppvdr"] or "").strip(),
        "fee": (r["iefee"] or 0) / 100, "lab_fee": (r["ilabfee"] or 0) / 100,
        "status": ITYPE.get(r["itype"].strip(), f"unknown_{r['itype']}"), "itype_raw": r["itype"].strip(),
    }


def cov_row(r, sub_rows=()):
    inherited = None
    if not (r["ixiplanid"] or "").strip() and r["ixisubpid"]:
        inherited = next((s for s in sub_rows if s["ixipid"] == r["ixisubpid"]), None)
    if inherited:
        return {**cov_row(inherited), "slot": (r["ixiplno"] or "").strip(),
                "subscriber_pid": r["ixisubpid"], "relation_to_subscriber": (r["ixireltosub"] or "").strip(),
                "active": r["ixiIsActive"], "expiry": r.get("ixiExpiryDate"), "inherited_from_subscriber": True}
    return {
        "slot": (r["ixiplno"] or "").strip(), "plan_id": (r["ixiplanid"] or "").strip() or None,
        "plan_name": (r["nplanname"] or "").strip() or None, "carrier_id": (r["ninscoid"] or "").strip() or None,
        "carrier_name": (r["insname"] or "").strip() or None,
        "carrier_supports_multipage_preds": r["insSupportsMultipagePreds"],
        "certificate": (r["ixicertno"] or "").strip() or None, "group": (r["ixigroupno"] or "").strip() or None,
        "subscriber_pid": r["ixisubpid"] or None, "relation_to_subscriber": (r["ixireltosub"] or "").strip(),
        "active": r["ixiIsActive"], "expiry": r.get("ixiExpiryDate"), "inherited_from_subscriber": False,
    }


# Notes written through the modern Clinical Note Builder are stored as RTF (with an embedded
# theme blob); Fictional Data notes are plain text. A rule must never quote RTF control words.
RTF_GROUP_SKIP = {"fonttbl", "colortbl", "stylesheet", "listtable", "listoverridetable", "info",
                  "themedata", "colorschememapping", "pict", "object", "header", "footer"}
RTF_WORD = re.compile(r"\\([a-z]+)(-?\d+)? ?|\\'([0-9a-f]{2})|\\(.)", re.S)
RTF_SPACE = {"par": "\n", "line": "\n", "tab": "\t", "~": " ", "emdash": "\u2014", "endash": "\u2013",
             "lquote": "\u2018", "rquote": "\u2019", "ldblquote": "\u201c", "rdblquote": "\u201d", "bullet": "\u2022"}


def rtf_group_is_skipped(rtf, i):
    """Called at an opening brace: destination groups ({\\*...}) and the known tables are noise."""
    if rtf.startswith("{\\*", i):
        return True
    m = re.match(r"\{\\([a-z]+)", rtf[i:i + 24])
    return bool(m and m.group(1) in RTF_GROUP_SKIP)


def rtf_to_text(rtf):
    out, i, depth, skipped, pending_uc = [], 0, 0, [], 0
    while i < len(rtf):
        ch = rtf[i]
        if ch == "{":
            depth += 1
            if rtf_group_is_skipped(rtf, i):
                skipped.append(depth)
            i += 1
        elif ch == "}":
            if skipped and skipped[-1] == depth:
                skipped.pop()
            depth -= 1
            i += 1
        elif ch == "\\":
            m = RTF_WORD.match(rtf, i)
            if not m:
                i += 1
                continue
            word, num, hexch, lit = m.groups()
            if not skipped:
                if pending_uc and (hexch or lit == "'"):
                    pending_uc -= 1  # the fallback char after \uN belongs to the unicode escape
                elif word == "u" and num:
                    out.append(chr(int(num) % 65536)); pending_uc = 1
                elif word in RTF_SPACE:
                    out.append(RTF_SPACE[word])
                elif hexch:
                    out.append(bytes.fromhex(hexch).decode("cp1252", "replace"))
                elif lit in RTF_SPACE:
                    out.append(RTF_SPACE[lit])
                elif lit in ("\\", "{", "}"):
                    out.append(lit)
            i = m.end()
        else:
            if not skipped and ch not in "\r\n":
                if pending_uc:
                    pending_uc -= 1
                else:
                    out.append(ch)
            i += 1
    return "".join(out).strip()


def note_text(raw):
    if raw and raw.lstrip().startswith("{\\rtf"):
        return rtf_to_text(raw), "rtf"
    return raw, "plain"


def note_row(r):
    text, fmt = note_text(r["Note"])
    return {
        "date": r["Date"], "chart_num": r["KeyNumber"] if r["KeyType"] == 1 else None,
        "chart_date": r["ChartDate"], "chart_certified": r["ChartCertified"],
        "key_type": r["KeyType"], "note_type": r["NoteType"], "ref_number": r["RefNumber"],
        "tooth_fdi": fdi_or_none(r["ToothNumber"]), "operator": (r["OperatorID"] or "").strip(),
        "signed_off": r["IsSignedOff"], "view_only": r.get("IsViewOnly"),
        "text": text, "text_format": fmt,
    }


HEADER = (f"{'pid':>4} {'patient':<18} {'planned':>7} {'crowns':>6} {'done':>5} {'cond':>4} {'xray':>4} "
          f"{'perio':>5} {'pts(last)':>9} {'notes':>5} {'cov':>3}  imaging")


def summary_line(pid, case):
    pl = case["planned_procedures"]["items"]
    pe = case["perio_exams"]["items"]
    return (f"{pid:>4} {case['patient']['surname'] + ', ' + case['patient']['given']:<18.18} "
            f"{len(pl):>7} {sum((p['code'] or '').startswith('27') for p in pl):>6} "
            f"{len(case['completed_procedures']['items']):>5} {len(case['odontogram_conditions']['items']):>4} "
            f"{len(case['imaging']['procedure_events']):>4} {len(pe):>5} "
            f"{(pe[-1]['point_count'] if pe else '-'):>9} {len(case['clinical_notes']['items']):>5} "
            f"{len(case['coverage']['items']):>3}  {case['imaging']['source_assurance']['status']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pids", nargs="*", type=int, help="patient ids; default = all with planned work")
    ap.add_argument("--out", default=str(HERE.parent.parent / "fixtures" / "abeldent" / "fictional"))
    args = ap.parse_args()

    pids = args.pids or planned_pids()
    raw = fetch(pids)
    img_counts = {r["t"]: r["n"] for r in raw["img"]}
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    print(HEADER)
    for pid in pids:
        case = build(pid, raw, img_counts)
        if not case:
            print(f"{pid:>4} (no pat row)")
            continue
        (outdir / f"{pid}.json").write_text(json.dumps(case, indent=2, default=str) + "\n")
        print(summary_line(pid, case))
    print(f"\n{len(pids)} patients -> {outdir}")


if __name__ == "__main__":
    main()
