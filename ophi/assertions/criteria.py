"""Context for Clinician Assertions: which variant of a criterion applies to this tooth and what the
chart already shows. Shared by the web screen and the packet so the two never disagree.

Ophi never answers these criteria. It only tells the dentist which definition applies and what
the odontogram records, then records the dentist's answer with attribution."""

from __future__ import annotations

from pydantic import BaseModel

from ophi.cdm.models import ArtifactType, AssertionPayload, Case
from ophi.dental import notation
from ophi.rules.schema import RulePack


class CriterionContext(BaseModel):
    criterion_id: str
    label: str
    clause_ref: str
    clause_quote: str | None
    variant_key: str | None = None
    variant_text: str | None = None
    hint: str | None = None  # what the chart already records, for the dentist's reference
    current_value: str | None = None
    asserted_by: str | None = None
    asserted_on: str | None = None
    note: str | None = None


def extensively_restored_variant(case: Case) -> str:
    if notation.is_anterior(case.requested_tooth):
        return "anterior"
    return "posterior_endo" if case.tooth_is_endo_treated() else "posterior_non_endo"


def criterion_context(case: Case, pack: RulePack, criterion_id: str) -> CriterionContext:
    crit = pack.assertion_criteria[criterion_id]
    ctx = CriterionContext(criterion_id=criterion_id, label=crit.label, clause_ref=f"{crit.clause.source} {crit.clause.ref}",
                           clause_quote=crit.clause.quote)
    t = case.requested_tooth
    if criterion_id == "extensively_restored" and crit.variants:
        ctx.variant_key = extensively_restored_variant(case)
        ctx.variant_text = crit.variants.get(ctx.variant_key)
        surfaces = case.dentition.restored_surfaces.get(t)
        if surfaces:
            ctx.hint = f"Odontogram records {''.join(surfaces)} ({len(surfaces)} surfaces) restored on #{t}"
    elif criterion_id == "no_furcation" and notation.tooth_class(t) not in ("molar", "third_molar"):
        ctx.hint = f"#{t} is the {notation.describe(t)}; furcation applies to multi-rooted teeth — 'not applicable' may be the accurate answer"
    elif criterion_id == "endo_healed":
        rct = [h for h in case.procedure_history if h.status == "completed" and h.tooth_fdi == t and h.code.startswith("33")]
        if rct:
            ctx.hint = f"RCT {rct[-1].code} completed on #{t} on {rct[-1].performed_on}"
    elif criterion_id == "active_disease_addressed":
        pending = [h for h in case.procedure_history if h.status == "planned" and h.code != case.treatment.code]
        if pending:
            ctx.hint = "Plan still lists: " + ", ".join(f"{h.code}{' #' + str(h.tooth_fdi) if h.tooth_fdi else ''}" for h in pending)
        else:
            ctx.hint = "No other planned procedures in the chart"
    elif criterion_id == "third_molar_in_occlusion":
        q = notation.quadrant(t)
        ctx.hint = f"Odontogram: #{q}6 {case.dentition.state(q * 10 + 6).value}, #{q}7 {case.dentition.state(q * 10 + 7).value}"

    hits = [a for a in case.artifacts_of(ArtifactType.CLINICIAN_ASSERTION)
            if isinstance(a.payload, AssertionPayload) and a.payload.criterion_id == criterion_id]
    if hits:
        p = max(hits, key=lambda a: a.payload.asserted_at).payload  # type: ignore[attr-defined]
        assert isinstance(p, AssertionPayload)
        ctx.current_value, ctx.asserted_by, ctx.asserted_on, ctx.note = p.value, p.asserted_by, str(p.asserted_at.date()), p.note
    return ctx


def relevant_criteria(case: Case, pack: RulePack) -> list[str]:
    """Criteria referenced by requirements that apply to this case, in pack order."""
    from ophi.engine.evaluate import applies
    from ophi.rules.schema import _finds  # closed vocabulary; walking it is the engine's job

    out: list[str] = []
    for req in pack.requirements:
        if not applies(req, case):
            continue
        for f in _finds(req.satisfied_by):
            if f.artifact_type == ArtifactType.CLINICIAN_ASSERTION and f.criterion and f.criterion not in out:
                out.append(f.criterion)
    # third-molar exception only matters for third molars
    if notation.tooth_class(case.requested_tooth) != "third_molar":
        out = [c for c in out if c != "third_molar_in_occlusion"]
    return out


def all_contexts(case: Case, pack: RulePack) -> list[CriterionContext]:
    return [criterion_context(case, pack, c) for c in relevant_criteria(case, pack)]
