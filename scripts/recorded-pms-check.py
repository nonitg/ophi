#!/usr/bin/env python3
"""Check the recorded PMS answers the board exactly as the live VM does: same cases, same patients, same past."""

from __future__ import annotations

from ophi.sources.abeldent import list_predeterminations
from ophi.sources.pms_lookback import PmsLookBack
from ophi.sources.pms_repository import AbelDentPmsRepository, RecordedPmsRepository


def summary(repo) -> dict:
    cases = repo.get_cases()
    return {
        "cases": sorted((c.case_id, c.patient.display_name, c.treatment.code, c.requested_tooth) for c in cases),
        "claims": sorted((c.claim_id, c.patient_name, c.status, c.outcome) for c in list_predeterminations(repo.sql)),
        "lookback": sorted((r.case_id, r.patient_name, r.decision, tuple(r.gaps)) for r in PmsLookBack(repo).report().rows),
    }


def main() -> None:
    live, rec = summary(AbelDentPmsRepository()), summary(RecordedPmsRepository())
    ok = True
    for key in live:
        if live[key] == rec[key]:
            print(f"{key}: {len(live[key])} match")
        else:
            ok = False
            print(f"{key}: MISMATCH\n  live: {live[key]}\n  rec:  {rec[key]}")
    print("\n".join(f"  {c[1]} — {c[2]} #{c[3]}" for c in rec["cases"]))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
