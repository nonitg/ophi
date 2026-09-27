"""Make the fixer's plan (ophi.outcomes.fixer) for every demo case (cases/demo) and write cases/demo/laya/<case_id>.json
for the case page, so the app shows it without loading torch.

Each case gets a plan as charted and, when Ophi has safe fixes to make (ophi.fixes), one for the chart with them
made, so the page still has a plan after staff click Apply.

Run after retraining: .venv/bin/python scripts/laya-demo-predict.py [--models var/models]
"""
import argparse
from datetime import date
from pathlib import Path

from ophi import fixes
from ophi.engine.assess import assess
from ophi.outcomes.case_export import to_export
from ophi.outcomes.fixer import plan_fixes
from ophi.outcomes.readout import READOUT_DIR, Readout, ScoredPlan, fingerprint, note_fingerprint, text_for
from ophi.outcomes.risk import RiskModel
from ophi.service import CaseService

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", type=Path, default=ROOT / "var/models", help="holds laya-cdcp/ and risk-tree/")
    args = ap.parse_args()
    model = RiskModel.load(args.models / "laya-cdcp", args.models / "risk-tree")
    svc = CaseService()
    READOUT_DIR.mkdir(parents=True, exist_ok=True)
    for cid in svc.case_ids():
        case = svc.base_case(cid)
        pack = svc.pack_for(case)  # date-of-service pack, as the app scores it
        safe = fixes.open_on(assess(case, pack))
        states = [("as_charted", case)] + ([("safe_fixes", fixes.apply(case, safe, pack))] if safe else [])
        plans = [ScoredPlan(state=s, text_sha256=fingerprint(text_for(c)), note_sha256=note_fingerprint(c),
                            plan=plan_fixes(to_export(c), c.as_of, pack, model, request_id=cid).model_dump(mode="json"))
                 for s, c in states]
        (READOUT_DIR / f"{cid}.json").write_text(Readout(case_id=cid, scored_on=date.today(), plans=plans).model_dump_json(indent=1) + "\n")
        print(f"{cid:10} " + "  ".join(f"{p.state}: {p.plan['now']['level']} -> {p.plan['after_fixes']['level']}"
                                       f" ({p.plan['after_fixes']['because'] or '-'})" for p in plans))


if __name__ == "__main__":
    main()
