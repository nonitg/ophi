"""Service-layer contract: roles, narrative validation, and sign-off tied to the assessment it attested."""

from pathlib import Path

import pytest

from ophi.packet.narrative import draft_narrative
from ophi.service import CaseService, NarrativeInvalid, Store

CRITERIA = ["no_active_perio", "crown_root_ratio", "no_furcation", "margin_3mm", "ferrule_1_5mm",
            "mesiodistal_space", "no_adjunctive_needed", "extensively_restored", "active_disease_addressed", "endo_healed"]


@pytest.fixture
def svc(tmp_path: Path) -> CaseService:
    return CaseService(store=Store(tmp_path / "var"))


def _make_ready(svc: CaseService, case_id: str = "tremblay") -> str:
    v = svc.view(case_id)
    svc.confirm_proposal(case_id, v.proposals[0].artifact_id, "confirmed", "Kim Osei")
    for c in CRITERIA:
        svc.assert_criterion(case_id, c, "met", "Dr. Priya Lau", "ON-48213")
    v = svc.view(case_id)
    return draft_narrative(v.case, v.assessment, svc.pack)


def test_apply_fix_closes_a_gap_ophi_can_fix_itself(svc: CaseService):
    assert svc.apply_fixes("deng", ["lab_codes_current"], "Kim Osei") == ["lab_codes_current"]
    v = svc.view("deng")
    assert v.case.treatment.lab_codes == ["99113"] and v.base_case.treatment.lab_codes == ["99333"]  # the PMS read is untouched
    assert v.assessment.requirement("lab_codes_current").status.value == "satisfied"
    assert [e.detail for e in svc.store.audit_log("deng") if e.event == "apply_fix"] == ["Replace lab code 99333 with 99113"]
    with pytest.raises(ValueError):
        svc.apply_fixes("deng", ["lab_codes_current"], "Kim Osei")  # already closed
    with pytest.raises(ValueError):
        svc.apply_fixes("singh", ["radiograph_pa"], "Kim Osei")  # a film is taken, not applied


def test_coordinator_cannot_assert_or_sign(svc: CaseService):
    with pytest.raises(PermissionError):
        svc.assert_criterion("tremblay", "ferrule_1_5mm", "met", "Kim Osei", None, role="treatment coordinator")
    text = _make_ready(svc)
    with pytest.raises(PermissionError):
        svc.sign_off("tremblay", "Kim Osei", None, text, role="treatment coordinator")


def test_narrative_validator_blocks_copy_law_and_ungrounded_text(svc: CaseService):
    text = _make_ready(svc)
    with pytest.raises(NarrativeInvalid) as e:
        svc.sign_off("tremblay", "Dr. Priya Lau", "ON-48213", text + "\nThis crown will be approved and is medically necessary.")
    assert any("approved" in v for v in e.value.violations)
    with pytest.raises(NarrativeInvalid):
        svc.save_narrative("tremblay", text + "\nRadiograph dated 2019-01-01 shows #47 fracture.", "Dr. Priya Lau")
    svc.sign_off("tremblay", "Dr. Priya Lau", "ON-48213", text)  # the unedited draft signs cleanly
    assert svc.view("tremblay").signed


def test_sign_off_is_void_after_a_clinical_change(svc: CaseService):
    text = _make_ready(svc)
    svc.sign_off("tremblay", "Dr. Priya Lau", "ON-48213", text)
    assert svc.view("tremblay").signed
    svc.assert_criterion("tremblay", "ferrule_1_5mm", "not_applicable", "Dr. Priya Lau", "ON-48213")
    v = svc.view("tremblay")
    assert not v.signed and v.state.sign_off is None  # a new answer clears the record outright


