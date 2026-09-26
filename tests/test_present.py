"""Worklist, case steps and timing as the templates render them. Page-level coverage is in test_web."""

from __future__ import annotations

from datetime import date

import pytest

from ophi.demo import seed
from ophi.service import CaseService, Store
from ophi.web import present
from ophi.web.present import ACTORS


@pytest.fixture
def svc(tmp_path):
    s = CaseService(store=Store(tmp_path / "state"))
    seed(s)
    return s


def test_worklist_groups_by_step_in_lifecycle_order_and_flags_late_appointments(svc):
    w = present.worklist(svc.queue(), ACTORS["coordinator"], svc.today())
    assert [g["label"] for g in w["groups"]] == ["Fix chart gaps", "Dentist review", "Send to Sun Life", "Waiting on Sun Life", "Book the crown", "Resubmit"]
    assert w["headline"] == "8 preauthorizations need you"
    assert [r["case"].case_id for r in w["late"]] == ["kowalchuk", "deng"]  # appointments inside Sun Life's 7 days
    assert [r["case"].case_id for r in w["overdue"]] == ["okafor"]  # at Sun Life longer than 7 days


def test_dentist_sees_only_their_pile(svc):
    w = present.worklist(svc.queue(), ACTORS["dentist"], svc.today())
    assert [g["label"] for g in w["groups"]] == ["Waiting on you", "You can confirm criteria now"]
    assert [r["case"].case_id for r in w["groups"][0]["rows"]] == ["whitfield"]
    assert [r["case"].case_id for r in w["groups"][1]["rows"]] == ["tremblay"]  # films and perio current; paperwork left
    assert w["groups"][1]["rows"][0]["next"]["title"] == "Confirm 10 clinical criteria"


def test_runway_shares_one_four_week_scale():
    assert present.runway(14) == {"appt": 50.0, "win": 25.0, "win_w": 25.0, "beyond": False, "late": False, "days": 14}
    assert present.runway(3)["late"] and present.runway(3)["win"] == 0
    assert present.runway(40)["beyond"] and present.runway(-1) is None


def test_case_steps_open_the_current_step_and_hold_criteria_until_the_films_are_current(svc):
    steps = {s["key"]: s["state"] for s in present.case_steps(svc.view("singh"))}  # needs a new periapical
    assert steps == {"check": "done", "chart": "current", "criteria": "upcoming", "sign": "upcoming", "send": "upcoming",
                     "decision": "upcoming", "book": "upcoming"}
    tremblay = {s["key"]: s["state"] for s in present.case_steps(svc.view("tremblay"))}  # only a quote to confirm
    assert tremblay["criteria"] == "open"
    resubmit = present.case_steps(svc.view("marchand"))[-1]
    assert resubmit["key"] == "resubmit" and resubmit["reconsider_by"] == date(2026, 11, 2)


def test_activity_folds_a_burst_of_answers_into_one_line(svc):
    svc.assert_many("singh", [{"criterion_id": c, "value": "met"} for c in ("ferrule_1_5mm", "margin_3mm")], "Dr. Priya Lau", "ON-48213")
    assert present.activity(svc.store.audit_log("singh"))[0]["what"] == "recorded 2 criteria"


def test_results_count_gaps_caught_and_sun_life_decisions(svc):
    res = present.results(svc.queue(), svc.pack, svc.lookback(), present.recover(svc.recover_rows()))
    assert res["caught_total"] == 7 and res["caught_cases"] == 4  # found missing; what the PMS couldn't show isn't counted
    assert (res["approved"], res["denied"], res["waiting"]) == (1, 1, 2)
    assert res["recover"]["count"] == 10
