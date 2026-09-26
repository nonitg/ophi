"""Past-decision export directory -> assessed as of each submission date -> outcomes schema."""

from __future__ import annotations

from pathlib import Path

import psycopg

from ophi.engine.assess import assess
from ophi.outcomes import store
from ophi.outcomes.adapter import in_pack, load_export, to_case, to_submission
from ophi.outcomes.denial_map import load_denial_map
from ophi.rules.schema import RulePack


def ingest_dir(conn: psycopg.Connection, roots: list[Path], pack: RulePack) -> dict[str, int]:
    store.save_denial_map(conn, pack, load_denial_map(pack))
    counts = {"submissions": 0, "assessed": 0}
    for f in sorted(f for root in roots for f in root.glob("*.json")):
        d = load_export(f)
        sub = to_submission(d)
        a = assess(to_case(d, sub), pack) if in_pack(sub, pack) else None
        store.save(conn, sub, a)
        counts["submissions"] += 1
        counts["assessed"] += a is not None
    conn.commit()
    return counts
