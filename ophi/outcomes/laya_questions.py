"""The questions Laya is fine-tuned on and asked at run time, in laya's question format, and the gold answer
for each one an example has a label for. Training and evaluation share them so both see the same wording
and option order (docs/plan/05-outcomes-learning.md §4.2).
"""

from __future__ import annotations

from ophi.outcomes.training_set import NOTE_QUESTIONS, VAGUE, Example, note_labels

# Yes/no is asked as a two-option choice with neutral keys: on the base checkpoint a noul answer can
# follow its own true/false labels instead of the text (laya issue #156).
YES, NO = "A", "B"
DECISION, APPROVED, OTHER = "decision", "approved", "other"
# Sun Life reason codes as short option keys: all options must fit the 192-token question head.
REASON_KEYS = {
    "DOC_MISSING_RADIOGRAPH": "missing_radiograph", "DOC_RADIOGRAPH_STALE": "stale_radiograph",
    "DOC_MISSING_PERIO_CHART": "missing_perio_chart", "DOC_INSUFFICIENT_NOTES": "insufficient_notes",
    "FREQ_LIMIT": "frequency_limit", "ELIGIBILITY": "client_ineligible", "TOOTH_INELIGIBLE": "tooth_ineligible",
    "DUPLICATE_REQUEST": "duplicate_request", "ADMIN_INVALID_CODE": "invalid_lab_code",
    "CLIN_ACTIVE_DISEASE": "basic_treatment_pending", "CLIN_NOT_EXT_RESTORED": "not_extensively_restored",
    "CLIN_ENDO_NOT_HEALED": "endo_not_healed", "CLIN_PERIO_PROGNOSIS": "perio_prognosis",
    "CLIN_FERRULE": "insufficient_ferrule", "CLIN_NOT_COVERED_INDICATION": "indication_not_covered",
    "CLIN_NEED_NOT_MET": "need_not_met",
}
DECISION_KEYS = [APPROVED, *REASON_KEYS.values(), OTHER]

QUESTIONS = {q: {"type": "choice", "instructions": text, "criteria": {YES: "yes", NO: "no"}}
             for q, (text, _) in NOTE_QUESTIONS.items()}
QUESTIONS[DECISION] = {"type": "choice", "instructions": "What will Sun Life decide on this CDCP crown preauthorization?",
                       "criteria": DECISION_KEYS}


def decision_key(code: str) -> str:
    return APPROVED if code == APPROVED else REASON_KEYS.get(code, OTHER)


def gold(e: Example) -> dict[str, list[float]]:
    """Target distribution, in option order, for each question this example has a label for. A vague
    letter gives no decision label, as it wouldn't in real data."""
    out = {q: [1.0, 0.0] if yes else [0.0, 1.0] for q, yes in (note_labels(e) or {}).items()}
    if e.decision not in (None, VAGUE):
        out[DECISION] = [float(k == decision_key(e.decision)) for k in DECISION_KEYS]
    return out
