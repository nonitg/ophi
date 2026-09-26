"""Assessment output — what the UI, the packet and the eval harness consume. Enum verdict, no score."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from ophi.rules.schema import Clause


class Status(StrEnum):
    SATISFIED = "satisfied"
    AT_RISK = "at_risk"
    PENDING_CONFIRMATION = "satisfied_pending_confirmation"
    UNSATISFIED = "unsatisfied"
    INDETERMINATE = "indeterminate"
    NOT_APPLICABLE = "not_applicable"


# Worst-first for conjunctions; best-first (reversed) for alternatives.
SEVERITY: dict[Status, int] = {
    Status.UNSATISFIED: 5,
    Status.INDETERMINATE: 4,
    Status.PENDING_CONFIRMATION: 3,
    Status.AT_RISK: 2,
    Status.SATISFIED: 1,
    Status.NOT_APPLICABLE: 0,
}


class Verdict(StrEnum):
    PREAUTH_NOT_REQUIRED = "PREAUTH_NOT_REQUIRED"
    EXCLUDED_AS_CODED = "EXCLUDED_AS_CODED"
    BLOCKED = "BLOCKED"
    NEEDS_INPUT = "NEEDS_INPUT"
    READY_WITH_RISKS = "READY_WITH_RISKS"
    READY_TO_SUBMIT = "READY_TO_SUBMIT"


class StaleItem(BaseModel):
    artifact_id: str
    label: str
    captured_at: date
    age_days: int
    over_by_days: int


class Shortfall(BaseModel):
    """Always populated, even when satisfied — it is what makes gap text precise."""

    missing: list[str] = Field(default_factory=list)
    stale: list[StaleItem] = Field(default_factory=list)
    undated: list[str] = Field(default_factory=list)
    pending_confirmation: list[str] = Field(default_factory=list)
    missing_assertions: list[str] = Field(default_factory=list)
    not_met_assertions: list[str] = Field(default_factory=list)
    incomplete: dict | None = None
    near_miss: str | None = None
    detail: str | None = None

    @property
    def distance(self) -> int:
        """How far from satisfied: count of things missing. Used to pick the closest near-miss."""
        n = len(self.missing) + len(self.stale) + len(self.undated) + len(self.pending_confirmation) \
            + len(self.missing_assertions) + len(self.not_met_assertions)
        if self.incomplete:
            n += max(1, len(self.incomplete.get("teeth_without_6_sites", [])))
        return n

    @property
    def empty(self) -> bool:
        return not any([self.missing, self.stale, self.undated, self.pending_confirmation,
                        self.missing_assertions, self.not_met_assertions, self.incomplete])


class EvidenceRef(BaseModel):
    artifact_id: str
    type: str
    label: str
    captured_at: date | None = None
    age_days: int | None = None
    expires_on: date | None = None
    extraction_method: str = "db_field"
    teeth_fdi: list[int] = Field(default_factory=list)
    confirmed: bool = True
    quote: str | None = None


class EscalationResult(BaseModel):
    id: str
    fired: bool
    detail: str
    demanded: str | None = None
    scope: dict | None = None


class LeafResult(BaseModel):
    status: Status
    matched: list[EvidenceRef] = Field(default_factory=list)
    shortfall: Shortfall = Field(default_factory=Shortfall)
    expires_on: date | None = None
    detail: str = ""


class RequirementResult(BaseModel):
    requirement_id: str
    label: str
    clause: Clause
    status: Status
    applicable: bool = True
    satisfied_via: str | None = None
    evidence: list[EvidenceRef] = Field(default_factory=list)
    shortfall: Shortfall = Field(default_factory=Shortfall)
    escalations_evaluated: list[EscalationResult] = Field(default_factory=list)
    risk_reason: str | None = None
    explanation: str = ""
    detail: str = ""  # leaf detail without the rule prefix, for action text
    near_miss_option: str | None = None  # when nothing passed: the cheapest option tried
    near_miss_title: str | None = None
    expires_on: date | None = None


class Action(BaseModel):
    rank: int
    blocking: bool
    effort: str
    action_type: str
    title: str
    why: str
    unblocks: list[str]


class Deadline(BaseModel):
    artifact_id: str
    label: str
    expires_on: date
    requirement_id: str


class ScheduleResult(BaseModel):
    disposition: str  # preauth_required | not_required | excluded | not_in_schedule_b
    preauth_required: bool | None
    detail: str
    clause: Clause | None = None


class Workload(BaseModel):
    """What the engine did, so the UI can show the manual cross-check it replaced."""

    artifacts_scanned: int
    requirements_evaluated: int
    subsystems_read: list[str]
    elapsed_ms: int


class RulesetRef(BaseModel):
    id: str
    version: str
    content_hash: str
    effective_from: date
    weights_hash: str | None = None  # outcome weights used to order equal-ranked actions, if any


class Assessment(BaseModel):
    assessment_id: str
    case_id: str
    ruleset: RulesetRef
    assessed_at: datetime
    submission_date_assumed: date
    engine_version: str
    schedule: ScheduleResult
    verdict: Verdict
    completeness: dict[str, int]
    requirements: list[RequirementResult]
    actions: list[Action]
    deadlines: list[Deadline]
    notes: list[str]
    workload: Workload

    def requirement(self, rid: str) -> RequirementResult | None:
        return next((r for r in self.requirements if r.requirement_id == rid), None)

    @property
    def blocking_count(self) -> int:
        return sum(1 for a in self.actions if a.blocking)
