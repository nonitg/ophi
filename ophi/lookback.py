"""Look-Back: re-derive documentation gaps for past preauthorizations from the chart as it stood on
each submission date. Denial text from Sun Life is often unusable ("as per the plan criteria"), so we
never rely on it; the engine finds the gap itself. This is the sales instrument and the measurement
instrument for the recoverability thesis (PLAN.md risk #2)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from ophi.casegen.dsl import build_case
from ophi.engine.assess import assess
from ophi.engine.models import Status
from ophi.rules.loader import default_pack

ROOT = Path(__file__).resolve().parents[1]
LOOKBACK_DIR = ROOT / "cases" / "lookback"

# Gaps that Health Canada and Sun Life name as the top causes of incomplete submissions. A denial with
# one of these open on the submission date counts as "missing a document CDCP explicitly requires".
DOCUMENT_REQUIREMENTS = {"radiograph_pa", "radiograph_bw", "perio_chart", "tx_plan_details", "claim_form"}


class LookBackRow(BaseModel):
    case_id: str
    patient_label: str  # initials, for the shareable report
    patient_name: str  # for staff calling the patient back
    code: str
    tooth_fdi: int
    submitted_on: date
    decision: str  # denied | approved
    fee_dollars: float
    gaps: list[str] = Field(default_factory=list)  # labels of documentation requirements confirmed unsatisfied
    unverifiable: list[str] = Field(default_factory=list)  # source could not see the section; never counted as a gap
    other_open: list[str] = Field(default_factory=list)  # non-document requirements not satisfied (assertions etc.)
    resubmitted: bool = False
    resubmitted_decision: str | None = None
    denial_text: str | None = None

    @property
    def documentation_gap(self) -> bool:
        return bool(self.gaps)


class LookBackReport(BaseModel):
    window_label: str
    ruleset_version: str
    submitted: int
    denied: int
    denied_dollars: float
    approved: int
    denied_with_doc_gap: int
    denied_with_doc_gap_dollars: float
    never_resubmitted: int
    never_resubmitted_dollars: float
    rows: list[LookBackRow]

    @property
    def denial_rate(self) -> float:
        return self.denied / self.submitted if self.submitted else 0.0


def _initials(name: str) -> str:
    parts = [p for p in name.replace(",", " ").split() if p]
    return "".join(p[0].upper() + "." for p in parts[:2]) or "—"


def load_rows(cases_dir: Path = LOOKBACK_DIR) -> list[LookBackRow]:
    rows = []
    for f in sorted(cases_dir.glob("*.yaml")):
        d = yaml.safe_load(f.read_text())
        outcome = d.pop("outcome")
        d["as_of"] = outcome["submitted"]  # judge the chart as it stood on the day it was sent
        case = build_case(d, f.stem)
        a = assess(case, default_pack(case.as_of))  # the rules in force on the day it was sent
        docs = [r for r in a.requirements if r.applicable and r.requirement_id in DOCUMENT_REQUIREMENTS]
        gaps = [r.label for r in docs if r.status == Status.UNSATISFIED]
        unverifiable = [r.label for r in docs if r.status == Status.INDETERMINATE]
        other = [r.label for r in a.requirements if r.applicable and r.requirement_id not in DOCUMENT_REQUIREMENTS
                 and r.status not in (Status.SATISFIED, Status.NOT_APPLICABLE)]
        rows.append(LookBackRow(
            case_id=case.case_id, patient_label=_initials(case.patient.display_name), patient_name=case.patient.display_name, code=case.treatment.code,
            tooth_fdi=case.requested_tooth, submitted_on=case.as_of, decision=outcome["decision"],
            fee_dollars=(case.treatment.fee_cents or 0) / 100, gaps=gaps, unverifiable=unverifiable, other_open=other,
            resubmitted=bool(outcome.get("resubmitted", False)), resubmitted_decision=outcome.get("resubmitted_decision"),
            denial_text=outcome.get("denial_text"),
        ))
    return rows


def run_lookback(cases_dir: Path = LOOKBACK_DIR) -> LookBackReport:
    rows = load_rows(cases_dir)
    denied = [r for r in rows if r.decision == "denied"]
    with_gap = [r for r in denied if r.documentation_gap]
    never = [r for r in denied if not r.resubmitted]
    return LookBackReport(
        window_label="last 12 months",
        ruleset_version=", ".join(sorted({default_pack(r.submitted_on).version for r in rows})) or default_pack().version,
        submitted=len(rows),
        denied=len(denied),
        denied_dollars=round(sum(r.fee_dollars for r in denied), 2),
        approved=sum(1 for r in rows if r.decision == "approved"),
        denied_with_doc_gap=len(with_gap),
        denied_with_doc_gap_dollars=round(sum(r.fee_dollars for r in with_gap), 2),
        never_resubmitted=len(never),
        never_resubmitted_dollars=round(sum(r.fee_dollars for r in never), 2),
        rows=sorted(rows, key=lambda r: r.submitted_on, reverse=True),
    )
