"""The plan §5 fixer with a stand-in scorer: which fixes it proposes, how it ranks them, and the after-fixes level."""

from __future__ import annotations

import copy

from ophi.engine.models import Status
from ophi.outcomes.fixer import plan_fixes
from ophi.outcomes.risk import Score
from ophi.outcomes.training_set import NOTE_QUESTIONS, assess_sent, case_for, load_examples
from ophi.packet.narrative import validate_narrative
from ophi.rules.loader import default_pack

EXAMPLES = {e.preauth_id: e for e in load_examples()}
PACK = default_pack()


class FakeScorer:
    """Risk rises with each requirement the engine finds unmet; Laya's note answers are fixed per test."""
    label = {"laya": "fake", "risk": "fake"}

    def __init__(self, **note: float):
        self.note = {q: 0.1 for q in NOTE_QUESTIONS} | {"extensively_restored": 0.9} | note

    def score(self, requests, pack, clinic_denial_rate=None):
        out = []
        for e in requests:
            unmet = sum(r.status == Status.UNSATISFIED for r in assess_sent(e, pack).requirements)
            out.append(Score(p_denied=min(0.95, 0.3 + 0.15 * unmet), note=self.note, drivers=[("verdict", 0.2)]))
        return out


def test_worked_example_gets_the_lab_code_bitewings_and_the_dentists_call():
    e = EXAMPLES["PA-SYN-300010"]  # docs/plan/05-outcomes-learning.md §7 step 5
    before = copy.deepcopy(e.sent)
    plan = plan_fixes(e.sent, e.submitted_on, PACK, FakeScorer(extensively_restored=0.1), request_id=e.preauth_id)
    fixes = {f.id: f for f in plan.fixes}
    assert plan.fixes[0].id == "lab_codes_current" and fixes["lab_codes_current"].patch == {"lab_codes": ["99112"]}
    assert fixes["radiograph_bw"].kind == "task" and fixes["radiograph_bw"].risk_drop > 0
    assert fixes["extensively_restored"].kind == "dentist" and fixes["extensively_restored"].concern == "clinical"
    assert (plan.now.score, plan.now.level) == (0.6, "medium") and plan.after_fixes.because == "clinical"  # 2 unmet
    assert "claim_form" not in fixes  # exports never carry the client ID; the real Case checks it
    assert validate_narrative(fixes["narrative"].patch["narrative"], case_for(e)) == []  # grounded, copy-law clean
    assert e.sent == before  # what-ifs work on copies


def test_timing_concern_caps_after_fixes_at_medium():
    e = EXAMPLES["PA-SYN-300000"]  # root canal on #46 in the plan
    sent = copy.deepcopy(e.sent)
    sent["prior_history"] |= {"same_tooth_crown_months_ago": None, "same_code_last_5y": False}  # drop the frequency problem
    plan = plan_fixes(sent, e.submitted_on, PACK, FakeScorer(endo_not_healed=0.9), request_id=e.preauth_id)
    endo = next(f for f in plan.fixes if f.id == "endo_healed")
    assert endo.wait and endo.patch["added_attachments"][0]["type"] == "periapical_radiograph"
    assert plan.after_fixes.because == "timing" and plan.after_fixes.level != "high"
    assert plan.remaining.startswith("Timing: Wait for #46")


def test_a_fix_never_reads_as_adding_risk():
    class NarrativeLooksWorse(FakeScorer):  # the kind of noise a small tree produces
        def score(self, requests, pack, clinic_denial_rate=None):
            return [s.model_copy(update={"p_denied": s.p_denied + (0.2 if e.sent["narrative"] else 0.0)})
                    for e, s in zip(requests, super().score(requests, pack, clinic_denial_rate))]

    e = EXAMPLES["PA-SYN-300010"]
    plan = plan_fixes(e.sent, e.submitted_on, PACK, NarrativeLooksWorse(), request_id=e.preauth_id)
    assert next(f for f in plan.fixes if f.id == "narrative").risk_drop == 0.0
    assert plan.after_fixes.score <= plan.now.score


def test_a_note_answer_with_no_concern_is_never_named_as_a_driver():
    class NoisyDriver(FakeScorer):  # root canal answer says "fine", but the tree still pushes on it
        def score(self, requests, pack, clinic_denial_rate=None):
            return [s.model_copy(update={"p_denied": 0.6, "drivers": [("laya_endo_not_healed", 0.3), ("pa_age_days", 0.1)]})
                    for s in super().score(requests, pack, clinic_denial_rate)]

    e = EXAMPLES["PA-SYN-300013"]
    plan = plan_fixes(e.sent, e.submitted_on, PACK, NoisyDriver(endo_not_healed=0.03, extensively_restored=0.9), request_id=e.preauth_id)
    assert [d.feature for d in plan.drivers] == ["pa_age_days"]
    assert "root canal" not in plan.remaining
