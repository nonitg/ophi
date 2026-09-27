"""Engine invariants over the whole corpus, plus inline single-perturbation cases for behaviours the
snapshot corpus cannot express (evidence details, escalation results, action text, rule boundaries)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from dateutil.relativedelta import relativedelta

from ophi.engine.models import Assessment, Action, Status, Verdict
from ophi.rules.schema import EFFORT_ORDER
from tests._cases import assess_dict, assess_path, corpus_files, ready_dict

CORPUS = corpus_files()
AS_OF = date(2026, 9, 17)


def _dump(a: Assessment) -> str:
    # `assessed_at` is wall-clock by design; `workload.elapsed_ms` is timing. Everything else must be
    # byte-identical run to run (docs/plan/02-reasoning.md §2 stage 5).
    return a.model_dump_json(exclude={"assessed_at": True, "workload": {"elapsed_ms"}})


def _action_key(x: Action, a: Assessment) -> tuple:
    """The ranking key documented in assess.rank_actions: blocking first; within blocking, missing/stale
    evidence before things a human only confirms; then most-unblocking; cheapest effort; requirement id."""
    if x.unblocks == ["schedule"]:
        return (0, 0, -1, EFFORT_ORDER["confirm_in_app"], "0_schedule")
    r = a.requirement(x.unblocks[0])
    assert r is not None
    sev = {Status.UNSATISFIED: 0, Status.INDETERMINATE: 1, Status.PENDING_CONFIRMATION: 2, Status.AT_RISK: 3}[r.status]
    return (0 if x.blocking else 1, sev, -len(x.unblocks), EFFORT_ORDER[x.effort], r.requirement_id)


def _verdict_per_spec(a: Assessment) -> Verdict:
    """docs/plan/02-reasoning.md §4: enum verdict, worst status wins."""
    if a.schedule.disposition == "excluded":
        return Verdict.EXCLUDED_AS_CODED
    if a.schedule.disposition == "not_required":
        return Verdict.PREAUTH_NOT_REQUIRED
    statuses = {r.status for r in a.requirements if r.applicable}
    if Status.UNSATISFIED in statuses:
        return Verdict.BLOCKED
    if statuses & {Status.INDETERMINATE, Status.PENDING_CONFIRMATION} or a.schedule.disposition == "not_in_schedule_b":
        return Verdict.NEEDS_INPUT
    if Status.AT_RISK in statuses:
        return Verdict.READY_WITH_RISKS
    return Verdict.READY_TO_SUBMIT


# --- (a)(b)(f) corpus-wide invariants -----------------------------------------------------------


@pytest.mark.parametrize("path", CORPUS, ids=lambda p: p.stem)
def test_determinism(path: Path):
    a1, a2 = assess_path(path), assess_path(path)
    assert _dump(a1) == _dump(a2)
    assert a1.assessment_id == a2.assessment_id


@pytest.mark.parametrize("path", CORPUS, ids=lambda p: p.stem)
def test_actions_sorted_by_documented_key_with_contiguous_ranks(path: Path):
    a = assess_path(path)
    keys = [_action_key(x, a) for x in a.actions]
    assert keys == sorted(keys)
    assert [x.rank for x in a.actions] == list(range(1, len(a.actions) + 1))
    # Every open applicable requirement is unblocked by exactly one action, and nothing else is.
    open_reqs = sorted(r.requirement_id for r in a.requirements if r.applicable and r.status != Status.SATISFIED)
    assert sorted(rid for x in a.actions for rid in x.unblocks if rid != "schedule") == open_reqs


@pytest.mark.parametrize("path", CORPUS, ids=lambda p: p.stem)
def test_zero_false_satisfied_and_verdict_matches_spec(path: Path):
    a = assess_path(path)
    applicable = [r for r in a.requirements if r.applicable]
    if a.verdict == Verdict.READY_TO_SUBMIT:
        assert all(r.status == Status.SATISFIED for r in applicable)
        assert a.actions == []
    assert a.verdict == _verdict_per_spec(a)
    assert a.completeness == {"satisfied": sum(r.status == Status.SATISFIED for r in applicable), "applicable": len(applicable)}
    for r in a.requirements:
        assert (r.status == Status.NOT_APPLICABLE) == (not r.applicable)
        if r.status == Status.SATISFIED:
            assert r.shortfall.empty, f"{r.requirement_id} satisfied with a non-empty shortfall"
        if r.status == Status.AT_RISK and r.satisfied_via:
            assert r.risk_reason, f"{r.requirement_id} at_risk via {r.satisfied_via} without a risk reason"


# --- baseline ------------------------------------------------------------------------------------


def test_ready_baseline_is_ready_to_submit():
    a = assess_dict(ready_dict())
    assert a.verdict == Verdict.READY_TO_SUBMIT
    assert a.completeness == {"satisfied": 13, "applicable": 13}
    assert a.actions == []
    assert a.requirement("endo_healed").applicable is False
    # Deadlines: every matched dated artifact expires 12 months after capture; sorted deterministically.
    assert a.deadlines
    for d in a.deadlines:
        assert d.expires_on == AS_OF - relativedelta(days=40) + relativedelta(months=12)
    keys = [(d.expires_on, d.requirement_id, d.artifact_id) for d in a.deadlines]
    assert keys == sorted(keys)


# --- (c) absent vs unseen ------------------------------------------------------------------------


def test_imaging_unknown_is_indeterminate_absent_confirmed_is_unsatisfied():
    d = ready_dict()
    d["radiographs"] = []
    d["assurance"] = {"imaging": {"availability": "Unknown", "reason": "imaging tables empty in this install"}}
    a = assess_dict(d)
    assert a.requirement("radiograph_pa").status == Status.INDETERMINATE
    assert a.requirement("radiograph_bw").status == Status.INDETERMINATE
    assert a.verdict == Verdict.NEEDS_INPUT
    pa_action = next(x for x in a.actions if x.unblocks == ["radiograph_pa"])
    assert pa_action.action_type == "check_source" and pa_action.title.startswith("Check the imaging software")
    assert not pa_action.needs_patient  # the film may already be in the imaging software: a desk check first

    d["assurance"] = {"imaging": "AbsentConfirmed"}
    a = assess_dict(d)
    assert a.requirement("radiograph_pa").status == Status.UNSATISFIED
    assert a.requirement("radiograph_bw").status == Status.UNSATISFIED
    assert a.verdict == Verdict.BLOCKED
    pa_action = next(x for x in a.actions if x.unblocks == ["radiograph_pa"])
    assert pa_action.title == "Take a periapical of #46" and pa_action.needs_patient


# --- (d) PSR interim path and escalations --------------------------------------------------------


def _psr_case(scores: dict[str, int], sextant_teeth: dict[int, list[int]] | None = None) -> dict:
    d = ready_dict()
    teeth = {46: [3, 3, 3, 3, 3, 3], **(sextant_teeth or {})}
    d["perio_charts"] = [{"id": "perio_partial", "age": "40d", "full_mouth": False, "teeth": teeth}]
    d["psr"] = [{"id": "psr_1", "age": "40d", "scores": {"S1": 2, "S2": 1, "S3": 2, "S4": 2, "S5": 1, "S6": 2, **scores}}]
    return d


def test_psr_interim_path_is_at_risk_never_satisfied():
    a = assess_dict(_psr_case({}))
    r = a.requirement("perio_chart")
    assert r.status == Status.AT_RISK and r.satisfied_via == "psr_interim_path"
    assert "will be considered" in (r.risk_reason or "")
    assert {e.id: e.fired for e in r.escalations_evaluated} == {"psr_requires_full_chart": False, "psr_requires_sextant_chart": False}
    assert {e.type for e in r.evidence} == {"psr", "perio_chart"}
    assert a.verdict == Verdict.READY_WITH_RISKS
    assert a.verdict != Verdict.READY_TO_SUBMIT
    (act,) = a.actions
    assert act.blocking is False and act.action_type == "review_risk" and act.unblocks == ["perio_chart"]


def test_psr_4_closes_the_interim_path_and_demands_the_complete_chart():
    # Footnote 7: PSR 4 in any sextant -> complete perio chart must be submitted. The escalation in the
    # pack demands the `complete_perio_chart` option, so the near-miss and the action must point there,
    # not at "complete the PSR path".
    a = assess_dict(_psr_case({"S1": 4}))
    r = a.requirement("perio_chart")
    assert r.status == Status.UNSATISFIED
    fired = {e.id: e for e in r.escalations_evaluated if e.fired}
    assert set(fired) == {"psr_requires_full_chart"}
    assert fired["psr_requires_full_chart"].demanded == "complete_perio_chart"
    assert fired["psr_requires_full_chart"].scope == {"sextants": ["S1"]}
    assert r.near_miss_option == "complete_perio_chart"
    act = next(x for x in a.actions if x.unblocks == ["perio_chart"])
    assert act.blocking and act.title == "Complete a 6-site periodontal chart (all present teeth)"
    assert "PSR path" not in act.title
    assert a.verdict == Verdict.BLOCKED


def test_psr_3_in_two_sextants_demands_the_complete_chart():
    a = assess_dict(_psr_case({"S1": 3, "S3": 3}))
    r = a.requirement("perio_chart")
    assert r.status == Status.UNSATISFIED
    assert [e.id for e in r.escalations_evaluated if e.fired] == ["psr_requires_full_chart"]
    assert r.near_miss_option == "complete_perio_chart"
    act = next(x for x in a.actions if x.unblocks == ["perio_chart"])
    assert act.title == "Complete a 6-site periodontal chart (all present teeth)"


def test_psr_3_in_requested_sextant_demands_that_sextant():
    # 46 is in S6. Only 46 charted -> the sextant demand is unmet; the action names the sextant.
    a = assess_dict(_psr_case({"S6": 3}))
    r = a.requirement("perio_chart")
    assert r.status == Status.UNSATISFIED
    fired = {e.id: e for e in r.escalations_evaluated if e.fired}
    assert set(fired) == {"psr_requires_sextant_chart"}
    assert fired["psr_requires_sextant_chart"].scope == {"sextants": ["S6"]}
    assert r.near_miss_option == "psr_interim_path"
    act = next(x for x in a.actions if x.unblocks == ["perio_chart"])
    assert "sextant S6" in act.title and act.title.endswith("to complete the PSR path")

    # Chart the whole sextant (44, 45, 46, 47 present; 48 missing) -> at_risk via the interim path.
    a = assess_dict(_psr_case({"S6": 3}, {t: [3] * 6 for t in (44, 45, 47)}))
    r = a.requirement("perio_chart")
    assert r.status == Status.AT_RISK and r.satisfied_via == "psr_interim_path"
    assert a.verdict == Verdict.READY_WITH_RISKS


def test_both_escalations_fire_full_chart_takes_precedence():
    a = assess_dict(_psr_case({"S1": 3, "S6": 3}, {t: [3] * 6 for t in (44, 45, 47)}))
    r = a.requirement("perio_chart")
    assert r.status == Status.UNSATISFIED
    assert [e.id for e in r.escalations_evaluated] == ["psr_requires_full_chart", "psr_requires_sextant_chart"]
    assert all(e.fired for e in r.escalations_evaluated)
    assert r.near_miss_option == "complete_perio_chart"
    act = next(x for x in a.actions if x.unblocks == ["perio_chart"])
    assert act.title == "Complete a 6-site periodontal chart (all present teeth)"


def test_psr_older_than_12_months_does_not_count():
    d = _psr_case({})
    d["psr"][0]["age"] = "13m"
    a = assess_dict(d)
    r = a.requirement("perio_chart")
    assert r.status == Status.UNSATISFIED
    assert all(not e.fired for e in r.escalations_evaluated)


# --- (e) proposals -------------------------------------------------------------------------------


def _proposal_case() -> dict:
    d = ready_dict()
    d["tx_plans"] = []
    d["notes"] = [{"id": "note_1", "age": "40d", "teeth": [46], "text": "46 fractured lingual cusp on a five-surface amalgam."}]
    d["extracted"] = [{"id": "ext_1", "from": "note_1", "quote": "46 fractured lingual cusp", "claim": "Treatment plan details", "age": "40d"}]
    return d


def test_unconfirmed_proposal_is_pending_and_needs_input():
    a = assess_dict(_proposal_case())
    r = a.requirement("tx_plan_details")
    assert r.status == Status.PENDING_CONFIRMATION and r.satisfied_via == "plan_in_note"
    assert r.evidence[0].confirmed is False and r.evidence[0].quote == "46 fractured lingual cusp"
    assert a.verdict == Verdict.NEEDS_INPUT
    (act,) = a.actions
    assert act.blocking and act.action_type == "confirm_extraction" and act.title.startswith("Confirm:")


def test_confirmed_proposal_is_satisfied():
    d = _proposal_case()
    d["extracted"][0]["confirmed_by"] = "Dr. Priya Lau"
    a = assess_dict(d)
    r = a.requirement("tx_plan_details")
    assert r.status == Status.SATISFIED and r.satisfied_via == "plan_in_note"
    assert a.verdict == Verdict.READY_TO_SUBMIT


def test_heuristic_proposer_end_to_end_yields_pending():
    d = ready_dict()
    d["tx_plans"] = []
    d["notes"] = [{"id": "note_1", "age": "40d", "teeth": [46], "text": "46 fractured lingual cusp. Plan: crown 46."}]
    a = assess_dict(d, with_proposer=True)
    r = a.requirement("tx_plan_details")
    assert r.status == Status.PENDING_CONFIRMATION
    assert r.evidence[0].quote == "Plan: crown 46."
    assert a.verdict == Verdict.NEEDS_INPUT


# --- assertions ----------------------------------------------------------------------------------


def test_not_met_assertion_blocks_with_attributed_action():
    d = ready_dict()
    next(x for x in d["assertions"] if x["criterion"] == "ferrule_1_5mm")["value"] = "not_met"
    a = assess_dict(d)
    r = a.requirement("restorability")
    assert r.status == Status.UNSATISFIED and r.shortfall.not_met_assertions == ["ferrule_1_5mm"]
    assert a.verdict == Verdict.BLOCKED
    (act,) = a.actions
    assert act.action_type == "criterion_not_met"
    assert act.title == "Dentist recorded a criterion as not met: Restorability criteria confirmed by the treating dentist"
    assert "Dr. Priya Lau" in act.why and "Adequate ferrule" in act.why


def test_missing_assertions_are_indeterminate_not_unsatisfied():
    d = ready_dict()
    d["assertions"] = []
    a = assess_dict(d)
    for rid in ("restorability", "extensively_restored", "basic_treatment_complete"):
        assert a.requirement(rid).status == Status.INDETERMINATE
    assert a.requirement("restorability").shortfall.missing_assertions == [
        "no_active_perio", "crown_root_ratio", "no_furcation", "margin_3mm", "ferrule_1_5mm", "mesiodistal_space", "no_adjunctive_needed"]
    assert a.verdict == Verdict.NEEDS_INPUT


# --- rule boundaries (rolling windows, Guide 4.0; age gate, Guide 6.3.5) ---------------------------


def _with_history(*items: dict) -> dict:
    d = ready_dict()
    d["history"] += list(items)
    return d


def test_frequency_tooth_96_months_is_rolling_and_inclusive():
    # Guide 4.0: service on Apr 1 2025 -> next eligible Apr 2 2026. Exactly 96 months ago still blocks;
    # one day earlier than that is outside the window.
    exactly = AS_OF - relativedelta(months=96)
    a = assess_dict(_with_history({"code": "27211", "tooth": 46, "date": str(exactly)}))
    assert a.requirement("frequency_tooth").status == Status.UNSATISFIED
    assert a.verdict == Verdict.BLOCKED
    a = assess_dict(_with_history({"code": "27211", "tooth": 46, "date": str(exactly - relativedelta(days=1))}))
    assert a.requirement("frequency_tooth").status == Status.SATISFIED


def test_frequency_tooth_ignores_other_teeth_and_planned_items():
    a = assess_dict(_with_history({"code": "27211", "tooth": 47, "age": "2y"},
                                  {"code": "27211", "tooth": 46, "age": "1y", "status": "planned"}))
    assert a.requirement("frequency_tooth").status == Status.SATISFIED


def test_frequency_client_four_in_120_months_blocks_three_does_not():
    crowns = [{"code": "27211", "tooth": t, "age": f"{i + 1}y"} for i, t in enumerate((16, 26, 36))]
    a = assess_dict(_with_history(*crowns))
    assert a.requirement("frequency_client").status == Status.SATISFIED
    a = assess_dict(_with_history(*crowns, {"code": "27301", "tooth": 17, "date": str(AS_OF - relativedelta(months=120))}))
    assert a.requirement("frequency_client").status == Status.UNSATISFIED
    a = assess_dict(_with_history(*crowns, {"code": "27301", "tooth": 17, "date": str(AS_OF - relativedelta(months=120, days=1))}))
    assert a.requirement("frequency_client").status == Status.SATISFIED


def test_age_gate_turns_on_the_18th_birthday():
    d = ready_dict()
    d["patient"]["dob"] = "2008-09-18"  # 17, birthday tomorrow
    a = assess_dict(d)
    assert a.requirement("client_age").status == Status.UNSATISFIED and a.verdict == Verdict.BLOCKED
    d["patient"]["dob"] = "2008-09-17"  # 18 today
    assert assess_dict(d).requirement("client_age").status == Status.SATISFIED
    d["patient"]["dob"] = None
    assert assess_dict(d).requirement("client_age").status == Status.INDETERMINATE


def test_history_unknown_makes_frequency_indeterminate_not_blocked():
    d = ready_dict()
    d["assurance"] = {"procedure_history": "Unknown"}
    a = assess_dict(d)
    assert a.requirement("frequency_tooth").status == Status.INDETERMINATE
    assert a.requirement("frequency_client").status == Status.INDETERMINATE
    assert a.verdict == Verdict.NEEDS_INPUT


# --- schedule --------------------------------------------------------------------------------------


@pytest.mark.parametrize("code,disposition,verdict", [
    ("27211", "preauth_required", Verdict.READY_TO_SUBMIT),
    ("27201", "preauth_required", Verdict.READY_TO_SUBMIT),
    ("27301", "preauth_required", Verdict.READY_TO_SUBMIT),
    ("27215", "not_in_schedule_b", Verdict.NEEDS_INPUT),
    ("62501", "excluded", Verdict.EXCLUDED_AS_CODED),
    ("21223", "not_required", Verdict.PREAUTH_NOT_REQUIRED),
])
def test_schedule_dispositions(code, disposition, verdict):
    d = ready_dict()
    d["treatment"]["code"] = code
    for plan in d.get("tx_plans", []):  # footnote 1: the plan must name the treatment being requested
        plan["pending"] = [code]
    a = assess_dict(d)
    assert a.schedule.disposition == disposition
    assert a.verdict == verdict
    if disposition == "not_in_schedule_b":
        assert a.actions[0].title == "Confirm the procedure code against the CDCP grid"
        assert a.actions[0].unblocks == ["schedule"]
