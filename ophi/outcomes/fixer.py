"""What to fix before a crown request goes to Sun Life, ranked by how much denial risk each fix removes
(docs/plan/05-outcomes-learning.md §5).

1. Diagnose: score the request as it stands.
2. What-if: re-score a copy with each fix applied, then with all of them together.
3. Act. Each fix has a kind and names who does it:
   - auto: Ophi applies it (a retired lab code);
   - task: the office does it (take a film, chart perio, finish basic treatment first);
   - draft: the dentist approves a narrative built only from what the chart already says;
   - dentist: a clinical judgment that no paperwork changes.

Fixes come from the rule engine's actions, each with its pack clause, and from Laya's reading of the note
for the criteria the dentist confirms. No fix changes a requirement or a verdict. A what-if assumes a new
film or chart shows nothing new, so "after fixes" is the best case, not a promise.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Protocol

from pydantic import BaseModel, computed_field

from ophi.engine.models import Action, Assessment
from ophi.outcomes.risk import Score
from ophi.outcomes.training_set import Example, assess_sent, case_for, resubmitted
from ophi.packet.narrative import draft_narrative
from ophi.rules.schema import Clause, RulePack

Level = Literal["low", "medium", "high"]
LOW_BELOW, HIGH_FROM = 0.45, 0.70  # P(denied) cut points; see scripts/fix-plan.py --bands for the held-out check
FLAG = 0.5  # Laya is calibrated, so above this the note more likely shows the problem than not

# Criteria the dentist confirms, and the note questions that bear on them: (question, a "yes" is a problem).
READS = {
    "extensively_restored": [("extensively_restored", False)],
    "restorability": [("subgingival_margin", True), ("poor_support", True)],
    "endo_healed": [("endo_not_healed", True)],
    "basic_treatment_complete": [("pending_basic", True)],
}
CONCERN = {"extensively_restored": "doesn't show the tooth is extensively restored",
           "subgingival_margin": "mentions a margin below the gum or crown lengthening",
           "poor_support": "mentions furcation or poor bone support",
           "endo_not_healed": "suggests the root canal is recent or not yet healed",
           "pending_basic": "mentions fillings or scaling still to do"}
# Note questions where "no" is the concern; for the rest, "yes" is.
CONCERN_WHEN_NO = {"extensively_restored", "structure_lost"}
# Exports never carry the CDCP client ID (hashed on ingest), so the claim form is checked on the real Case.
NOT_IN_EXPORTS = {"claim_form"}
# Engine actions that report a real finding, as opposed to something it couldn't check.
FINDING = {"review", "excluded_code"}
# Inputs nobody can change before sending: never offered as "what's left".
NOT_ACTIONABLE = {"clinic_denial_rate", "age_band", "tooth_class", "channel", "verdict"}
NO_PAPERWORK_FIX = {"client_age", "frequency_tooth", "frequency_client", "tooth_eligibility", "schedule"}
DRIVER_LABELS = {
    "verdict": "the rule check's overall result", "tooth_class": "tooth type", "age_band": "patient age", "channel": "how it is sent",
    "pa_age_days": "age of the periapical", "bw_sides": "bitewings sent", "perio_age_days": "age of the perio chart",
    "perio_complete": "a complete perio chart", "max_psr": "highest PSR score", "max_depth_at_tooth": "pocket depths at the tooth",
    "bleeding_at_tooth": "bleeding at the tooth", "furcation_class": "furcation at the tooth", "plan_sent": "treatment plan sent",
    "pending_other": "other treatment pending", "prior_crown_months": "a prior crown on the tooth", "note_chars": "how much the note says",
    "has_narrative": "a narrative", "clinic_denial_rate": "the clinic's recent denials",
    "laya_structure_lost": "what the note says about cusp or incisal-edge loss",
    "laya_extensively_restored": "what the note says about 'extensively restored'",
    "laya_endo_not_healed": "what the note says about root canal healing",
    "laya_pending_basic": "what the note says about pending fillings or scaling",
    "laya_subgingival_margin": "what the note says about the margin",
    "laya_uncovered_indication": "a cracked-tooth, sensitivity or cosmetic reason in the note",
    "laya_poor_support": "what the note says about bone support or furcation",
}
KIND_ORDER = {"auto": 0, "task": 1, "draft": 2, "dentist": 3}


class Fix(BaseModel):
    id: str
    kind: Literal["auto", "task", "draft", "dentist"]
    who: Literal["ophi", "moa", "dentist"]
    title: str
    why: str
    requirement_id: str | None = None
    # None on a dentist item: the rule pack has no clause for it yet. None on a draft: the packet narrative.
    clause: Clause | None = None
    patch: dict | None = None  # in the resubmission `changes` vocabulary; None: nothing to re-score
    risk_drop: float | None = None  # P(denied) removed by this fix alone; orders fixes, never shown
    concern: Literal["clinical", "timing"] | None = None

    @computed_field
    @property
    def wait(self) -> bool:
        """Do it, then submit."""
        return self.concern == "timing"


class Risk(BaseModel):
    level: Level
    score: float  # P(denied); orders and compares, never shown
    because: Literal["clinical", "timing"] | None = None


class Driver(BaseModel):
    feature: str
    push: float  # on the log-odds of denial; positive raises the risk
    label: str


class FixPlan(BaseModel):
    request_id: str
    as_of: date
    model: dict[str, str]
    now: Risk
    after_fixes: Risk
    remaining: str
    fixes: list[Fix]
    note_answers: dict[str, float]
    drivers: list[Driver]


class Scorer(Protocol):
    label: dict[str, str]

    def score(self, requests: list[Example], pack: RulePack, clinic_denial_rate: float | None = None) -> list[Score]: ...


def plan_fixes(sent: dict, as_of: date, pack: RulePack, model: Scorer, clinic_denial_rate: float | None = None,
               request_id: str = "request") -> FixPlan:
    base = Example(preauth_id=request_id, clinic="", submitted_on=as_of, decided_on=None, sent=sent)
    [now] = model.score([base], pack, clinic_denial_rate)
    fixes = candidate_fixes(base, assess_sent(base, pack), pack, now.note)
    patched = [f for f in fixes if f.patch]
    scores = model.score([with_fixes(base, [f]) for f in patched] + [with_fixes(base, patched)], pack, clinic_denial_rate) if patched else []
    # A what-if assumes the new document shows nothing new, so a fix can't add risk: a modeled rise is noise
    # from a small tree, floored at zero. A zero drop means the model can't see an effect, not that the rules
    # don't require the fix.
    for f, s in zip(patched, scores):
        f.risk_drop = round(max(0.0, now.p_denied - s.p_denied), 4)
    after = scores[-1] if patched else now
    # Auto fixes cost nothing, so they lead; the rest by risk removed.
    fixes.sort(key=lambda f: (f.kind != "auto", f.risk_drop is None, -(f.risk_drop or 0.0), KIND_ORDER[f.kind]))
    after_risk = _after(min(now.p_denied, after.p_denied), fixes)
    return FixPlan(request_id=request_id, as_of=as_of, model=model.label, now=Risk(level=level(now.p_denied), score=round(now.p_denied, 4)),
                   after_fixes=after_risk, remaining=_remaining(after_risk, after, fixes, pack), fixes=fixes,
                   note_answers={q: round(p, 4) for q, p in now.note.items()},
                   drivers=[_driver(f, v, pack) for f, v in now.drivers if not _misleading(f, v, now.note)])


def level(p_denied: float) -> Level:
    return "low" if p_denied < LOW_BELOW else "high" if p_denied >= HIGH_FROM else "medium"


def with_fixes(e: Example, fixes: list[Fix]) -> Example:
    """A copy of the request with each fix's patch applied, as a resubmission would carry it."""
    sent = e.sent
    for f in fixes:
        sent = resubmitted(sent, {"submitted_date": str(e.submitted_on), "changes": f.patch})
    return e.model_copy(update={"sent": sent})


