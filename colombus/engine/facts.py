"""Deterministic predicates over structured case fields (age, tooth, history, plan). No artifacts."""

from __future__ import annotations

from dateutil.relativedelta import relativedelta

from colombus.cdm.models import Availability, Case, Section, ToothState
from colombus.dental import notation
from colombus.engine.models import LeafResult, Shortfall, Status
from colombus.rules.schema import Fact, RulePack


def resolve(f: Fact, case: Case, pack: RulePack) -> LeafResult:
    return _HANDLERS[f.fact](f, case, pack)


def _age_at_least(f: Fact, case: Case, pack: RulePack) -> LeafResult:
    age = case.patient.age_on(case.as_of)
    if age is None:
        return LeafResult(status=Status.INDETERMINATE, shortfall=Shortfall(missing=["date of birth"]), detail="no date of birth on record")
    if age >= (f.years or 0):
        return LeafResult(status=Status.SATISFIED, detail=f"client is {age} on {case.as_of}; criterion is {f.years}+")
    return LeafResult(status=Status.UNSATISFIED, shortfall=Shortfall(detail=f"age {age}"), detail=f"client is {age} on {case.as_of}; CDCP crown criteria apply to clients {f.years}+")


def _tooth_class_in(f: Fact, case: Case, pack: RulePack) -> LeafResult:
    t = case.requested_tooth
    cls = notation.tooth_class(t)
    if cls in (f.classes or []):
        return LeafResult(status=Status.SATISFIED, detail=f"#{t} is the {notation.describe(t)}")
    return LeafResult(status=Status.UNSATISFIED, shortfall=Shortfall(detail=cls), detail=f"#{t} is the {notation.describe(t)}; not in {', '.join(f.classes or [])}")


def _adjacent_molars_missing(f: Fact, case: Case, pack: RulePack) -> LeafResult:
    t = case.requested_tooth
    q = notation.quadrant(t)
    first, second = q * 10 + 6, q * 10 + 7
    if case.assurance_for(Section.DENTITION).availability in (Availability.UNKNOWN, Availability.DEGRADED):
        return LeafResult(status=Status.INDETERMINATE, detail="odontogram not available from the source; cannot confirm #%d and #%d are missing" % (first, second))
    states = {n: case.dentition.state(n) for n in (first, second)}
    if all(s == ToothState.MISSING for s in states.values()):
        return LeafResult(status=Status.SATISFIED, detail=f"#{first} and #{second} are recorded missing")
    present = [f"#{n}" for n, s in states.items() if s != ToothState.MISSING]
    return LeafResult(status=Status.UNSATISFIED, shortfall=Shortfall(detail=", ".join(present)), detail=f"{', '.join(present)} recorded present; the third-molar exception requires both first and second molars missing")


def _code_matches(code: str, f: Fact) -> bool:
    if f.codes:
        return code in f.codes
    return code.startswith(f.prefix or "")


def _family(f: Fact) -> str:
    return "/".join(f.codes) if f.codes else f"{f.prefix}xxx"


def _client_identifiers_present(f: Fact, case: Case, pack: RulePack) -> LeafResult:
    """The claim form needs the client's CDCP identifier and date of birth; Colombus cannot invent them."""
    missing = [x for x, v in (("CDCP client ID", case.patient.cdcp_client_id), ("date of birth", case.patient.dob)) if not v]
    if missing:
        return LeafResult(status=Status.INDETERMINATE, shortfall=Shortfall(missing=missing),
                          detail=f"{' and '.join(missing)} not on file; the claim form cannot be completed")
    return LeafResult(status=Status.SATISFIED, detail="client identifiers on file (CDCP client ID, date of birth)")


def _history_or_indeterminate(case: Case) -> LeafResult | None:
    sa = case.assurance_for(Section.PROCEDURE_HISTORY)
    if sa.availability in (Availability.UNKNOWN, Availability.DEGRADED):
        return LeafResult(status=Status.INDETERMINATE, detail=f"procedure history reported as {sa.availability.value} by the source; frequency cannot be checked")
    return None


