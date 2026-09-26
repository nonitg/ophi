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


def test_board_puts_each_case_in_its_step_and_starts_with_the_late_appointment(svc):
    b = present.board(svc.queue(), ACTORS["coordinator"], svc.today())
    cols = {c["key"]: [x["case"].case_id for x in c["cards"]] for c in b["columns"]}
    assert list(cols) == ["prepare", "dentist", "send", "sun_life", "decision", "done"]
    assert cols["prepare"][:2] == ["kowalchuk", "deng"]  # appointments inside Sun Life's 7 days come first
    assert cols["sun_life"] == ["okafor", "park"]  # the longest wait first
    assert b["start"]["case"].case_id == "kowalchuk" and "Move it, or tell the patient" in b["start"]["advice"]
    assert b["headline"] == "9 cases need you"  # okafor counts: past 7 days, the mailbox needs checking
    mine = {x["case"].case_id: x["mine"] for c in b["columns"] for x in c["cards"]}
    assert not mine["whitfield"] and not mine["park"] and mine["okafor"]


def test_dentist_board_marks_only_their_cases(svc):
    b = present.board(svc.queue(), ACTORS["dentist"], svc.today())
    mine = [x for c in b["columns"] for x in c["cards"] if x["mine"]]
    assert [x["case"].case_id for x in mine] == ["tremblay", "whitfield"]  # films and perio current: criteria can start
    assert b["start"]["case"].case_id == "tremblay" and b["start"]["action"]["title"] == "Confirm 10 clinical criteria"
    assert b["headline"] == "2 cases are waiting on you"


def test_timing_chips_name_the_deadline_for_the_step(svc):
    chips = {v.case.case_id: present.timing(v, svc.today()) for v in svc.queue()}
    assert (chips["kowalchuk"]["text"], chips["kowalchuk"]["tone"]) == ("Late for Sep 20 crown", "bad")
    assert (chips["singh"]["text"], chips["singh"]["tone"]) == ("Send today", "warn")
    assert chips["whitfield"]["text"] == "Sign by Sep 24"
    assert (chips["okafor"]["text"], chips["okafor"]["tone"]) == ("Sent 8 days ago", "warn")


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
