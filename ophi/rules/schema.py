"""Rule pack schema — the closed predicate vocabulary.

An SME edits the YAML: labels, clauses, months, thresholds, which criteria apply. Engineers own the
semantics of each predicate kind here and in the evaluator. Anything the YAML cannot express is a
signal that an engineer must look, not something to improvise around.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from ophi.cdm.models import ArtifactType, RadiographView

Effort = Literal["none", "confirm_in_app", "chart_entry", "reuse_existing", "new_radiograph", "lab", "clinical"]
EFFORT_ORDER: dict[str, int] = {e: i for i, e in enumerate(
    ["none", "confirm_in_app", "chart_entry", "reuse_existing", "new_radiograph", "lab", "clinical"])}


class Clause(BaseModel):
    source: str
    ref: str
    quote: str | None = None
    also: Clause | None = None


class Recency(BaseModel):
    months: int


class Find(BaseModel):
    """Artifact query leaf — the only way a rule references the chart."""

    artifact_type: ArtifactType
    view: RadiographView | None = None
    for_tooth: Literal["requested"] | None = None
    laterality: list[Literal["right", "left"]] | None = None
    completeness: Literal["complete"] | None = None
    sites_per_tooth: int | None = None
    coverage: Literal["all_sextants"] | None = None
    criterion: str | None = None
    recency: Recency | None = None


class Fact(BaseModel):
    """Deterministic predicate over structured case fields (age, tooth, history, plan)."""

    fact: Literal[
        "age_at_least", "tooth_class_in", "adjacent_molars_missing", "no_prior_code_on_tooth_within",
        "prior_codes_count_below", "no_pending_codes_with_prefix", "no_retired_codes", "client_identifiers_present",
    ]
    codes: list[str] | None = None  # explicit code list for frequency facts (preferred over prefix)
    years: int | None = None
    classes: list[str] | None = None
    prefix: str | None = None
    prefixes: list[str] | None = None
    months: int | None = None
    max_count: int | None = None
    exclude_requested: bool = False
    exclude_prefixes: list[str] | None = None


class NotEscalated(BaseModel):
    not_escalated: str


class ProvidedByPacket(BaseModel):
    provided_by_packet: Literal[True]


class Option(BaseModel):
    id: str
    label: str
    remediation_cost: Effort = "chart_entry"
    confers_status: Literal["satisfied", "at_risk"] = "satisfied"
    risk_reason: str | None = None
    gap_title: str | None = None  # option-specific action title; `{missing}` is replaced with the shortfall
    find: Find | None = None
    fact: str | None = None
    classes: list[str] | None = None
    require_all: list[Predicate] | None = None

    def predicate(self) -> Predicate:
        if self.find is not None:
            return FindP(find=self.find)
        if self.fact is not None:
            return Fact(fact=self.fact, classes=self.classes)  # type: ignore[arg-type]
        if self.require_all is not None:
            return RequireAll(require_all=self.require_all)
        raise ValueError(f"option {self.id} has no predicate")


class FindP(BaseModel):
    find: Find


class OneOf(BaseModel):
    one_of: list[Option] = Field(min_length=1)


class RequireAll(BaseModel):
    require_all: list[Predicate] = Field(min_length=1)


Predicate = FindP | Fact | OneOf | RequireAll | NotEscalated | ProvidedByPacket


class EscalationWhen(BaseModel):
    any: list[EscalationWhen] | None = None
    psr_score_gte: int | None = None
    psr_score_eq: int | None = None
    min_sextants: int = 1
    in_sextant_of_requested_tooth: bool = False


class Escalation(BaseModel):
    id: str
    precedence: int
    when: EscalationWhen
    demand: str
    message: str


class PolicyDecision(BaseModel):
    id: str
    question: str
    decision: str
    decided_on: date | None = None
    decided_by: str | None = None


class AppliesWhen(BaseModel):
    tooth_has_endo_history: bool | None = None
    treatment_has_lab_codes: bool | None = None


class Gap(BaseModel):
    title: str
    why: str | None = None
    near_miss_why: str | None = None  # rendered when related evidence exists but does not satisfy; {bw_date} {tooth}
    action_type: str
    effort: Effort


class Requirement(BaseModel):
    id: str
    label: str
    clause: Clause
    applies_when: AppliesWhen | None = None
    satisfied_by: Predicate
    escalations: list[Escalation] = Field(default_factory=list)
    policy_decision: PolicyDecision | None = None
    gap: Gap

    @model_validator(mode="after")
    def _escalation_precedence_unique(self) -> Requirement:
        precs = [e.precedence for e in self.escalations]
        if len(precs) != len(set(precs)):
            raise ValueError(f"{self.id}: escalation precedences must be unique (dict order is not a tiebreak)")
        return self


class FrequencyLimit(BaseModel):
    count: int
    months: int


class RetiredCode(BaseModel):
    code: str
    replaced_by: str
    clause: Clause


class ExcludedFamily(BaseModel):
    prefix: str
    label: str
    clause: Clause


class Schedule(BaseModel):
    service_category: str
    preauth_always: list[str]
    family_prefix: str
    family_label: str
    excluded_families: list[ExcludedFamily] = Field(default_factory=list)
    frequency: dict
    retired_codes: list[RetiredCode] = Field(default_factory=list)


class AssertionCriterion(BaseModel):
    label: str
    clause: Clause
    variants: dict[str, str] | None = None


class Source(BaseModel):
    title: str
    url: str


class Jurisdiction(BaseModel):
    province: str
    provider_type: str
    grid_year: int


class RulePack(BaseModel):
    id: str
    version: str
    payer: str
    jurisdiction: Jurisdiction
    effective_from: date
    verified_on: date
    sources: dict[str, Source]
    schedule: Schedule
    assertion_criteria: dict[str, AssertionCriterion]
    requirements: list[Requirement]
    content_hash: str | None = None  # sha256 of the YAML bytes, set by the loader

    @model_validator(mode="after")
    def _lint(self) -> RulePack:
        ids = [r.id for r in self.requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate requirement ids")
        for r in self.requirements:
            _check_clause_sources(r.clause, self.sources, r.id)
            for f in _finds(r.satisfied_by):
                if f.artifact_type == ArtifactType.CLINICIAN_ASSERTION:
                    if f.criterion not in self.assertion_criteria:
                        raise ValueError(f"{r.id}: unknown assertion criterion {f.criterion!r}")
            for e in r.escalations:
                if e.demand not in _option_ids(r.satisfied_by) and e.demand != "sextant_perio_charting":
                    raise ValueError(f"{r.id}: escalation {e.id} demands unknown option {e.demand!r}")
        return self

    def requirement(self, rid: str) -> Requirement:
        return next(r for r in self.requirements if r.id == rid)


def _check_clause_sources(c: Clause, sources: dict[str, Source], rid: str) -> None:
    if c.source not in sources:
        raise ValueError(f"{rid}: clause cites unknown source {c.source!r}")
    if c.also:
        _check_clause_sources(c.also, sources, rid)


def _finds(p: Predicate) -> list[Find]:
    if isinstance(p, FindP):
        return [p.find]
    if isinstance(p, OneOf):
        return [f for o in p.one_of for f in _finds(o.predicate())]
    if isinstance(p, RequireAll):
        return [f for q in p.require_all for f in _finds(q)]
    return []


def _option_ids(p: Predicate) -> set[str]:
    if isinstance(p, OneOf):
        return {o.id for o in p.one_of}
    return set()


Option.model_rebuild()
RequireAll.model_rebuild()
OneOf.model_rebuild()
EscalationWhen.model_rebuild()
