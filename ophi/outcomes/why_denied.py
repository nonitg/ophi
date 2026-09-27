"""What went wrong on a denied request, and what changed on the one that followed.

Sun Life names a reason; denial_map.yaml says which pack requirements that reason points at. Reading the
assessment of the request that was actually sent against those requirements answers the question staff ask
first -- was this a gap Ophi flagged and we sent anyway, or one Ophi read as satisfied? The second case is a
pack blind spot, and saying so plainly is the point: it is what earns the next rule change.
"""

from __future__ import annotations

from pydantic import BaseModel

from ophi.engine.models import Assessment, RequirementResult, Status
from ophi.outcomes.denial_map import requirements_for
from ophi.rules.schema import RulePack

# The requirement was not met when the request went out, so the denial is explained by what was sent.
SHORT_OF = {Status.UNSATISFIED, Status.INDETERMINATE, Status.AT_RISK, Status.PENDING_CONFIRMATION}


class Criterion(BaseModel):
    requirement_id: str
    label: str
    status: Status
    detail: str
    short: bool  # the packet fell short of this one when it was sent


class DenialReading(BaseModel):
    reason_key: str | None
    criteria: list[Criterion]
    mapped: bool  # the SME has reviewed this reason code against the pack

    @property
    def foreseen(self) -> list[Criterion]:
        """Criteria Ophi had already read as short. The denial is explained."""
        return [c for c in self.criteria if c.short]

    @property
    def blind_spot(self) -> bool:
        """Sun Life denied on criteria Ophi read as satisfied: the pack, not the packet, is what missed."""
        return self.mapped and bool(self.criteria) and not self.foreseen

    @property
    def unexplained(self) -> bool:
        """No reason named, or no reviewed mapping for it -- Ophi cannot say which criterion was at issue."""
        return not self.mapped or not self.criteria


def _criterion(r: RequirementResult) -> Criterion:
    return Criterion(requirement_id=r.requirement_id, label=r.label, status=r.status,
                     detail=r.detail or r.explanation, short=r.applicable and r.status in SHORT_OF)


def explain_denial(a: Assessment, reason_key: str | None, pack: RulePack) -> DenialReading:
    """Read the sent request against the criteria Sun Life's reason points at."""
    rids = requirements_for(reason_key, pack)
    if rids is None:
        return DenialReading(reason_key=reason_key, criteria=[], mapped=False)
    found = [r for rid in rids if (r := a.requirement(rid)) is not None]
    return DenialReading(reason_key=reason_key, criteria=[_criterion(r) for r in found], mapped=True)


class Change(BaseModel):
    requirement_id: str
    label: str
    before: Status
    after: Status

    @property
    def fixed(self) -> bool:
        return self.before in SHORT_OF and self.after not in SHORT_OF


def changes_between(before: Assessment, after: Assessment) -> list[Change]:
    """Requirements that read differently on two attempts at the same case. With the first attempt's denial and
    the second's decision, this is the counterfactual the clinic wants: the change that turned it around."""
    out = []
    for r in after.requirements:
        prev = before.requirement(r.requirement_id)
        if prev is not None and prev.status != r.status:
            out.append(Change(requirement_id=r.requirement_id, label=r.label, before=prev.status, after=r.status))
    return out
