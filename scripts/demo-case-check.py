"""Assess every cases/demo/*.yaml through the app's own path and print verdict, completeness, blocking actions,
narrative-validator result and packet verification.

Usage: .venv/bin/python scripts/demo-case-check.py [--as-of YYYY-MM-DD]
  --as-of re-assesses each case as if submitted on that date (e.g. a resubmission).
"""

from __future__ import annotations

import argparse
import tempfile
from datetime import date
from pathlib import Path

from ophi.engine.assess import assess
from ophi.packet.build import build_packet
from ophi.packet.narrative import draft_narrative, validate_narrative
from ophi.service import CaseService, Store, identity_tokens
from ophi.verify.verifier import verify_packet


def check(svc: CaseService, case_id: str, as_of: date | None, work: Path) -> tuple[str, list[str]]:
    view = svc.view(case_id)
    case, a = view.case, view.assessment
    if as_of:
        case = case.model_copy(update={"as_of": as_of})
        a = assess(case, svc.pack)
    violations = validate_narrative(draft_narrative(case, a, svc.pack), case)
    out = work / case_id
    build_packet(case, a, out, pack=svc.pack)
    report = verify_packet(out, forbidden_tokens=identity_tokens(case))
    blocking = [x.title for x in a.actions if x.blocking]
    row = (f"{case_id:<11} {case.as_of}  {a.verdict.value:<17} {a.completeness['satisfied']:>2}/{a.completeness['applicable']:<3}"
           f" {len(blocking):>8}  {'ok' if not violations else f'{len(violations)} violations':<9} {'ok' if report.ok else 'FAIL'}")
    details = [f"    blocking: {t}" for t in blocking] + [f"    narrative: {v}" for v in violations]
    details += [f"    packet: {f}" for f in report.findings]
    return row, details


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", type=date.fromisoformat, default=None)
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        svc = CaseService(store=Store(Path(tmp) / "store"))
        print(f"{'case':<11} {'as_of':<10}  {'verdict':<17} {'done':<6} {'blocking':>8}  {'narrative':<9} packet")
        for cid in svc.case_ids():
            row, details = check(svc, cid, args.as_of, Path(tmp) / "packets")
            print(row, *details, sep="\n")


if __name__ == "__main__":
    main()
