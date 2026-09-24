"""Narrative drafter and grounding validator.

The narrative is a template over the case, not generated prose. Ophi restates the clinician's
chart entries verbatim with a pointer to each and describes documentation against cited rules. It
never states a diagnosis, prognosis or anything about payer behaviour (PLAN.md, "The copy law").

Format contract (consumed by `parse_narrative` for DOCX/PDF rendering): line 1 title, line 2 subtitle,
`N. Heading` section headings, quotes wrapped in curly quotes on their own paragraph followed by an
attribution line starting with an em dash, bullets starting with `- `.
"""

from __future__ import annotations

import re
from datetime import date

from ophi.assertions.criteria import extensively_restored_variant
from ophi.cdm.models import (
    ArtifactType, AssertionPayload, Case, ChartArtifact, ExtractedDetailPayload, Notation, NotePayload,
    ProcedureHistoryItem, ToothRef, TxPlanPayload,
)
from ophi.dental import notation
from ophi.engine.models import Assessment, RequirementResult, Status
from ophi.packet.labels import evidence_label, fmt_date
from ophi.rules.schema import Clause, RulePack

QUOTE_OPEN, QUOTE_CLOSE = "“", "”"
DASH = "—"
NO_FINDINGS = ("No clinical findings have been confirmed for inclusion. The treating dentist should add findings "
               "from the chart before submission.")
NO_ASSERTIONS = "No clinician assertions recorded."
FORBIDDEN_PHRASES = ("will be approved", "approved", "eligible", "covered", "medically necessary",
                     "requires a crown", "is necessary")

_QUOTE_RE = re.compile(f"{QUOTE_OPEN}(.*?){QUOTE_CLOSE}", re.S)
_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_TOOTH_RE = re.compile(r"#(\d{2})\b")
_HEADING_RE = re.compile(r"^\d\. \S")

_VARIANT_NAMES = {"anterior": "anterior tooth", "posterior_endo": "posterior tooth, endodontically treated",
                  "posterior_non_endo": "posterior tooth, not endodontically treated"}


# --- drafting -------------------------------------------------------------------------------------


def draft_narrative(case: Case, assessment: Assessment, pack: RulePack) -> str:
    lines = [
        "Preauthorization documentation narrative",
        f"Reference {assessment.assessment_id} {DASH} {case.clinic} {DASH} prepared {fmt_date(assessment.submission_date_assumed)}",
        "",
        *_section_treatment(case),
        "",
        *_section_plan_status(case),
        "",
        *_section_findings(case),
        "",
        *_section_assertions(case, pack),
        "",
        *_section_documentation(case, assessment),
        "",
        *_footer(assessment, pack),
    ]
    return "\n".join(lines).rstrip() + "\n"


def _section_treatment(case: Case) -> list[str]:
    t = case.treatment
    tooth = t.tooth
    out = [
        "1. Proposed treatment",
        f"Procedure {t.code} {DASH} {t.description or 'no PMS description on file'}.",
        f"Tooth #{tooth.tooth_fdi} (FDI{_as_written(tooth)}), the {notation.describe(tooth.tooth_fdi)}.",
    ]
    if t.surfaces:
        out.append(f"Surfaces: {', '.join(t.surfaces)}.")
    licence = f", licence {t.provider.licence}" if t.provider.licence else ""
    out.append(f"Provider: {t.provider.name}{licence}.")
    out.append(f"Planned date: {fmt_date(t.planned_date)}. Appointment: {fmt_date(t.appointment_date)}.")
    if t.lab_codes:
        out.append(f"Lab codes: {', '.join(t.lab_codes)}.")
    return out


def _as_written(tooth: ToothRef) -> str:
    """Only worth stating when the PMS charted the tooth in a different notation."""
    if tooth.notation_declared == Notation.FDI:
        return ""
    return f"; charted as {tooth.tooth_as_written} in {tooth.notation_declared.value} notation"


def _history_line(h: ProcedureHistoryItem) -> str:
    tooth = f" #{h.tooth_fdi}" if h.tooth_fdi else ""
    surfaces = f" ({','.join(h.surfaces)})" if h.surfaces else ""
    desc = f" {DASH} {h.description}" if h.description else ""
    return f"- {h.code}{tooth}{surfaces}, {fmt_date(h.performed_on)}{desc}"


