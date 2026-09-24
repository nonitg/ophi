"""Load and lint a rule pack. Content is hashed so every assessment can name the exact bytes it used."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

import yaml

from ophi.rules.schema import RulePack

PACKS_DIR = Path(__file__).resolve().parents[2] / "packs"


def load_pack(path: Path) -> RulePack:
    raw = path.read_bytes()
    data = yaml.safe_load(raw)
    pack = RulePack.model_validate(data)
    pack.content_hash = "sha256:" + hashlib.sha256(raw).hexdigest()
    return pack


@lru_cache(maxsize=8)
def default_pack() -> RulePack:
    """The newest pack under packs/cdcp/. Production resolves by intended submission date; v1 ships one."""
    candidates = sorted((PACKS_DIR / "cdcp").glob("*/pack.yaml"))
    if not candidates:
        raise FileNotFoundError("no rule packs under packs/cdcp/")
    return load_pack(candidates[-1])
