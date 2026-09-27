#!/usr/bin/env python3
"""Merge only the patient contact fields from a fresh chart dump into the committed fixtures.

A wholesale re-dump also picks up months of unrelated VM drift. The fixtures are a record of chart parsing;
this adds the one new field without rewriting the rest.
"""
import json, sys
from pathlib import Path

FX = Path(__file__).resolve().parent.parent / "fixtures" / "abeldent" / "fictional"
fresh_dir = Path(sys.argv[1])
changed = 0
for f in sorted(FX.glob("*.json")):
    fresh = fresh_dir / f.name
    if not fresh.exists():
        continue
    doc, src = json.loads(f.read_text()), json.loads(fresh.read_text())["patient"]
    pat = doc["patient"]
    if (pat.get("phone"), pat.get("email")) == (src.get("phone"), src.get("email")):
        continue
    # Same key order patient_section writes: contact before source_assurance.
    doc["patient"] = {**{k: v for k, v in pat.items() if k != "source_assurance"},
                      "phone": src.get("phone"), "email": src.get("email"),
                      "source_assurance": pat["source_assurance"]}
    f.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    changed += 1
print(f"{changed} fixtures gained contact")
