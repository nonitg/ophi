"""Every 'Why' line the case page can show, across the demo and adversarial cases.

Used to design the plain-language rewrite: one line per (action_type, clause?) with the exact
sentence staff read today.
"""
from pathlib import Path
import tempfile

from ophi import demo
from ophi.service import CaseService, Store
from ophi.web import present

svc = CaseService(store=Store(Path(tempfile.mkdtemp()) / "s"), cases_dir=Path(__import__("os").environ.get("CASES","cases/demo")))
demo.seed(svc)
seen = set()
for cid in svc.case_ids():
    v = svc.view(cid)
    rows = present.fix_panel(v, None, v.pack, present.gap_rows(v))["rows"]
    for r in rows:
        act = r["gap"]["action"] if r["gap"] else None
        key = (act.action_type if act else "?", r["title"])
        if key in seen:
            continue
        seen.add(key)
        print(f"[{key[0]}] rid={r['rid']} clause={(r['clause'].ref if r['clause'] else None)}")
        print(f"   title: {r['title']}")
        print(f"   why:   {r['why']}\n")
