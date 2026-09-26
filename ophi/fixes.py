"""Chart gaps Ophi can close itself, because the rule pack fixes the right value and no one's judgment is
involved. Each is keyed by the requirement it settles. A fix changes what Ophi puts in the packet; the PMS is
never written, so staff use the same value when they send from it.
"""

from __future__ import annotations

from collections.abc import Callable

from ophi.cdm.models import Case
from ophi.engine.models import Assessment
from ophi.rules.schema import RulePack
from ophi.workflow import chart_actions


def _swaps(case: Case, pack: RulePack) -> dict[str, str]:
    retired = {r.code: r.replaced_by for r in pack.schedule.retired_codes}
    return {c: retired[c] for c in case.treatment.lab_codes if c in retired}


def _current_lab_codes(case: Case, pack: RulePack) -> Case:
    swaps = _swaps(case, pack)
    t = case.treatment
    return case.model_copy(update={"treatment": t.model_copy(update={"lab_codes": [swaps.get(c, c) for c in t.lab_codes]})})


def _lab_codes_title(case: Case, pack: RulePack) -> str:
    return "; ".join(f"Replace lab code {old} with {new}" for old, new in _swaps(case, pack).items())


# requirement id -> (apply, the button's words for this case)
SAFE: dict[str, tuple[Callable[[Case, RulePack], Case], Callable[[Case, RulePack], str]]] = {
    "lab_codes_current": (_current_lab_codes, _lab_codes_title),
}


def open_on(a: Assessment) -> list[str]:
    """The case's open chart gaps that Ophi can close itself."""
    return [rid for rid in dict.fromkeys(rid for x in chart_actions(a) for rid in x.unblocks) if rid in SAFE]


def apply(case: Case, requirement_ids, pack: RulePack) -> Case:
    for rid in requirement_ids:
        if rid in SAFE:
            case = SAFE[rid][0](case, pack)
    return case


def title(case: Case, requirement_id: str, pack: RulePack) -> str:
    return SAFE[requirement_id][1](case, pack)
