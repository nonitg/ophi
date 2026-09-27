"""Load and lint a rule pack. Content is hashed so every assessment can name the exact bytes it used."""

from __future__ import annotations

import hashlib
import logging
from datetime import date
from functools import lru_cache
from pathlib import Path

import yaml

from ophi.rules.schema import RulePack

PACKS_DIR = Path(__file__).resolve().parents[2] / "packs"
CDCP_DIR = PACKS_DIR / "cdcp"

log = logging.getLogger(__name__)


def load_pack(path: Path) -> RulePack:
    raw = path.read_bytes()
    data = yaml.safe_load(raw)
    pack = RulePack.model_validate(data)
    pack.content_hash = "sha256:" + hashlib.sha256(raw).hexdigest()
    return pack


def pack_dir_for(version: str, cdcp_dir: Path = CDCP_DIR) -> Path:
    return cdcp_dir / version.replace(".", "-")


def rules_date(case) -> date:
    """The date of service a request's rules must hold on, as CDCP judges it: the appointment when booked, else
    the later of the chart's date and the plan's (a plan is written before the chart is read, so usually as_of)."""
    t = case.treatment
    return t.appointment_date or max(case.as_of, t.planned_date or case.as_of)


def pack_in_force(on: date | None = None, cdcp_dir: Path = CDCP_DIR) -> RulePack:
    """The newest pack whose effective date has arrived on `on` (today by default); an approved future-dated update
    waits its turn. Before the first pack took effect, the first pack: Ophi holds no older rules. A newly approved
    pack is picked up without a restart."""
    stamp = tuple((p.parent.name, p.stat().st_mtime_ns) for p in sorted(cdcp_dir.glob("*/pack.yaml")))
    packs = _packs(cdcp_dir, stamp)
    if not packs:
        raise FileNotFoundError(f"no rule pack under {cdcp_dir} loads")
    in_force = [p for p in packs if p.effective_from <= (on or date.today())]
    if not in_force:
        return min(packs, key=lambda p: p.effective_from)
    return sorted(in_force, key=lambda p: p.effective_from)[-1]  # stable sort: on equal dates the later directory wins


default_pack = pack_in_force


def pack_for(case, cdcp_dir: Path = CDCP_DIR) -> RulePack:
    return pack_in_force(rules_date(case), cdcp_dir)


@lru_cache(maxsize=8)
def _packs(cdcp_dir: Path, stamp: tuple) -> list[RulePack]:
    """Every pack under `cdcp_dir` that loads, once per set of pack files (`stamp`). A broken pack is skipped and
    logged, so one bad file never stops every request."""
    packs = []
    for name, _ in stamp:
        try:
            packs.append(load_pack(cdcp_dir / name / "pack.yaml"))
        except Exception:  # noqa: BLE001 — any unreadable or invalid pack
            log.exception("skipping rule pack %s: it does not load", cdcp_dir / name / "pack.yaml")
    return packs
