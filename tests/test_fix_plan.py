"""Past-decision fix plans on the case page: a charted case read as Laya reads past requests, the stored plan
matched to the chart as it stands, and what the dentist sees from it."""

from __future__ import annotations

from datetime import date

import pytest

from ophi import fixes
from ophi.outcomes import readout
from ophi.outcomes.readout import Readout, ScoredPlan, fingerprint, text_for
from ophi.service import CaseService, Store
from ophi.web import present


@pytest.fixture
def svc(tmp_path):
    return CaseService(store=Store(tmp_path / "state"))


def test_a_charted_case_reads_like_a_past_request(svc):
    text = text_for(svc.base_case("deng"))
    assert "Crown 27211 on tooth 37 (molar). Member age 70-74. Lab codes: 99333." in text
    assert "Plan pending: 27211 #37, 21212 #47." in text  # the plan's other tooth comes from the chart's history
    assert "Perio: psr only chart" in text  # a one-tooth chart is not a complete chart


def test_the_plan_shown_is_the_one_made_for_the_chart_as_it_stands(svc):
    r = readout.load("deng")
    base = svc.base_case("deng")
    assert r.matching(base) is r.plans[0].plan
    assert r.matching(fixes.apply(base, ["lab_codes_current"], svc.pack)) is r.plans[1].plan  # after staff click Apply
    changed = base.model_copy(update={"as_of": date(2026, 10, 1)})
    assert r.matching(changed) is None


def test_dentist_sees_what_the_note_shows_for_each_criterion(svc):
    view = svc.view("tremblay")
    plan = {"model": {"laya": "test"}, "now": {"level": "high", "score": 0.8}, "after_fixes": None, "remaining": None, "drivers": [],
            "fixes": [{"id": "cracked", "kind": "dentist", "title": "Cracked tooth", "why": "", "requirement_id": None, "clause": None}],
            "note_answers": {"extensively_restored": 0.2, "structure_lost": 0.9, "endo_not_healed": 0.95, "poor_support": 0.1,
                             "pending_basic": 0.5, "subgingival_margin": 0.05}}
    rd = Readout(case_id="tremblay", scored_on=date(2026, 9, 26),
                 plans=[ScoredPlan(state="as_charted", text_sha256=fingerprint(text_for(view.case)), plan=plan)])
    p = present.dentist_panel(view, rd)
    assert p["now"]["label"] == "High"
    assert p["reads"]["extensively_restored"] == "not_shown"  # a sure no outweighs the lost cusp
    assert p["reads"]["endo_healed"] == "not_shown"
    assert p["reads"]["no_furcation"] == p["reads"]["crown_root_ratio"] == p["reads"]["margin_3mm"] == "supports"
    assert "active_disease_addressed" not in p["reads"]  # the note is unclear
    assert [f["title"] for f in p["decide"]] == ["Cracked tooth"]  # no requirement asks for it
