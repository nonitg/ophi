"""The fix plan for each demo case, made offline by scripts/laya-demo-predict.py into cases/demo/laya/<case_id>.json.

The app never loads a model. Each file holds a plan for the case as charted and, when Ophi has safe fixes to
make, one for the chart with them made; the app shows the plan whose request text matches the chart as it
stands now. Nothing here changes a requirement or a verdict (docs/plan/05-outcomes-learning.md §0).
"""

from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path

from pydantic import BaseModel

from ophi.cdm.models import Case
from ophi.outcomes.case_export import to_export
from ophi.outcomes.training_set import VAGUE, Example, request_text

READOUT_DIR = Path(__file__).resolve().parents[2] / "cases" / "demo" / "laya"


def text_for(case: Case) -> str:
    """The request as Laya reads it, in the fine-tune's own format."""
    e = Example(preauth_id=case.case_id, clinic="", submitted_on=case.as_of, decided_on=None, sent=to_export(case), decision=VAGUE)
    return request_text(e)


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class ScoredPlan(BaseModel):
    state: str  # as_charted | safe_fixes
    text_sha256: str
    plan: dict  # the fixer's FixPlan as JSON: now, after_fixes, remaining, fixes, note_answers, drivers, model


class Readout(BaseModel):
    case_id: str
    scored_on: date
    plans: list[ScoredPlan]

    def matching(self, case: Case) -> dict | None:
        """The plan for the chart as it is now, or None when it changed after the plan was made."""
        sha = fingerprint(text_for(case))
        return next((p.plan for p in self.plans if p.text_sha256 == sha), None)


def load(case_id: str, root: Path = READOUT_DIR) -> Readout | None:
    p = root / f"{case_id}.json"
    return Readout.model_validate_json(p.read_text()) if p.exists() else None