def test_life_after_sign_off_send_deny_resubmit_approve_book(svc: CaseService):
    from datetime import date

    from ophi.workflow import Stage
    with pytest.raises(PermissionError):  # an unsigned packet cannot be marked sent
        svc.mark_submitted("whitfield", "Kim Osei")
    v = svc.view("whitfield")
    svc.sign_off("whitfield", "Dr. Priya Lau", "ON-48213", draft_narrative(v.case, v.assessment, svc.pack))
    assert svc.view("whitfield").stage == Stage.SEND

    with pytest.raises(ValueError):  # sent before the dentist signed
        svc.mark_submitted("whitfield", "Kim Osei", on=date(2026, 9, 10))
    svc.mark_submitted("whitfield", "Kim Osei", on=svc.today())
    assert svc.view("whitfield").stage == Stage.SUN_LIFE
    with pytest.raises(ValueError):  # decided before it was sent
        svc.record_decision("whitfield", "denied", date(2026, 9, 9), None, "Kim Osei")
    svc.record_decision("whitfield", "denied", svc.today(), "Required radiographs not received.", "Kim Osei")
    assert svc.view("whitfield").stage == Stage.RESUBMIT

    svc.start_resubmission("whitfield", "Kim Osei")
    st = svc.view("whitfield").state
    assert svc.view("whitfield").stage == Stage.DENTIST  # a new request needs a new signature
    assert st.attempts[0].decision.reason == "Required radiographs not received." and st.sign_off is None

    v = svc.view("whitfield")
    svc.sign_off("whitfield", "Dr. Priya Lau", "ON-48213", draft_narrative(v.case, v.assessment, svc.pack))
    svc.mark_submitted("whitfield", "Kim Osei")
    svc.record_decision("whitfield", "approved", svc.today(), None, "Kim Osei")
    svc.mark_booked("whitfield", date(2026, 10, 1), "Kim Osei")
    assert svc.view("whitfield").stage == Stage.DONE
    assert [e.event for e in svc.store.audit_log("whitfield")][-2:] == ["record_decision", "mark_booked"]


def test_a_sent_request_is_part_of_the_record_until_resubmitted(svc: CaseService):
    from datetime import date
    v = svc.view("whitfield")
    svc.sign_off("whitfield", "Dr. Priya Lau", "ON-48213", draft_narrative(v.case, v.assessment, svc.pack))
    svc.mark_submitted("whitfield", "Kim Osei", on=svc.today())
    for change in (lambda: svc.assert_criterion("whitfield", "ferrule_1_5mm", "not_met", "Dr. Priya Lau", "ON-48213"),
                   lambda: svc.mark_submitted("whitfield", "Kim Osei"),
                   lambda: svc.sign_off("whitfield", "Dr. Priya Lau", "ON-48213", draft_narrative(v.case, v.assessment, svc.pack))):
        with pytest.raises(PermissionError):
            change()
    svc.record_decision("whitfield", "approved", svc.today(), None, "Kim Osei")
    with pytest.raises(ValueError):  # past the decision's 12-month validity
        svc.mark_booked("whitfield", date(2028, 1, 1), "Kim Osei")


def test_undo_takes_back_only_the_latest_step(svc: CaseService):
    from ophi.workflow import Stage
    v = svc.view("whitfield")
    svc.sign_off("whitfield", "Dr. Priya Lau", "ON-48213", draft_narrative(v.case, v.assessment, svc.pack))
    svc.mark_submitted("whitfield", "Kim Osei")
    svc.record_decision("whitfield", "denied", svc.today(), None, "Kim Osei")
    with pytest.raises(PermissionError):
        svc.undo("whitfield", "sent", "Kim Osei")  # the decision came after it
    svc.undo("whitfield", "decision", "Kim Osei")
    assert svc.view("whitfield").stage == Stage.SUN_LIFE


def test_first_check_keeps_gaps_after_they_are_closed(svc: CaseService):
    assert svc.view("singh").state.first_check.gaps == ["radiograph_pa"]


def test_recover_followup_is_recorded_against_a_never_resubmitted_denial(svc: CaseService):
    row = svc.recover_rows()[0]["row"]
    svc.record_followup(row.case_id, "rebooking", "wants it before year end", "Kim Osei")
    got = next(x for x in svc.recover_rows() if x["row"].case_id == row.case_id)["followup"]
    assert got.status == "rebooking" and got.note == "wants it before year end"
    with pytest.raises(KeyError):
        svc.record_followup("not-a-denial", "rebooking", None, "Kim Osei")
