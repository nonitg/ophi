#!/usr/bin/env python3
"""Spot-check chart_dump fixtures: pid 60 (mirror vs no mirror), pid 5 (bridge groups), pid 8 (no tdi planned)."""
import json, os, sys
from pathlib import Path
FX = Path(__file__).resolve().parent.parent / "fixtures" / "abeldent" / "fictional"
files = sorted(FX.glob("*.json"), key=lambda p: int(p.stem))
print("files:", len(files), [p.stem for p in files])

def load(pid): return json.loads((FX / f"{pid}.json").read_text())

c = load(60)
print("\n== pid 60 planned")
for p in c["planned_procedures"]["items"]:
    m = p["financial_mirror"]
    print(f"  T{p['trans_id']} {p['code']} tooth={p['tooth_fdi']} fee={p['fee']} plan={p['plan']} "
          f"mirror={'itrid ' + str(m['itrid']) if m else None}")

c = load(5)
print("\n== pid 5 planned (crowns + bridge by Grp)")
for p in c["planned_procedures"]["items"]:
    print(f"  T{p['trans_id']} {p['code']} {p['description'][:40]:<40} tooth={p['tooth_fdi']} grp={p['bridge_group']} "
          f"chart_code={p['chart_code']} mirror={'yes' if p['financial_mirror'] else None}")

c = load(8)
print("\n== pid 8 planned")
for p in c["planned_procedures"]["items"]:
    print(f"  T{p['trans_id']} {p['code']} tooth={p['tooth_fdi']} plan={p['plan']} mirror={p['financial_mirror']}")
print("  completed sample:", [(x['code'], x['tooth_fdi'], x['financial_mirror'] and x['financial_mirror']['itrid']) for x in c["completed_procedures"]["items"]])
print("  conditions sample:", [(x['chart_code'], x['description'], x['tooth_fdi'], x['surfaces']) for x in c["odontogram_conditions"]["items"][:5]])
print("  xray events:", c["imaging"]["procedure_events"])

print("\n== anomalies across all fixtures")
no_tooth, other, del_raw, unmirrored_done, planned_deleted = [], [], set(), 0, []
for f in files:
    c = json.loads(f.read_text())
    for p in c["planned_procedures"]["items"]:
        if p["tooth_fdi"] is None: no_tooth.append((int(f.stem), p["trans_id"], p["code"]))
        del_raw.add(p["deleted_raw"])
        if p["deleted_raw"]: planned_deleted.append((int(f.stem), p["trans_id"]))
    for o in c["other_ledger_rows"]:
        other.append((int(f.stem), o["type_raw"], o["code"], o["tooth_fdi"]))
    unmirrored_done += sum(1 for x in c["completed_procedures"]["items"] if not x["financial_mirror"])
print("  planned without tooth:", no_tooth)
print("  planned deleted_raw values:", del_raw, "deleted planned:", planned_deleted)
print("  other_ledger_rows (pid, type, code, tooth):", other)
print("  completed rows with no tdi mirror:", unmirrored_done)
