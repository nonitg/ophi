"""Denial reason code -> pack requirement ids, versioned next to the pack it refers to."""

from __future__ import annotations

from pathlib import Path

import yaml

from ophi.rules.loader import PACKS_DIR
from ophi.rules.schema import RulePack


def load_denial_map(pack: RulePack) -> dict[str, list[str]]:
    path = PACKS_DIR / "cdcp" / pack.version.replace(".", "-") / "denial_map.yaml"
    m = {str(k): list(v or []) for k, v in yaml.safe_load(path.read_text()).items()}
    known = {r.id for r in pack.requirements}
    bad = sorted({rid for ids in m.values() for rid in ids} - known)
    if bad:
        raise ValueError(f"denial_map.yaml names requirements not in pack {pack.version}: {', '.join(bad)}")
    return m
