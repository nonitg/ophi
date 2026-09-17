"""Golden-expectation regression over cases/**. Any changed verdict, status, completeness or top action is a
failure a human must acknowledge by rewriting the expectation (`colombus eval --write`)."""

from __future__ import annotations

from colombus.evals.run import run_all
from tests._cases import CASES_DIR, EXPECTED_DIR, corpus_files


def test_corpus_matches_golden_expectations():
    ok, report = run_all(CASES_DIR, EXPECTED_DIR)
    assert ok, report
    # A case with no expectation is silently written and reported as "wrote"; that is not a pass.
    assert "wrote" not in report, report
    assert "FALSE-READY" not in report, report


def test_corpus_has_the_enumerated_adversarial_cases():
    stems = {p.stem for p in corpus_files()}
    required = {
        "pa_364d", "pa_365d", "pa_366d", "pa_leap_band", "psr_4_one_sextant", "psr_3_two_sextants",
        "psr_3_requested_sextant_charted", "psr_3_requested_sextant_not_charted", "psr_3_other_sextant_only",
        "perio_missing_requested_tooth", "perio_missing_other_tooth", "perio_uncertified", "bw_right_only",
        "bw_derived_side", "radiograph_undated", "universal_16", "third_molar_no_exception", "age_17",
        "prior_crown_same_tooth", "four_crowns_ten_years", "bridge_code_excluded", "code_27215_not_in_schedule_b",
        "filling_not_preauth", "assertion_not_met", "history_unknown", "pending_basic_treatment", "retired_lab_code",
        "current_lab_code", "endo_history_via_history", "fully_ready", "proposal_pending",
    }
    assert required <= stems, sorted(required - stems)
    # Expectations are keyed by case stem, so stems must be unique across cases/**.
    assert len(stems) == len(corpus_files())
