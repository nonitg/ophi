"""Denial risk from the structured request, with and without Laya's note answers (plan §4.1, §7 steps 2 and 4).

LightGBM on the engine's reading of each requirement plus the raw values it can't weigh (film ages, depths,
the clinic's track record). Trained on the train clinics, early-stopped on the calibration clinics, scored
on the test clinics. Given Laya's predictions (scripts/laya-eval.py), a second model adds the note answers
as features, and both are scored on the same test requests beside Laya's own decision answer.

Run: .venv/bin/python scripts/risk-tree.py [--laya var/models/laya-cdcp/predictions.jsonl]
"""
import argparse
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
from sklearn.metrics import brier_score_loss, roc_auc_score

from ophi.outcomes.laya_questions import APPROVED, DECISION, YES
from ophi.outcomes.training_set import NOTE_QUESTIONS, clinic_denial_rates, features, load_examples, split_by_clinic
from ophi.rules.loader import default_pack

# Small, shallow trees: a few hundred training rows.
PARAMS = dict(n_estimators=1000, learning_rate=0.03, num_leaves=15, min_child_samples=10, subsample=0.8, subsample_freq=1,
              colsample_bytree=0.8, random_state=0, verbose=-1)


def encode(rows: list[dict]) -> tuple[np.ndarray, list[str], list[int]]:
    """Feature dicts -> matrix. Text values become category indices; a value not sent stays NaN."""
    cols = list(rows[0])
    vocab = {c: sorted({r[c] for r in rows if isinstance(r[c], str)}) for c in cols}
    X = np.array([[np.nan if r[c] is None else vocab[c].index(r[c]) if vocab[c] else r[c] for c in cols] for r in rows], float)
    return X, cols, [i for i, c in enumerate(cols) if vocab[c]]


def fit(X, y, split, cat) -> lgb.LGBMClassifier:
    m = lgb.LGBMClassifier(**PARAMS)
    m.fit(X[split == "train"], y[split == "train"], eval_X=X[split == "calib"], eval_y=y[split == "calib"],
          categorical_feature=cat, callbacks=[lgb.early_stopping(50, verbose=False)])
    return m


def drivers(m: lgb.LGBMClassifier, X: np.ndarray, cols: list[str], n: int) -> list[tuple[str, float]]:
    """Mean push on the log-odds of denial per input over the given rows (last column is the bias)."""
    contrib = m.booster_.predict(X, pred_contrib=True)[:, :-1]
    return sorted(zip(cols, contrib.mean(0) if len(X) == 1 else np.abs(contrib).mean(0)), key=lambda t: -abs(t[1]))[:n]


def line(name: str, y: np.ndarray, p: np.ndarray) -> str:
    return f"{name:44} AUC {roc_auc_score(y, p):.3f}   Brier {brier_score_loss(y, p):.3f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--laya", type=Path, help="predictions.jsonl from scripts/laya-eval.py")
    args = ap.parse_args()
    parts = split_by_clinic(load_examples())
    ordered = [e for rows in parts.values() for e in rows]
    split = np.array([name for name, rows in parts.items() for _ in rows])
    rates, pack = clinic_denial_rates(ordered), default_pack()
    rows = [features(e, pack, rates[e.preauth_id]) for e in ordered]
    y = np.array([e.decision != APPROVED for e in ordered], float)  # a vague letter is still a denial
    te = split == "test"

    print(f"test: {te.sum()} requests from {len({e.clinic for e in parts['test']})} clinics, {y[te].mean():.0%} denied")
    print(line("base rate from train clinics", y[te], np.full(te.sum(), y[split == 'train'].mean())))
    X, cols, cat = encode(rows)
    m = fit(X, y, split, cat)
    print(line(f"LightGBM, structured fields ({m.best_iteration_} trees)", y[te], m.predict_proba(X[te])[:, 1]))

    if args.laya:
        pred = {r["preauth_id"]: r["answers"] for r in map(json.loads, args.laya.read_text().splitlines())}
        # Laya's answers on train clinics are in-sample, so this model may over-trust them; the test score stays honest.
        rows = [r | {f"laya_{q}": pred[e.preauth_id][q][YES] for q in NOTE_QUESTIONS} for r, e in zip(rows, ordered)]
        X, cols, cat = encode(rows)
        m = fit(X, y, split, cat)
        print(line(f"LightGBM, structured + Laya notes ({m.best_iteration_} trees)", y[te], m.predict_proba(X[te])[:, 1]))
        print(line("Laya decision question alone", y[te], np.array([1 - pred[e.preauth_id][DECISION][APPROVED] for e in parts["test"]])))

    print("\nwhat drives the risk (mean |push| on test requests):")
    for c, v in drivers(m, X[te], cols, 8):
        print(f"  {c:32} {v:.3f}")
    p = m.predict_proba(X[te])[:, 1]
    i = int(p.argmax())
    e = parts["test"][i]
    print(f"\nhighest-risk test request {e.preauth_id} ({p[i]:.0%}, decided: {e.decision}); pushes on the log-odds of denial:")
    for c, v in drivers(m, X[te][i:i + 1], cols, 5):
        print(f"  {c:32} {v:+.3f}")


if __name__ == "__main__":
    main()
