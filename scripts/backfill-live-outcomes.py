#!/usr/bin/env python
"""Send decisions already recorded in the case store to the outcomes database.

The sink in ophi/outcomes/from_live.py records a decision as staff enter it, but a decision entered while
Supabase was unreachable, or before the sink existed, never got there. This walks the case store and saves
every decided attempt it finds.

Every attempt of a case is saved, however many there were: each one carries the snapshot frozen when it was
sent (`service.Sent`), so a row labelled with one attempt's decision holds that attempt's chart.

Attempts sent before snapshots were kept have none. Those are reported as skipped rather than filled in from
the chart as it stands today, which would teach the model something untrue.

  uv run python scripts/backfill-live-outcomes.py --dry-run
  uv run python scripts/backfill-live-outcomes.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from ophi import db_store
from ophi.outcomes import store
from ophi.outcomes.from_live import attempt_id, reason_code, save_sent
from ophi.service import CaseService


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="list what would be saved, touch no database")
    args = ap.parse_args()
    load_dotenv()  # SUPABASE_DB_URL

    svc = db_store.service_from_env() or CaseService()
    saved = skipped = 0
    conn = None if args.dry_run else store.connect()
    try:
        for case_id in svc.case_ids():
            st = svc.store.load(case_id)
            # Every attempt the case has made: the earlier ones from st.attempts, then the one in flight.
            made = [(a.submitted_on, a.decision, a.sent) for a in st.attempts]
            if st.decision is not None and st.submitted_on is not None:
                made.append((st.submitted_on, st.decision, st.snapshot))
            for n, (on, decision, sent) in enumerate(made, start=1):
                pid = attempt_id(case_id, n)
                if sent is None:
                    print(f"skip  {pid:24} sent before snapshots were kept")
                    skipped += 1
                    continue
                code = reason_code(decision.outcome, decision.reason_key) or "-"
                if args.dry_run:
                    print(f"would save {pid:24} {decision.outcome:8} {code}")
                else:
                    save_sent(conn, sent, pid, on, decision.outcome, decision.reason_key)
                    print(f"saved {pid:24} {decision.outcome:8} {code}")
                saved += 1
    finally:
        if conn is not None:
            conn.close()
    print(f"\n{saved} attempt(s) {'would be ' if args.dry_run else ''}saved; "
          f"{skipped} skipped (no snapshot: sent before they were kept)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
