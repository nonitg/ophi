"""Training set for Laya and the tree model: what was sent, labels, resubmissions, clinic split."""

from __future__ import annotations

from ophi.outcomes.laya_questions import DECISION, DECISION_KEYS, gold
from ophi.outcomes.training_set import SENT, clinic_denial_rates, features, load_examples, note_labels, request_text, split_by_clinic
from ophi.rules.loader import default_pack

EXAMPLES = {e.preauth_id: e for e in load_examples()}


def test_first_request_renders_only_what_was_sent():
    e = EXAMPLES["PA-SYN-300010"]  # the worked example in docs/plan/05-outcomes-learning.md §2.3
    text = request_text(e)
    assert set(e.sent) == set(SENT)
    assert "bitewings not sent" in text and "Lab codes: 99222" in text and e.sent["clinical_notes"] in text
    assert e.decision == "UNSPECIFIED"  # the vague letter
    assert note_labels(e)["extensively_restored"] is False  # the reason the letter didn't give


def test_resubmission_applies_the_clinics_changes():
    first, resub = EXAMPLES["PA-SYN-300024"], EXAMPLES["PA-SYN-300024/resubmission"]  # fixed a missing perio chart
    assert first.sent["perio_summary"] is None or first.sent["perio_summary"]["chart_type"] != "complete"
    assert resub.sent["perio_summary"]["chart_type"] == "complete"
    assert [a["type"] for a in resub.sent["attachments"]].count("periodontal_charting") == 1
    assert resub.truth is None and note_labels(resub) is None
    assert resub.decision == "UNSPECIFIED"  # denied again, vague letter


def test_split_keeps_each_clinic_in_one_part():
    parts = split_by_clinic(list(EXAMPLES.values()))
    clinics = [{e.clinic for e in rows} for rows in parts.values()]
    assert sum(len(rows) for rows in parts.values()) == len(EXAMPLES)
    assert not (clinics[0] & clinics[1] or clinics[0] & clinics[2] or clinics[1] & clinics[2])


def test_features_carry_the_engines_reading():
    rates = clinic_denial_rates(list(EXAMPLES.values()))
    f = features(EXAMPLES["PA-SYN-300010"], default_pack(), rates["PA-SYN-300010"])
    assert f["req_radiograph_bw"] == "unsatisfied" and f["req_lab_codes_current"] == "unsatisfied"
    assert f["bw_sides"] == 0 and f["pa_age_days"] is not None
    assert rates["PA-SYN-300000"] is None or 0 <= rates["PA-SYN-300000"] <= 1


def test_gold_labels_the_decision_only_when_the_letter_names_it():
    vague, named = EXAMPLES["PA-SYN-300010"], EXAMPLES["PA-SYN-300000"]  # FREQ_LIMIT
    assert DECISION not in gold(vague) and gold(vague)["extensively_restored"] == [0.0, 1.0]
    target = gold(named)[DECISION]
    assert sum(target) == 1.0 and DECISION_KEYS[target.index(1.0)] == "frequency_limit"