def _no_prior_code_on_tooth_within(f: Fact, case: Case, pack: RulePack) -> LeafResult:
    if (r := _history_or_indeterminate(case)):
        return r
    since = case.as_of - relativedelta(months=f.months or 0)
    hits = [h for h in case.procedure_history if h.status == "completed" and _code_matches(h.code, f)
            and h.tooth_fdi == case.requested_tooth and h.performed_on >= since]
    if not hits:
        return LeafResult(status=Status.SATISFIED, detail=f"no completed {_family(f)} on #{case.requested_tooth} since {since}")
    h = max(hits, key=lambda x: x.performed_on)
    return LeafResult(status=Status.UNSATISFIED, shortfall=Shortfall(detail=f"{h.code} on {h.performed_on}"),
                      detail=f"{h.code} completed on #{h.tooth_fdi} on {h.performed_on}, within {f.months} months of {case.as_of}")


def _prior_codes_count_below(f: Fact, case: Case, pack: RulePack) -> LeafResult:
    if (r := _history_or_indeterminate(case)):
        return r
    since = case.as_of - relativedelta(months=f.months or 0)
    hits = [h for h in case.procedure_history if h.status == "completed" and _code_matches(h.code, f) and h.performed_on >= since]
    n = len(hits)
    if n < (f.max_count or 0):
        return LeafResult(status=Status.SATISFIED, detail=f"{n} completed {_family(f)} since {since}; limit is {f.max_count} per {f.months} months")
    return LeafResult(status=Status.UNSATISFIED, shortfall=Shortfall(detail=f"{n} crowns"),
                      detail=f"{n} completed {_family(f)} since {since} ({', '.join(f'{h.code} #{h.tooth_fdi} {h.performed_on}' for h in hits)}); limit is {f.max_count} per {f.months} months")


def _no_pending_codes_with_prefix(f: Fact, case: Case, pack: RulePack) -> LeafResult:
    sa = case.assurance_for(Section.PLANNED)
    if sa.availability in (Availability.UNKNOWN, Availability.DEGRADED):
        return LeafResult(status=Status.INDETERMINATE, detail=f"planned procedures reported as {sa.availability.value}; cannot confirm basic treatment is complete")
    tx = case.treatment
    pend = [h for h in case.procedure_history if h.status == "planned" and any(h.code.startswith(p) for p in (f.prefixes or []))
            and not any(h.code.startswith(x) for x in (f.exclude_prefixes or []))
            and not (f.exclude_requested and h.code == tx.code and h.tooth_fdi == tx.tooth.tooth_fdi)]
    if not pend:
        return LeafResult(status=Status.SATISFIED, detail="no pending basic restorative or periodontal treatment in the plan")
    items = ", ".join(f"{h.code}{' #' + str(h.tooth_fdi) if h.tooth_fdi else ''}" for h in pend)
    return LeafResult(status=Status.UNSATISFIED, shortfall=Shortfall(missing=[f"completion of {items}"], detail=items),
                      detail=f"plan still lists pending basic treatment: {items}")


def _no_retired_codes(f: Fact, case: Case, pack: RulePack) -> LeafResult:
    retired = {r.code: r for r in pack.schedule.retired_codes}
    hits = [retired[c] for c in case.treatment.lab_codes if c in retired]
    if not hits:
        return LeafResult(status=Status.SATISFIED, detail=f"lab codes {', '.join(case.treatment.lab_codes)} are current")
    txt = "; ".join(f"{r.code} was replaced by {r.replaced_by} on 2026-04-01" for r in hits)
    return LeafResult(status=Status.UNSATISFIED, shortfall=Shortfall(missing=[f"replace {', '.join(r.code for r in hits)}"], detail=txt), detail=txt)


_HANDLERS = {
    "age_at_least": _age_at_least,
    "tooth_class_in": _tooth_class_in,
    "adjacent_molars_missing": _adjacent_molars_missing,
    "no_prior_code_on_tooth_within": _no_prior_code_on_tooth_within,
    "prior_codes_count_below": _prior_codes_count_below,
    "no_pending_codes_with_prefix": _no_pending_codes_with_prefix,
    "no_retired_codes": _no_retired_codes,
    "client_identifiers_present": _client_identifiers_present,
}
