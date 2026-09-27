"""List every quoted clause in the newest pack and whether its quote appears in the source snapshot it cites.

Usage: PYTHONPATH=. .venv/bin/python scripts/pack-quote-audit.py
Compares with whitespace collapsed, since snapshots are normalized per line.
"""
from ophi.rules.loader import load_pack
from ophi.rules.watch import latest_pack_dir

d = latest_pack_dir()
pack = load_pack(d / "pack.yaml")
flat = {p.stem: " ".join(p.read_text().split()) for p in (d / "sources").glob("*.txt")}
clauses = [(r.id, r.clause) for r in pack.requirements] + [(r.id, r.clause.also) for r in pack.requirements if r.clause.also]
clauses += [(k, c.clause) for k, c in pack.assertion_criteria.items()] + [(r.code, r.clause) for r in pack.schedule.retired_codes]
for owner, c in clauses:
    if c.quote:
        ok = " ".join(c.quote.split()) in flat.get(c.source, "")
        print(f"{'ok     ' if ok else 'MISSING'} {c.source:<9} {owner:<26} {c.quote[:70]!r}")