def _section_plan_status(case: Case) -> list[str]:
    out = ["2. Treatment plan status"]
    completed = [h for h in case.procedure_history if h.status == "completed"]
    planned = [h for h in case.procedure_history if h.status == "planned"]
    out.append("Completed treatment on record:" if completed else "No completed treatment on record.")
    out += [_history_line(h) for h in completed]
    out.append("Other planned treatment on record:" if planned else "No other planned treatment on record.")
    out += [_history_line(h) for h in planned]
    for a in case.artifacts_of(ArtifactType.TX_PLAN):
        p = a.payload
        assert isinstance(p, TxPlanPayload)
        pending = ", ".join(p.pending_codes) or "none"
        done = ", ".join(p.completed_codes) or "none"
        out.append(f"Treatment plan {a.artifact_id} dated {fmt_date(a.captured_at)}: pending {pending}; completed {done}.")
    return out


def _attribution(note: ChartArtifact | None, fallback_date: date | None, suffix: str = "") -> str:
    d = fmt_date(note.captured_at if note else fallback_date)
    author = (note.payload.author if note and isinstance(note.payload, NotePayload) else None) or "author not recorded"
    return f"{DASH} clinical note dated {d}, {author}{suffix}"


def _section_findings(case: Case) -> list[str]:
    out = ["3. Clinical findings recorded in the chart"]
    tooth = case.requested_tooth
    notes = [n for n in case.artifacts_of(ArtifactType.CLINICAL_NOTE)
             if isinstance(n.payload, NotePayload) and n.payload.signed_off and tooth in n.payload.teeth_fdi]
    quoted_notes = {n.artifact_id for n in notes}
    quotes: list[str] = []
    # (a) confirmed proposals, skipped when their source note is quoted in full below
    for a in case.artifacts_of(ArtifactType.TX_PLAN_DETAILS):
        p = a.payload
        if not isinstance(p, ExtractedDetailPayload) or p.confirmed_by is None or p.rejected:
            continue
        if p.source_artifact_id in quoted_notes:
            continue
        quotes += [f"{QUOTE_OPEN}{p.quote}{QUOTE_CLOSE}",
                   _attribution(case.artifact(p.source_artifact_id), a.captured_at, f"; confirmed by {p.confirmed_by}")]
    # (b) signed-off notes about the requested tooth, in full
    for n in notes:
        assert isinstance(n.payload, NotePayload)
        quotes += [f"{QUOTE_OPEN}{n.payload.text}{QUOTE_CLOSE}", _attribution(n, None)]
    return out + (quotes or [NO_FINDINGS])


def _assertion_lines(a: ChartArtifact, case: Case, pack: RulePack) -> list[str]:
    p = a.payload
    assert isinstance(p, AssertionPayload)
    crit = pack.assertion_criteria.get(p.criterion_id)
    label = crit.label if crit else p.criterion_id
    who = f"{p.asserted_by} ({p.licence})" if p.licence else p.asserted_by
    verb = {"met": "confirmed", "not_applicable": "recorded as not applicable",
            "not_met": "recorded that this criterion is not met"}[p.value]
    cite = f" [{_cite(crit.clause)}]" if crit else ""
    out = [f"{who} {verb} on {fmt_date(p.asserted_at.date())}: {label}.{cite}"]
    if crit and crit.variants:
        key = extensively_restored_variant(case)
        if key in crit.variants:
            out.append(f"  Definition applied ({_VARIANT_NAMES.get(key, key)}): {crit.variants[key]}")
    if p.note:
        out.append(f"  Clinician note: {p.note}")
    return out


def _section_assertions(case: Case, pack: RulePack) -> list[str]:
    out = ["4. Clinician assessment of CDCP crown criteria"]
    assertions = case.artifacts_of(ArtifactType.CLINICIAN_ASSERTION)
    if not assertions:
        return out + [NO_ASSERTIONS]
    for a in assertions:
        out += _assertion_lines(a, case, pack)
    return out


def _cite(c: Clause) -> str:
    s = f"{c.source} {c.ref}"
    return f"{s}; also {_cite(c.also)}" if c.also else s


def _documentation_line(r: RequirementResult, case: Case) -> str:
    docs = [e for e in r.evidence if e.type != ArtifactType.CLINICIAN_ASSERTION.value]
    if docs:
        evidence = "; ".join(evidence_label(e, case) for e in docs)
    else:
        evidence = "clinician assertions recorded in section 4"
    risk = f" Risk noted: {r.risk_reason}" if r.status == Status.AT_RISK and r.risk_reason else ""
    return f"- {r.label}: {evidence}. Rule {r.requirement_id}; {_cite(r.clause)}.{risk}"


