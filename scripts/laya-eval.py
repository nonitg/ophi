"""Score Laya on the held-out test clinics: the base checkpoint vs the fine-tuned one (plan §7 steps 1 and 3).

Asks through laya.Agent.predict_batch, the path the app would use, so each checkpoint's own temperatures
apply. Every metric sits beside a trivial guess learned from the train clinics:
- note questions: accuracy, Brier score and calibration error against the answer key;
- decision: top-1 on letters that name a reason, and approved-vs-denied AUC on every test request;
- hidden reason: on vague letters, whether the true reason is the top-ranked (or a top-3) denial reason.
Writes the fine-tuned model's answers for every request to <model>/predictions.jsonl for scripts/risk-tree.py.

Run: .venv/bin/python scripts/laya-eval.py [--model var/models/laya-cdcp] [--from-files]
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import laya
import numpy as np
import torch
from dotenv import load_dotenv
from laya.common import ece_score
from sklearn.metrics import roc_auc_score

from ophi.outcomes.laya_questions import APPROVED, DECISION, DECISION_KEYS, QUESTIONS, YES, decision_key
from ophi.outcomes.past_store import load_training
from ophi.outcomes.training_set import NOTE_QUESTIONS, VAGUE, note_labels, request_text, split_by_clinic

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "var/models/laya"
REASONS = [k for k in DECISION_KEYS if k != APPROVED]


def ask(model_dir: Path, examples) -> list[dict[str, dict[str, float]]]:
    agent = laya.Agent(str(model_dir), device="cuda")
    res = agent.predict_batch([request_text(e) for e in examples], QUESTIONS, batch_size=16)
    del agent
    torch.cuda.empty_cache()
    return [{q: r["answers"][q]["probabilities"] for q in QUESTIONS} for r in res]


def note_metrics(p: np.ndarray, y: np.ndarray) -> dict[str, float]:
    right = ((p >= 0.5) == y).astype(float)
    return {"accuracy": right.mean(), "brier": ((p - y) ** 2).mean(), "calibration_error": ece_score(np.maximum(p, 1 - p), right)}


def scores(test, answers) -> dict[str, float]:
    """Every metric for one model's answers on the test requests."""
    out = {}
    firsts = [(e, a) for e, a in zip(test, answers) if e.truth]
    for q in NOTE_QUESTIONS:
        y = np.array([note_labels(e)[q] for e, _ in firsts], float)
        p = np.array([a[q][YES] for _, a in firsts])
        out |= {f"{q} {m}": v for m, v in note_metrics(p, y).items()}
    named = [(e, a) for e, a in zip(test, answers) if e.decision != VAGUE]
    out["decision top-1"] = np.mean([max(a[DECISION], key=a[DECISION].get) == decision_key(e.decision) for e, a in named])
    out["denied AUC"] = roc_auc_score([e.decision != APPROVED for e in test], [1 - a[DECISION][APPROVED] for a in answers])
    hidden = [(decision_key(e.true_reason), sorted(REASONS, key=lambda k: -a[DECISION][k])) for e, a in zip(test, answers) if e.decision == VAGUE]
    out["hidden reason top-1"] = np.mean([truth == ranked[0] for truth, ranked in hidden])
    out["hidden reason top-3"] = np.mean([truth in ranked[:3] for truth, ranked in hidden])
    return out


def trivial(train, test) -> dict[str, float]:
    """What guessing from the train clinics' base rates scores: the bar a model has to clear."""
    out = {}
    firsts = [e for e in train if e.truth]
    for q in NOTE_QUESTIONS:
        rate = np.mean([note_labels(e)[q] for e in firsts])
        y = np.array([note_labels(e)[q] for e in test if e.truth], float)
        out |= {f"{q} {m}": v for m, v in note_metrics(np.full(len(y), rate), y).items()}
    common = Counter(decision_key(e.decision) for e in train if e.decision != VAGUE).most_common(1)[0][0]
    out["decision top-1"] = np.mean([decision_key(e.decision) == common for e in test if e.decision != VAGUE])
    out["denied AUC"] = 0.5
    ranked = [k for k, _ in Counter(decision_key(e.decision) for e in train if e.decision not in (VAGUE, APPROVED)).most_common()]
    hidden = [decision_key(e.true_reason) for e in test if e.decision == VAGUE]
    out["hidden reason top-1"] = np.mean([t == ranked[0] for t in hidden])
    out["hidden reason top-3"] = np.mean([t in ranked[:3] for t in hidden])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=ROOT / "var/models/laya-cdcp")
    ap.add_argument("--from-files", action="store_true", help="read fixtures/cdcp_crowns instead of Supabase")
    args = ap.parse_args()
    load_dotenv()
    parts = split_by_clinic(load_training(args.from_files))
    split_of = {e.preauth_id: name for name, rows in parts.items() for e in rows}
    everything = [e for rows in parts.values() for e in rows]
    test = parts["test"]

    tuned_all = ask(args.model, everything)
    with (args.model / "predictions.jsonl").open("w") as f:
        for e, a in zip(everything, tuned_all):
            f.write(json.dumps({"preauth_id": e.preauth_id, "split": split_of[e.preauth_id], "answers": a}) + "\n")
    tuned = [a for e, a in zip(everything, tuned_all) if split_of[e.preauth_id] == "test"]
    cols = {"trivial": trivial(parts["train"], test), "base": scores(test, ask(BASE, test)), "fine-tuned": scores(test, tuned)}

    print(f"test clinics: {len({e.clinic for e in test})}, requests: {len(test)} "
          f"({sum(bool(e.truth) for e in test)} first requests, {sum(e.decision == VAGUE for e in test)} vague letters)")
    print(f"{'metric (brier, calibration_error: lower is better)':52}" + "".join(f"{c:>12}" for c in cols))
    for metric in cols["fine-tuned"]:
        print(f"{metric:52}" + "".join(f"{cols[c][metric]:12.3f}" for c in cols))
    (args.model / "eval.json").write_text(json.dumps({c: {m: round(float(v), 4) for m, v in s.items()} for c, s in cols.items()}, indent=2))
    print(f"wrote {args.model / 'predictions.jsonl'} and eval.json")


if __name__ == "__main__":
    main()
