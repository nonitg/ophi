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


def test_board_starts_with_the_patient_in_the_chair_then_the_late_appointment(svc):
    b = present.board(svc.queue(), ACTORS["coordinator"], svc.today())
    cols = {c["key"]: [x["case"].case_id for x in c["cards"]] for c in b["columns"]}
    assert list(cols) == ["patient", "prepare", "dentist", "send", "sun_life", "decision"]
    assert cols["patient"] == ["kowalchuk", "deng", "singh", "rosco"]  # films and perio need the patient; paperwork doesn't
    assert cols["prepare"] == ["tremblay"] and cols["sun_life"] == ["okafor", "park"]  # the longest wait first
    start = b["start"]
    assert start["case"].case_id == "kowalchuk" and [i["label"] for i in start["chair"]] == ["6-site perio chart", "PA X-ray of #46"]
    assert b["headline"] == "9 cases need you"  # okafor counts: past 7 days, the mailbox needs checking
    mine = {x["case"].case_id: x["mine"] for c in b["columns"] for x in c["cards"]}
    assert not mine["whitfield"] and not mine["park"] and mine["okafor"]


def test_chair_gaps_batch_into_one_visit_on_the_card(svc):
    b = present.board(svc.queue(), ACTORS["coordinator"], svc.today())
    acts = {x["case"].case_id: x["action"] for c in b["columns"] for x in c["cards"]}
    assert acts["kowalchuk"]["title"] == "Before Teresa leaves: 6-site perio chart, PA X-ray of #46"
    assert (acts["deng"]["title"], acts["deng"]["note"]) == ("Move the crown, then book a visit: 6-site perio chart, basic treatment", "+1 desk fix")


def test_booked_cases_close_out_the_decision_column(svc):
    svc.mark_booked("nguyen", date(2026, 9, 16), "Kim Osei")
    b = present.board(svc.queue(), ACTORS["coordinator"], svc.today())
    decision = next(c for c in b["columns"] if c["key"] == "decision")["cards"]
    assert [x["case"].case_id for x in decision] == ["marchand", "nguyen"] and decision[-1]["timing"]["text"] == "Booked Sep 16"


def test_dentist_board_marks_only_their_cases(svc):
    b = present.board(svc.queue(), ACTORS["dentist"], svc.today())
    mine = {x["case"].case_id: x for c in b["columns"] for x in c["cards"] if x["mine"]}
    assert list(mine) == ["kowalchuk", "tremblay", "whitfield"]  # in the chair: the dentist orders the film
    assert mine["tremblay"]["action"]["title"] == "Confirm 10 clinical criteria"  # films and perio current: criteria can start
    assert b["start"]["case"].case_id == "kowalchuk" and b["headline"] == "3 cases are waiting on you"


def test_timing_chips_name_the_deadline_for_the_step(svc):
    chips = {v.case.case_id: present.timing(v, svc.today()) for v in svc.queue()}
    assert (chips["kowalchuk"]["text"], chips["kowalchuk"]["tone"]) == ("In the chair now", "warn")
    assert (chips["deng"]["text"], chips["deng"]["tone"]) == ("Late for Sep 23 crown", "bad")
    assert (chips["singh"]["text"], chips["singh"]["tone"]) == ("Visit needed today", "warn")
    assert chips["whitfield"]["text"] == "Sign by Sep 24"
    assert (chips["okafor"]["text"], chips["okafor"]["tone"]) == ("Sent 8 days ago", "warn")


def test_case_steps_open_the_current_step_and_hold_criteria_until_the_films_are_current(svc):
    steps = {s["key"]: s["state"] for s in present.case_steps(svc.view("singh"))}  # needs a new periapical
    assert steps == {"check": "done", "chart": "current", "criteria": "upcoming", "sign": "upcoming", "send": "upcoming",
                     "decision": "upcoming", "book": "upcoming"}
    tremblay = {s["key"]: s["state"] for s in present.case_steps(svc.view("tremblay"))}  # only a quote to confirm
    assert tremblay["criteria"] == "open"
    chart = present.case_steps(svc.view("kowalchuk"))[1]  # in the chair: the dentist's team closes the gaps now
    assert (chart["title"], chart["who"], chart["state"]) == ("Before Teresa leaves", "dentist", "current")
    resubmit = present.case_steps(svc.view("marchand"))[-1]
    assert resubmit["key"] == "resubmit" and resubmit["reconsider_by"] == date(2026, 11, 2)


def test_activity_folds_a_burst_of_answers_into_one_line(svc):
    svc.assert_many("singh", [{"criterion_id": c, "value": "met"} for c in ("ferrule_1_5mm", "margin_3mm")], "Dr. Priya Lau", "ON-48213")
    assert present.activity(svc.store.audit_log("singh"))[0]["what"] == "recorded 2 criteria"


def test_results_count_gaps_caught_and_sun_life_decisions(svc):
    res = present.results(svc.queue(), svc.pack, svc.lookback(), present.recover(svc.recover_rows()))
    assert res["caught_total"] == 7 and res["caught_cases"] == 4  # found missing; what the PMS couldn't show isn't counted
    assert sum(n for _, n in res["caught_chair"]) == 6 and res["denied_for_chair"] > 0  # films, perio and basic treatment
    assert (res["approved"], res["denied"], res["waiting"]) == (1, 1, 2)
    assert res["recover"]["count"] == 10
