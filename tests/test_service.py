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
