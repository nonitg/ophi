"""Per-requirement denial lift from past outcomes, frozen into a hashed file the engine can read.

Weights only break ties between actions the rules already rank equal; they never add, remove or
re-verdict a requirement, and they are never shown as a likelihood.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]
WEIGHTS_PATH = ROOT / "var" / "requirement_weights.yaml"
MIN_N = 10  # below this on either side, the difference is noise


class Weights(BaseModel):
    pack_version: str
    lift: dict[str, float]
    content_hash: str = ""


def compute(pack_version: str, rows: list[dict]) -> Weights:
    lift = {}
    for r in rows:
        if r["n_missing"] < MIN_N or r["n_present"] < MIN_N:
            lift[r["requirement_id"]] = 0.0
            continue
        lift[r["requirement_id"]] = round(r["denied_missing"] / r["n_missing"] - r["denied_present"] / r["n_present"], 4)
    return Weights(pack_version=pack_version, lift=lift)


def write(w: Weights, path: Path = WEIGHTS_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"pack_version": w.pack_version, "lift": w.lift}, sort_keys=True))
    return path


def load(path: Path = WEIGHTS_PATH) -> Weights | None:
    if not path.exists():
        return None
    raw = path.read_bytes()
    w = Weights.model_validate(yaml.safe_load(raw))
    w.content_hash = "sha256:" + hashlib.sha256(raw).hexdigest()
    return w
