#!/usr/bin/env python3
"""Record everything the live ABELDent answers, so the demo can run the same board without the VM.

Runs the pulls the board makes (planned crowns, providers, appointments, predeterminations, the Look-Back's
chart pulls), keeping each SQL answer and each patient chart verbatim. `RecordedPmsRepository` replays them,
so case building, crown choice and gap judgement stay the real code paths -- only the VM is gone.

    python scripts/record-pms-snapshot.py [--out mocks/pms/snapshot.json]
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from ophi.sources.abeldent import LIST_APPOINTMENTS, LIST_PROVIDERS, SEARCH_PATIENTS, list_predeterminations
from ophi.sources.pms_lookback import PmsLookBack
from ophi.sources.pms_repository import AbelDentPmsRepository, sql_key

ROOT = Path(__file__).resolve().parents[1]


class Recorder(AbelDentPmsRepository):
    """The live repository, keeping a copy of every answer it gets."""

    def __init__(self) -> None:
        super().__init__()
        self.sql_rows: dict[str, dict] = {}
        self.charts: dict[int, dict] = {}

    def sql(self, query: str, params: dict | None = None) -> list[dict]:
        rows = super().sql(query, params)
        self.sql_rows[sql_key(query, params)] = {"query": query, "params": params, "rows": rows}
        return rows

    def fetch_patient_charts(self, pids: list[int]) -> dict[int, dict]:
        charts = super().fetch_patient_charts(pids)
        self.charts.update(charts)
        return charts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "mocks" / "pms" / "snapshot.json"))
    args = ap.parse_args()

    rec = Recorder()
    planned = rec.planned_patient_ids()
    print(f"planned patients: {len(planned)}")
    cases = rec._pull()  # charts + providers + next crown appointments
    print(f"cases: {len(cases)}")
    claims = list_predeterminations(rec.sql)
    print(f"predeterminations: {len(claims)}")
    report = PmsLookBack(rec)._build()  # pulls charts for every decided claim's patient
    print(f"look-back rows: {len(report.rows)}")
    rec.sql(rec._CHANGED_SQL)          # the change checks, so replay reports a stable stamp
    rec.sql(PmsLookBack._STAMP_SQL)
    rec.sql(LIST_PROVIDERS)            # the lab API's own reads
    rec.sql(SEARCH_PATIENTS, {"q": ""})
    rec.sql(LIST_APPOINTMENTS, {"date": datetime.now(UTC).date().isoformat()})

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "planned_pids": planned,
        "charts": {str(pid): chart for pid, chart in sorted(rec.charts.items())},
        "sql": list(rec.sql_rows.values()),
    }, indent=1, default=str))
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {len(rec.charts)} charts, {len(rec.sql_rows)} queries)")


if __name__ == "__main__":
    main()
