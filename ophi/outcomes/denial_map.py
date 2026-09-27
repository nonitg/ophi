"""Denial reason code -> pack requirement ids, versioned next to the pack it refers to."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from ophi.rules.loader import PACKS_DIR
from ophi.rules.schema import RulePack


@lru_cache(maxsize=8)
def _read(version: str) -> dict[str, list[str]]:
    """Cached on the pack version: a page render attributes a denial on every open, and the file
    changes only when the pack does."""
    path = PACKS_DIR / "cdcp" / version.replace(".", "-") / "denial_map.yaml"
    return {str(k): list(v or []) for k, v in yaml.safe_load(path.read_text()).items()}


def load_denial_map(pack: RulePack) -> dict[str, list[str]]:
    m = _read(pack.version)
    known = {r.id for r in pack.requirements}
    bad = sorted({rid for ids in m.values() for rid in ids} - known)
    if bad:
        raise ValueError(f"denial_map.yaml names requirements not in pack {pack.version}: {', '.join(bad)}")
    return m


# Sun Life's letters name a reason in the app's own vocabulary (workflow.REASONS); the administrator exports
# name it as a code. They are the same reasons under two names, so a live denial can be attributed through the
# same SME-maintained denial_map.yaml the past exports go through, and lands in the same training pool.
EXPORT_CODE: dict[str, str] = {
    "missing_radiograph": "DOC_MISSING_RADIOGRAPH",
    "stale_radiograph": "DOC_RADIOGRAPH_STALE",
    "missing_perio_chart": "DOC_MISSING_PERIO_CHART",
    "basic_treatment_pending": "CLIN_ACTIVE_DISEASE",
    "endo_not_healed": "CLIN_ENDO_NOT_HEALED",
    "insufficient_notes": "DOC_INSUFFICIENT_NOTES",
    "invalid_lab_code": "ADMIN_INVALID_CODE",
    "not_extensively_restored": "CLIN_NOT_EXT_RESTORED",
    "insufficient_ferrule": "CLIN_FERRULE",
    "perio_prognosis": "CLIN_PERIO_PROGNOSIS",
    "need_not_met": "CLIN_NEED_NOT_MET",
    "indication_not_covered": "CLIN_NOT_COVERED_INDICATION",
    "frequency_limit": "FREQ_LIMIT",
    "client_ineligible": "ELIGIBILITY",
    "tooth_ineligible": "TOOTH_INELIGIBLE",
    "duplicate_request": "DUPLICATE_REQUEST",
}


def requirements_for(reason_key: str | None, pack: RulePack) -> list[str] | None:
    """Pack requirements the letter's reason points at. None when the letter named no reason, or when the SME
    hasn't reviewed the code yet -- both mean "don't claim to know", which is not the same as the empty list
    ("reviewed: no requirement in this pack covers it")."""
    code = EXPORT_CODE.get(reason_key or "")
    return load_denial_map(pack).get(code) if code else None
