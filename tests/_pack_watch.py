"""Shared builders for pack watch/draft/approve tests: a scratch copy of the shipped CDCP pack and a fake web.

Nothing here touches the network, packs/ or var/: every fetch is served from a dict, every write lands in tmp_path.
The fake web itself is ophi.rules.fixture_web, shared with scripts/pack-watch-fixture.py.
"""

from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

import pytest

from ophi.rules import watch
from ophi.rules.fixture_web import (  # noqa: F401 — re-exported for the tests
    FIX,
    NEW_DOC,
    PAGE,
    WATCH,
    fetcher,
    served,
)
from ophi.rules.loader import CDCP_DIR

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 9, 26)
BASE = "2026-01-26"
# a crown on 99113 (current until the fixture factsheet retires it), one on 99333 (already retired), and a filling
FEW_CASES = ("adversarial/current_lab_code.yaml", "adversarial/retired_lab_code.yaml", "adversarial/filling_not_preauth.yaml")


@pytest.fixture
def cdcp(tmp_path: Path) -> Path:
    """A copy of the shipped pack with its baseline and changelog, so drafts and approvals write nowhere real."""
    shutil.copytree(CDCP_DIR / BASE, tmp_path / "cdcp" / BASE)
    shutil.copy(CDCP_DIR / "CHANGELOG.md", tmp_path / "cdcp" / "CHANGELOG.md")
    return tmp_path / "cdcp"


@pytest.fixture
def cases(tmp_path: Path) -> Path:
    """A few cases for the impact check, so a draft does not assess the whole corpus."""
    for rel in FEW_CASES:
        (tmp_path / "cases" / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / "cases" / rel, tmp_path / "cases" / rel)
    return tmp_path / "cases"


@pytest.fixture
def status(tmp_path: Path) -> Path:
    """Where the board's rules-watch status goes: tmp, never var/."""
    return tmp_path / "status.json"


def draft_fixture(cdcp: Path, cases: Path):
    """Check and draft against the April 2027 factsheet fixture, into cdcp/drafts/ where approve expects drafts."""
    from ophi.rules import draft

    get = fetcher(served(cdcp / BASE))
    return draft.draft(watch.check(cdcp / BASE, TODAY, get, config=WATCH), TODAY, get, cases_dir=cases,
                       drafts_dir=cdcp / "drafts")
