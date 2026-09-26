"""Denial risk for a crown request and what drives it (docs/plan/05-outcomes-learning.md §4): Laya reads
the note, LightGBM weighs its answers with the engine's reading and the raw values.

Trained by scripts/laya-finetune.py and scripts/risk-tree.py --save. Only RiskModel.load imports laya and
lightgbm, so the fixer, the web app and the tests can use this module without them.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from pydantic import BaseModel

from ophi.outcomes.laya_questions import QUESTIONS, YES
from ophi.outcomes.training_set import NOTE_QUESTIONS, Example, features, request_text
from ophi.rules.schema import RulePack

ROOT = Path(__file__).resolve().parents[2]
LAYA_DIR = ROOT / "var/models/laya-cdcp"
TREE_DIR = ROOT / "var/models/risk-tree"
NOTE_ONLY = {q: QUESTIONS[q] for q in NOTE_QUESTIONS}


class Score(BaseModel):
    p_denied: float
    note: dict[str, float]  # P(yes) per note question
    drivers: list[tuple[str, float]]  # (feature, push on the log-odds of denial), strongest first


def with_note_answers(row: dict, note: dict[str, float]) -> dict:
    return row | {f"laya_{q}": note[q] for q in NOTE_QUESTIONS}


def build_vocab(rows: list[dict]) -> dict[str, list[str]]:
    """Category values per text column; saved with the model so run time encodes exactly as training did."""
    return {c: sorted({r[c] for r in rows if isinstance(r[c], str)}) for c in rows[0]}


def encode(rows: list[dict], cols: list[str], vocab: dict[str, list[str]]) -> np.ndarray:
    """Feature dicts -> matrix. Text becomes its category index; a value not sent, or unseen in training, is NaN."""
    def cell(c, v):
        if v is None:
            return np.nan
        if vocab[c]:
            return vocab[c].index(v) if v in vocab[c] else np.nan
        return v
    return np.array([[cell(c, r[c]) for c in cols] for r in rows], float)


def categorical(cols: list[str], vocab: dict[str, list[str]]) -> list[int]:
    return [i for i, c in enumerate(cols) if vocab[c]]


class RiskModel:
    def __init__(self, agent, booster, cols: list[str], vocab: dict[str, list[str]], label: dict[str, str]):
        self.agent, self.booster, self.cols, self.vocab, self.label = agent, booster, cols, vocab, label

    @classmethod
    def load(cls, laya_dir: Path = LAYA_DIR, tree_dir: Path = TREE_DIR, device: str | None = None) -> RiskModel:
        import laya
        import lightgbm as lgb

        meta = json.loads((tree_dir / "features.json").read_text())
        training = json.loads((laya_dir / "rl_agent_config.json").read_text())["training"]
        tree_hash = hashlib.sha256((tree_dir / "model.txt").read_bytes()).hexdigest()[:12]
        label = {"laya": f"laya-cdcp {training['trained_on']} data {training['data'].removeprefix('sha256:')[:12]}",
                 "risk": f"risk-tree {meta['trained_on']} {tree_hash}"}
        return cls(laya.Agent(str(laya_dir), device=device), lgb.Booster(model_file=str(tree_dir / "model.txt")),
                   meta["cols"], meta["vocab"], label)

    def score(self, requests: list[Example], pack: RulePack, clinic_denial_rate: float | None = None) -> list[Score]:
        """One forward pass for every request, so a request and all its what-if copies score together."""
        answers = self.agent.predict_batch([request_text(e) for e in requests], NOTE_ONLY, batch_size=16)
        notes = [{q: a["answers"][q]["probabilities"][YES] for q in NOTE_QUESTIONS} for a in answers]
        X = encode([with_note_answers(features(e, pack, clinic_denial_rate), n) for e, n in zip(requests, notes)], self.cols, self.vocab)
        p = self.booster.predict(X)
        contrib = self.booster.predict(X, pred_contrib=True)[:, :-1]  # last column is the bias
        return [Score(p_denied=float(pi), note=n, drivers=sorted(zip(self.cols, map(float, ci)), key=lambda t: -abs(t[1]))[:8])
                for pi, n, ci in zip(p, notes, contrib)]
