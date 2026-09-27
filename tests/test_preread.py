"""Ophi's pre-read of the dentist's criteria: chart evidence and Laya's note answers, suggested only when they agree."""

from __future__ import annotations

import pytest

from ophi.assertions.preread import pre_reads
from ophi.outcomes import readout
from ophi.service import CaseService, Store


@pytest.fixture
def svc(tmp_path):
    return CaseService(store=Store(tmp_path / "state"))


def test_the_chart_alone_pre_fills_what_it_records_and_flags_what_it_contradicts(svc):
    pre = pre_reads(svc.view("kowalchuk").case, svc.pack, note=None)
    assert pre["no_active_perio"].suggest == "met"  # 3 mm, no bleeding at #46
    assert pre["active_disease_addressed"].suggest == "met"
    er = pre["extensively_restored"]
    assert er.suggest is None and er.against[0].text.startswith("Tooth chart: #46 is already filled on 4 sides (M, O, D, B); this tooth needs 5")
    assert pre["margin_3mm"].suggest is None  # judged on the film, and without the note there is nothing to go on


def test_pending_treatment_in_the_plan_leaves_active_disease_to_the_dentist(svc):
    pre = pre_reads(svc.view("deng").case, svc.pack, note=None)
    assert pre["active_disease_addressed"].suggest is None
    assert pre["active_disease_addressed"].against[0].text == "The treatment plan still has 21212 #47 waiting to be done"


def test_laya_note_answers_outlive_a_new_film(svc):
    svc.record_capture("kowalchuk", "radiograph_pa", "M. Haddad")
    case, rd = svc.view("kowalchuk").case, readout.load("kowalchuk")
    assert rd.matching(case) is None  # the request changed, so the risk plan no longer applies
    assert rd.note_answers(case) == rd.plans[0].plan["note_answers"]  # but the note Laya read is the same
