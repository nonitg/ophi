"""The call-script verifier, against a corpus of deliberately bad scripts.

The memo's bar (`docs/voice-followup.md`): if the verifier cannot reject every one of these, the drafter
does not get built. Each bad script isolates one failure so a regression names itself.
"""

from __future__ import annotations

from datetime import date

import pytest

from ophi.lookback import LookBackRow
from ophi.verify.callscript import verify_script

CLINIC = "Bayview Dental"

GOOD = """Hi, this is Bayview Dental calling for Leila. We're following up on something unfinished on your
file — the crown we planned for tooth #16. We sent the request to Sun Life on 2026-01-15 and it came back
to us, and we need a new x-ray of that tooth before we can send it again. Could you give us a call back so
we can find a time that suits you? Thanks very much."""


@pytest.fixture
def row() -> LookBackRow:
    return LookBackRow(
        case_id="pred_4411", patient_label="L.F.", patient_name="Leila Farahani", code="27211",
        tooth_fdi=16, submitted_on=date(2026, 1, 15), decision="denied", fee_dollars=1450.0,
        gaps=["Periapical radiograph of the requested tooth"], denial_text="Denied as per the plan criteria",
    )


def test_a_grounded_script_passes(row):
    r = verify_script(GOOD, row, CLINIC)
    assert r.ok, r.findings


# Each entry: the check it must trip, and the script that trips it.
BAD = [
    ("copy_law", "Hi, this is Bayview Dental. Your crown on #16 will be approved once we resend it. Call us back."),
    ("copy_law", "Bayview Dental here. The crown on #16 is covered by the plan, so call us back to get started."),
    ("copy_law", "Bayview Dental calling. It is likely Sun Life says yes this time on #16. Please call back."),
    ("no_promise", "Bayview Dental calling about #16. You won't pay anything for the crown. Call us back."),
    ("no_promise", "Bayview Dental calling. We can get this sorted for #16 — reimburses in full. Call back."),
    ("tooth_grounded", "Bayview Dental calling about the crown on tooth #26. We need a new x-ray. Call us back."),
    ("no_fee_quoted", "Bayview Dental calling about #16. The crown is $1,450. Call us back to book an x-ray."),
    ("dates_grounded", "Bayview Dental calling about #16. Sun Life wrote to us on 2025-03-02. Call us back for an x-ray."),
    ("gaps_grounded", "Bayview Dental calling about #16. We need periodontal charting and pocket depths. Call back."),
    ("no_invented_name", "Bayview Dental calling about #16. Doctor Melissa Brandt wants a new x-ray. Call us back."),
    ("names_clinic", "Hi, we're calling about the crown on tooth #16. We need a new x-ray. Please call us back."),
    ("length", "Bayview Dental calling about tooth #16 and the x-ray we need. " + "We would really like to see you again soon. " * 40),
    ("not_empty", "   "),
]


@pytest.mark.parametrize(("check", "script"), BAD, ids=[f"{c}-{i}" for i, (c, _) in enumerate(BAD)])
def test_bad_scripts_are_rejected(row, check, script):
    r = verify_script(script, row, CLINIC)
    assert not r.ok, f"accepted a bad script: {script!r}"
    assert r.checks[check] is False, f"rejected for {r.findings}, not for {check}"


def test_the_patients_own_name_is_allowed_once_staff_template_it_in(row):
    script = GOOD.replace("for Leila.", "for Leila Farahani.")
    assert verify_script(script, row, CLINIC, allow_name=row.patient_name).ok


def test_a_gap_the_row_does_record_may_be_named(row):
    row.gaps = ["Six-point periodontal charting"]
    script = GOOD.replace("a new x-ray of that tooth", "an updated set of gum measurements")
    assert verify_script(script, row, CLINIC).ok


# --- the drafter's loop, with a scripted model ------------------------------------------------------


def test_the_drafter_re_asks_with_the_findings_and_returns_the_clean_draft(row):
    from ophi.callscript import draft_call_script

    drafts = iter(["Bayview Dental calling. Your crown on #16 will be approved. Call us back.", GOOD])
    asked: list[str] = []

    def model(prompt: str) -> str:
        asked.append(prompt)
        return next(drafts)

    script = draft_call_script(row, CLINIC, drafter=model)
    assert script.report.ok
    assert "will be approved" in asked[1], "the second ask never told the model what was wrong"


def test_no_draft_is_returned_when_none_verifies(row):
    from ophi.callscript import draft_call_script
    from ophi.letters import LetterError

    bad = "Bayview Dental calling about #16. The crown is $1,450 and it's covered. Call us back."
    with pytest.raises(LetterError, match="didn't hold up"):
        draft_call_script(row, CLINIC, drafter=lambda _p: bad)


def test_the_drafter_is_never_given_the_patients_name(row):
    from ophi.callscript import facts

    f = facts(row, CLINIC)
    assert row.patient_label in f
    assert "Leila" not in f and "Farahani" not in f
