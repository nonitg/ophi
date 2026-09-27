"""Print the fixer's plan for crown requests (docs/plan/05-outcomes-learning.md §5), and check it on the
held-out clinics.

--check, on calibration + test clinics (never trained on):
- risk levels: how many requests land in each level, and how many of those Sun Life actually denied;
- resubmissions: when a clinic really resubmitted with a fix, did the risk move the way the second
  decision did (down for approvals, less so for denials)?

Run: .venv/bin/python scripts/fix-plan.py [PREAUTH_ID ...] [--json] [--check]   (default PA-SYN-300010)
"""
import argparse
import json

import numpy as np
from dotenv import load_dotenv
from sklearn.metrics import roc_auc_score

from ophi.outcomes.fixer import FixPlan, level, plan_fixes
from ophi.outcomes.laya_questions import APPROVED
from ophi.outcomes.past_store import load_training
from ophi.outcomes.risk import RiskModel
from ophi.outcomes.training_set import VAGUE, clinic_denial_rates, split_by_clinic
from ophi.rules.loader import default_pack


def show(plan: FixPlan):
    b = f" ({plan.after_fixes.because})" if plan.after_fixes.because else ""
    print(f"\n== {plan.request_id}  Now: {plan.now.level} · After fixes: {plan.after_fixes.level}{b}")
    print(f"   {plan.remaining}")
    for f in plan.fixes:
        drop = f"{f.risk_drop:+.2f}" if f.risk_drop is not None else "  —  "
        cite = f"[{f.clause.ref}]" if f.clause else "[no pack clause]" if f.kind == "dentist" else ""
        print(f"   {drop}  {f.kind:7} {f.who:7} {f.title}  {cite}{'  (wait)' if f.wait else ''}")
    print("   drivers: " + "; ".join(f"{d.label} {d.push:+.2f}" for d in plan.drivers[:4]))


def check(model, pack, examples, rates):
    held = [e for name, rows in split_by_clinic(examples).items() if name != "train" for e in rows]
    scores = [model.score([e], pack, rates[e.preauth_id])[0] for e in held]  # each with its own clinic's track record
    by = {"low": [], "medium": [], "high": []}
    for e, s in zip(held, scores):
        by[level(s.p_denied)].append(e.decision != APPROVED)
    print(f"\nrisk levels on {len(held)} held-out requests:")
    for lv, denied in by.items():
        print(f"  {lv:6} {len(denied):4} requests, {np.mean(denied) if denied else float('nan'):.0%} denied")

    p = {e.preauth_id: s.p_denied for e, s in zip(held, scores)}
    pairs = [(e.preauth_id, e.preauth_id.removesuffix("/resubmission"), e.decision) for e in held if e.preauth_id.endswith("/resubmission")]
    moved = {"approved": [], "denied": []}
    for rid, first, decision in pairs:
        moved["approved" if decision == APPROVED else "denied"].append(p[first] - p[rid])
    print(f"resubmissions on held-out clinics ({len(pairs)}): mean risk removed by the clinic's real fix")
    for outcome, drops in moved.items():
        print(f"  second decision {outcome:8} {len(drops):3} cases, risk removed {np.mean(drops) if drops else float('nan'):+.3f}")
    after = roc_auc_score([d != APPROVED for _, _, d in pairs], [p[rid] for rid, _, _ in pairs])
    print(f"  risk after the fix separates the second decisions with AUC {after:.2f} (0.5 = no better than chance)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", default=["PA-SYN-300010"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--from-files", action="store_true", help="read fixtures/cdcp_crowns instead of Supabase")
    args = ap.parse_args()
    load_dotenv()
    examples = load_training(args.from_files)
    rates, pack, model = clinic_denial_rates(examples), default_pack(), RiskModel.load()
    by_id = {e.preauth_id: e for e in examples}
    for rid in args.ids:
        e = by_id[rid]
        plan = plan_fixes(e.sent, e.submitted_on, pack, model, rates[rid], rid)
        print(plan.model_dump_json(indent=1)) if args.json else show(plan)
        if e.decision:
            print(f"   (Sun Life decided: {e.decision}{'; true reason ' + e.true_reason if e.decision == VAGUE else ''})")
    if args.check:
        check(model, pack, examples, rates)


if __name__ == "__main__":
    main()
