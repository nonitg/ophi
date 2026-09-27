"""A denial read back against the pack: what Sun Life's reason points at, and what a resubmission changed."""

from __future__ import annotations

from ophi.casegen.dsl import build_case
from ophi.engine.models import Status
from ophi.outcomes.denial_map import EXPORT_CODE, load_denial_map, requirements_for
from ophi.outcomes.why_denied import changes_between, explain_denial
from ophi.rules.loader import pack_for
from ophi.workflow import REASONS
from tests._cases import assess_dict, ready_dict

PACK = pack_for(build_case(ready_dict(), "inline"))


def test_every_live_reason_maps_to_a_reviewed_export_code():
    """The letter vocabulary and the export vocabulary must stay joined, or a live denial silently stops
    being attributable the moment someone adds a reason."""
    assert set(EXPORT_CODE) == set(REASONS)
    known = set(load_denial_map(PACK))
    assert not set(EXPORT_CODE.values()) - known


def test_missing_radiograph_names_the_criteria_ophi_had_flagged():
    d = ready_dict()
    d["radiographs"] = []
    a = assess_dict(d)
    r = explain_denial(a, "missing_radiograph", PACK)
    assert r.mapped and not r.unexplained
    assert {c.requirement_id for c in r.foreseen} == {"radiograph_pa", "radiograph_bw"}
    assert not r.blind_spot  # Ophi saw this one coming


def test_a_denial_on_criteria_ophi_read_as_satisfied_is_a_blind_spot():
    a = assess_dict(ready_dict())  # fully documented: the radiographs are there
    r = explain_denial(a, "missing_radiograph", PACK)
    assert r.criteria and not r.foreseen
    assert r.blind_spot


def test_a_vague_letter_is_unexplained_rather_than_guessed():
    a = assess_dict(ready_dict())
    r = explain_denial(a, None, PACK)
    assert r.unexplained and not r.mapped and r.criteria == []


def test_requirements_for_separates_unreviewed_from_reviewed_as_uncovered():
    assert requirements_for("duplicate_request", PACK) == []  # reviewed: nothing in the pack covers it
    assert requirements_for(None, PACK) is None


def test_changes_between_attempts_names_what_turned_it_around():
    before = assess_dict({**ready_dict(), "radiographs": []})
    after = assess_dict(ready_dict())
    fixed = [c for c in changes_between(before, after) if c.fixed]
    assert {c.requirement_id for c in fixed} >= {"radiograph_pa", "radiograph_bw"}
    assert all(c.after is Status.SATISFIED for c in fixed if c.requirement_id.startswith("radiograph"))


def _denied_client(tmp_path, reason_key):
    """A case driven to the resubmit step with Sun Life's reason recorded, on the real page."""
    from fastapi.testclient import TestClient

    from ophi.packet.narrative import draft_narrative
    from ophi.service import CaseService, Store
    from ophi.web.app import create_app

    svc = CaseService(store=Store(tmp_path / "var"))
    v = svc.view("whitfield")
    svc.sign_off("whitfield", "Dr. Priya Lau", "ON-48213", draft_narrative(v.case, v.assessment, svc.pack))
    svc.mark_submitted("whitfield", "Kim Osei")
    svc.record_decision("whitfield", "denied", svc.today(), "No radiograph received.", "Kim Osei", reason_key=reason_key)
    return TestClient(create_app(svc=svc, live_ml=False))


def test_the_case_page_names_the_criteria_the_denial_points_to(tmp_path):
    body = _denied_client(tmp_path, "missing_radiograph").get("/cases/whitfield").text
    assert "What that reason points to in the rule pack" in body
    assert "Dated periapical radiograph of the requested tooth, within 12 months" in body
    assert "Ophi read this as" in body


def test_the_panel_stays_off_when_the_letter_named_no_reason(tmp_path):
    body = _denied_client(tmp_path, None).get("/cases/whitfield").text
    assert "What that reason points to in the rule pack" not in body
