"""The fix plan for each demo case, made offline by scripts/laya-demo-predict.py into cases/demo/laya/<case_id>.json.

The app never loads a model. Each file holds a plan for the case as charted, one with Ophi's safe fixes made, and
one for each set of chair gaps the demo can take; the app shows the plan whose request text matches the chart as
it stands now. Nothing here changes a requirement or a verdict (docs/plan/05-outcomes-learning.md §0).
"""

from __future__ import annotations

import hashlib
from datetime import date
from itertools import combinations
from pathlib import Path

from pydantic import BaseModel

from ophi import fixes
from ophi.casegen.dsl import CAPTURABLE, capture_artifacts
from ophi.cdm.models import Case
from ophi.engine.assess import assess
from ophi.outcomes.case_export import to_export
from ophi.outcomes.training_set import VAGUE, Example, request_text
from ophi.rules.schema import RulePack
from ophi.workflow import chair_actions

READOUT_DIR = Path(__file__).resolve().parents[2] / "cases" / "demo" / "laya"


def text_for(case: Case) -> str:
    """The request as Laya reads it, in the fine-tune's own format."""
    e = Example(preauth_id=case.case_id, clinic="", submitted_on=case.as_of, decided_on=None, sent=to_export(case), decision=VAGUE)
    return request_text(e)


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def note_fingerprint(case: Case) -> str:
    return fingerprint(to_export(case)["clinical_notes"])


def demo_states(case: Case, pack: RulePack) -> list[tuple[str, Case]]:
    """Every chart staff can reach on the demo's buttons, to score ahead: each set of chair gaps taken (stamped on the
    chart's day, as the service stamps them), each with and without Ophi's safe fixes."""
    takeable = sorted({rid for x in chair_actions(assess(case, pack)) for rid in x.unblocks if rid in CAPTURABLE})
    out = []
    for n in range(len(takeable) + 1):
        for taken in combinations(takeable, n):
            c = case.with_artifacts(capture_artifacts(case, dict.fromkeys(taken, case.as_of))) if taken else case
            prefix = "taken:" + "+".join(taken) + "+" if taken else ""
            out.append((prefix.rstrip("+") or "as_charted", c))
            if safe := fixes.open_on(assess(c, pack)):
                out.append((prefix + "safe_fixes", fixes.apply(c, safe, pack)))
    return out


class ScoredPlan(BaseModel):
    state: str  # as_charted | safe_fixes | taken:<chair gaps>[+safe_fixes]
    text_sha256: str
    note_sha256: str | None = None  # the clinical note alone: what Laya's note answers are about
    plan: dict  # the fixer's FixPlan as JSON: now, after_fixes, remaining, fixes, note_answers, drivers, model


class Readout(BaseModel):
    case_id: str
    scored_on: date
    plans: list[ScoredPlan]

    def matching(self, case: Case) -> dict | None:
        """The plan for the chart as it is now, or None when it changed after the plan was made."""
        sha = fingerprint(text_for(case))
        return next((p.plan for p in self.plans if p.text_sha256 == sha), None)

    def note_answers(self, case: Case) -> dict[str, float] | None:
        """Laya's answers about the note, while the note is the one it read. A new film or perio chart changes the
        request, and so the plan, but not what the note says."""
        if plan := self.matching(case):
            return plan["note_answers"]
        sha = note_fingerprint(case)
        return next((p.plan["note_answers"] for p in self.plans if p.note_sha256 == sha), None)


def load(case_id: str, root: Path = READOUT_DIR) -> Readout | None:
    p = root / f"{case_id}.json"
    return Readout.model_validate_json(p.read_text()) if p.exists() else None