def candidate_fixes(e: Example, a: Assessment, pack: RulePack, note: dict[str, float]) -> list[Fix]:
    """One fix per engine action, shaped by Laya's reading where the dentist confirms a criterion; plus a
    narrative draft when none was sent, and a dentist item for an indication the pack has no clause for."""
    fixes = [_from_action(act, e, pack, note) for act in a.actions if act.unblocks[0] not in NOT_IN_EXPORTS]
    if not e.sent["narrative"]:
        fixes.append(Fix(id="narrative", kind="draft", who="dentist", title="Add a narrative for the dentist to approve",
                         why="It restates the chart's own entries and the documentation against each CDCP rule; the dentist edits and signs it.",
                         patch={"narrative": draft_narrative(case_for(e), a, pack)}))
    if note["uncovered_indication"] >= FLAG:
        fixes.append(Fix(id="uncovered_indication", kind="dentist", who="dentist", concern="clinical",
                         title="The note gives a cracked-tooth, sensitivity or cosmetic reason for the crown",
                         why="This is Laya's reading of the note; the rule pack has no clause for it yet. The dentist decides."))
    return fixes


def _from_action(act: Action, e: Example, pack: RulePack, note: dict[str, float]) -> Fix:
    rid = act.unblocks[0]
    req = pack.requirement(rid) if rid != "schedule" else None
    base = {"id": rid, "requirement_id": rid if req else None, "clause": req.clause if req else None, "title": act.title, "why": act.why}
    s, as_of, tooth = e.sent, str(e.submitted_on), int(e.sent["services"][0]["tooth"])
    if rid == "lab_codes_current":
        swap = {r.code: r.replaced_by for r in pack.schedule.retired_codes}
        old = s["services"][0].get("lab_codes") or []
        new = [swap.get(c, c) for c in old]
        return Fix(**base | {"title": f"Swap retired lab code {', '.join(c for c in old if c in swap)} for {', '.join(new)}"},
                   kind="auto", who="ophi", patch={"lab_codes": new})
    if rid in ("radiograph_pa", "radiograph_bw", "perio_chart", "tx_plan_details"):
        return Fix(**base, kind="task", who="moa", patch=_document(rid, s, as_of))
    if act.action_type == "criterion_not_met":  # the dentist has answered; Laya's reading never overrides it
        return Fix(**base, kind="dentist", who="dentist", concern="clinical")
    if rid in READS:
        worst, q = max((note[q] if yes_is_problem else 1 - note[q], q) for q, yes_is_problem in READS[rid])
        if rid == "basic_treatment_complete":
            done = [{"code": p["code"], "tooth": p["tooth"], "date": as_of} for p in (s["treatment_plan"] or {}).get("pending", [])
                    if p["code"] != s["services"][0]["procedure_code"]]
            if done or worst >= FLAG:
                why = act.why + (f" The note {CONCERN[q]}." if worst >= FLAG else "")
                return Fix(**base | {"title": "Finish the pending fillings or scaling first", "why": why}, kind="task", who="moa",
                           patch={"completed_treatment": done} if done else None, concern="timing")
        if worst < FLAG:
            return Fix(**base | {"why": f"Laya's reading of the note raises no concern here. {act.why}"}, kind="dentist", who="dentist")
        if rid == "endo_healed":
            return Fix(**base | {"title": f"Wait for #{tooth}'s root canal to heal, then take a new periapical",
                                 "why": f"The note {CONCERN[q]}. {act.why}"},
                       kind="task", who="dentist", concern="timing", patch=_document("radiograph_pa", s, as_of))
        return Fix(**base | {"title": f"The note {CONCERN[q]} (#{tooth})",
                             "why": "Paperwork won't change this; the dentist decides."
                                    + (" If it isn't met, discuss a large filling with the patient instead." if rid == "extensively_restored" else "")},
                   kind="dentist", who="dentist", concern="clinical")
    if rid in NO_PAPERWORK_FIX or act.effort == "clinical":
        return Fix(**base, kind="dentist", who="dentist", concern="clinical" if act.action_type in FINDING else None)
    return Fix(**base, kind="task", who="moa")


