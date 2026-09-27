"""The outcomes corpus behind a case: the clinic's denial rate for scoring, and no past outcomes on the step."""

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