def _section_documentation(case: Case, assessment: Assessment) -> list[str]:
    out = ["5. Supporting documentation"]
    for r in assessment.requirements:
        if r.applicable and r.status in (Status.SATISFIED, Status.AT_RISK) and r.evidence:
            out.append(_documentation_line(r, case))
    if len(out) == 1:
        out.append("No requirement is currently supported by documentation on record.")
    return out


def _footer(assessment: Assessment, pack: RulePack) -> list[str]:
    h = (pack.content_hash or assessment.ruleset.content_hash).removeprefix("sha256:")[:12]
    out = [
        f"Prepared with Ophi for review by the treating provider. Documentation completeness assessed against "
        f"{pack.id} {pack.version} (content hash {h}) on {fmt_date(assessment.submission_date_assumed)}. "
        f"The treating dentist is solely responsible for clinical content and the decision to submit.",
    ]
    return out


# --- validation -----------------------------------------------------------------------------------


def case_dates(case: Case) -> set[date]:
    """Every date the chart actually contains; the narrative may not mention any other."""
    ds: set[date | None] = {case.as_of, case.patient.dob, case.treatment.planned_date, case.treatment.appointment_date}
    ds |= {h.performed_on for h in case.procedure_history}
    for a in case.artifacts:
        ds |= {a.captured_at, a.recorded_at}
        if isinstance(a.payload, AssertionPayload):
            ds.add(a.payload.asserted_at.date())
    return {d for d in ds if d is not None}


def case_teeth(case: Case) -> set[int]:
    teeth = {case.requested_tooth} | set(case.dentition.teeth) | set(case.dentition.restored_surfaces) | case.dentition.endo_treated
    teeth |= {h.tooth_fdi for h in case.procedure_history if h.tooth_fdi}
    for a in case.artifacts:
        teeth |= set(a.teeth_fdi)
    return teeth


def _quote_sources(case: Case) -> list[str]:
    out = [a.payload.text for a in case.artifacts_of(ArtifactType.CLINICAL_NOTE) if isinstance(a.payload, NotePayload)]
    out += [a.payload.quote for a in case.artifacts_of(ArtifactType.TX_PLAN_DETAILS)
            if isinstance(a.payload, ExtractedDetailPayload) and a.payload.confirmed_by and not a.payload.rejected]
    return out


def validate_narrative(text: str, case: Case) -> list[str]:
    """Deterministic grounding check. Empty list means clean; this is a safety control, not a style check."""
    violations: list[str] = []
    allowed_dates = {d.isoformat() for d in case_dates(case)}
    violations += [f"date {d} does not appear in the case" for d in sorted(set(_DATE_RE.findall(text))) if d not in allowed_dates]
    allowed_teeth = case_teeth(case)
    violations += [f"tooth #{t} does not appear in the case" for t in sorted(set(_TOOTH_RE.findall(text))) if int(t) not in allowed_teeth]
    sources = _quote_sources(case)
    for q in _QUOTE_RE.findall(text):
        if not any(q in s for s in sources):
            violations.append(f"quote is not verbatim from a note or confirmed proposal: {q[:60]!r}")
    # The copy law governs Ophi's own voice; verbatim chart quotes are the clinician's words.
    own_voice = _QUOTE_RE.sub("", text)
    for phrase in FORBIDDEN_PHRASES:
        if re.search(rf"\b{re.escape(phrase)}\b", own_voice, re.I):
            violations.append(f"forbidden phrase: {phrase!r}")
    return violations


# --- structure for renderers ----------------------------------------------------------------------


def parse_narrative(text: str) -> list[tuple[str, str]]:
    """Split the plain text into (kind, text) blocks: title, subtitle, heading, quote, attribution, bullet, body."""
    blocks: list[tuple[str, str]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if not blocks:
            blocks.append(("title", line))
        elif len(blocks) == 1 and blocks[0][0] == "title":
            blocks.append(("subtitle", line))
        elif line.startswith(QUOTE_OPEN):
            buf = [line]
            while QUOTE_CLOSE not in buf[-1] and i + 1 < len(lines):
                i += 1
                buf.append(lines[i])
            blocks.append(("quote", "\n".join(buf).strip(QUOTE_OPEN + QUOTE_CLOSE)))
        elif line.startswith(DASH + " "):
            blocks.append(("attribution", line))
        elif _HEADING_RE.match(line):
            blocks.append(("heading", line))
        elif line.lstrip().startswith("- "):
            blocks.append(("bullet", line.lstrip()[2:]))
        else:
            blocks.append(("body", line.strip()))
        i += 1
    return blocks