def _document(rid: str, s: dict, as_of: str) -> dict:
    """The document the task adds, dated today; a new chart's values are unknown until it is taken."""
    if rid == "radiograph_pa":
        return {"added_attachments": [{"type": "periapical_radiograph", "count": 1, "captured_date": as_of}]}
    if rid == "radiograph_bw":
        return {"added_attachments": [{"type": "bitewing_radiographs", "count": 2, "captured_date": as_of}]}
    if rid == "perio_chart":
        return {"added_attachments": [{"type": "periodontal_charting", "count": 1, "captured_date": as_of}],
                "perio_summary": {"chart_type": "complete", "captured_date": as_of, "psr": (s["perio_summary"] or {}).get("psr"),
                                  "tooth_sites_mm": None, "bop_at_tooth": None, "furcation_class": None}}
    svc = s["services"][0]
    return {"treatment_plan": s["treatment_plan"] or {"pending": [{"code": svc["procedure_code"], "tooth": int(svc["tooth"])}], "completed": []}}


def _after(p_denied: float, fixes: list[Fix]) -> Risk:
    """Plan §5.1: a clinical concern stays whatever the score says; a timing concern resolves by waiting, so
    it caps the level at medium."""
    because = "clinical" if any(f.concern == "clinical" for f in fixes) else "timing" if any(f.wait for f in fixes) else None
    lv = level(p_denied)
    if because == "timing" and lv == "high":
        lv = "medium"
    return Risk(level=lv, score=round(p_denied, 4), because=because)


def _remaining(after: Risk, score: Score, fixes: list[Fix], pack: RulePack) -> str:
    if after.because == "clinical":
        return f"{next(f.title for f in fixes if f.concern == 'clinical')}. Paperwork won't change this; the dentist decides."
    if after.because == "timing":
        return f"Timing: {next(f.title for f in fixes if f.wait)}. Send after that."
    if after.level == "low":
        return "Nothing major left once these are done."
    up = [f for f, v in score.drivers if v > 0 and f not in NOT_ACTIONABLE and not _misleading(f, v, score.note)]
    return f"Most of what's left: {_label(up[0], pack)}." if up else "Nothing on the request itself stands out."


def _misleading(feature: str, push: float, note: dict[str, float]) -> bool:
    """A note answer on the no-concern side that still pushes risk up: the tree's noise, and read aloud it
    would suggest a problem the note doesn't show."""
    q = feature.removeprefix("laya_")
    if q == feature or push <= 0:
        return False
    return note[q] >= FLAG if q in CONCERN_WHEN_NO else note[q] < FLAG


def _driver(feature: str, push: float, pack: RulePack) -> Driver:
    return Driver(feature=feature, push=round(push, 4), label=_label(feature, pack))


def _label(feature: str, pack: RulePack) -> str:
    if feature.startswith("req_"):
        return pack.requirement(feature.removeprefix("req_")).label
    return DRIVER_LABELS.get(feature, feature)
