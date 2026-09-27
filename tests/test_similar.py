"""Past requests like a case, from Supabase: both of Sun Life's answers for a fix step, and the links on the case page."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests import _pg
from ophi.outcomes import past_store, similar, store
from ophi.rules.loader import default_pack
from ophi.service import CaseService, Store
from ophi.web.app import create_app


@pytest.fixture(scope="module")
def url():
    name, url = _pg.start()
    try:
        with store.connect(url) as c:
            store.migrate(c)
            past_store.save_all(c, default_pack())
        yield url
    finally:
        _pg.stop(name)


@pytest.fixture
def past(url):
    return past_store.Cached(lambda: store.connect(url))


def _case(tmp_path, case_id: str = "kowalchuk"):
    return CaseService(store=Store(tmp_path / "state")).view(case_id).case


def test_periapical_step_finds_both_answers_like_this_tooth_first(tmp_path, past):
    case = _case(tmp_path)  # crown on #46, a molar
    [like] = similar.for_steps(past, case, default_pack(), [["radiograph_pa"]])
    assert like["approved"] and like["denied"] and like["n_resent"] and like["n_denied"]
    assert like["approved"][0]["resent_then_approved"] and like["approved"][0]["outcome"] == "approved"
    assert all(x["outcome"] == "denied" and not x["resent_then_approved"] for x in like["denied"])
    assert like["denied"][0]["tooth"] == 46  # the same tooth outranks the rest
    assert all(x["tooth"] % 10 in (6, 7, 8) for x in like["approved"][:1] + like["denied"])  # molars like #46 first
    assert like["reasons"][0]["reason"] == "X-ray over 12 months old"  # #46 has a periapical, just an old one


def test_clinic_denial_rate_for_a_clinic_with_past_requests(tmp_path, past, url):
    case = _case(tmp_path)
    assert similar.clinic_denial_rate(past, lambda: store.connect(url), case) is None  # the demo clinic has no past requests
    t = case.treatment
    ours = case.model_copy(update={"treatment": t.model_copy(update={"provider": t.provider.model_copy(update={"licence": "SYN-P-4017"})})})
    with store.connect(url) as c:
        want = past_store.clinic_denial_rate(c, "SYN-P-4017", case.as_of)
    assert want is not None and similar.clinic_denial_rate(past, lambda: store.connect(url), ours) == pytest.approx(want)


def test_case_page_keeps_past_outcomes_off_the_step(tmp_path, past):
    """The step says what to do; past approvals and denials stay on the Past denials pages."""
    app = create_app(svc=CaseService(store=Store(tmp_path / "state")), packets_dir=tmp_path / "packets")
    app.state.past = past
    html = TestClient(app).get("/cases/kowalchuk").text
    assert "Past requests like this" not in html and "/past/PA-SYN-" not in html


def test_counts_stay_corpus_wide_when_chips_are_scoped_to_one_clinic(tmp_path, past):
    case = _case(tmp_path)
    [every] = similar.for_steps(past, case, default_pack(), [["radiograph_pa"]])
    clinic = every["denied"][0]
    owner = next(r["clinic_id"] for r in past.rows() if r["preauth_id"] == clinic["id"])
    [mine] = similar.for_steps(past, case, default_pack(), [["radiograph_pa"]], owner)
    assert (mine["n_resent"], mine["n_approved"], mine["n_denied"]) == (every["n_resent"], every["n_approved"], every["n_denied"])
    ids = {x["id"] for x in mine["approved"] + mine["denied"]}
    assert ids and all(r["clinic_id"] == owner for r in past.rows() if r["preauth_id"] in ids)


def test_a_clinic_with_no_past_requests_still_sees_the_counts(tmp_path, past):
    case = _case(tmp_path)
    [like] = similar.for_steps(past, case, default_pack(), [["radiograph_pa"]], "SYN-P-NOBODY")
    assert like["n_denied"] and not like["approved"] and not like["denied"]
