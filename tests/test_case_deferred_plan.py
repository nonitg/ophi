"""The case page must open without running the models; the now-section arrives on its own request."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ophi import copy_law
from ophi.service import CaseService, Store
from ophi.web.app import create_app


class StubScorer:
    """Stands in for LiveScorer with nothing scored yet, and counts every time a request would wait on it."""

    def __init__(self):
        self.waits = 0

    def cached(self, case):
        return None

    def latest(self, case):
        self.waits += 1
        return None

    def warm_cases(self, cases):
        pass


@pytest.fixture
def unscored(tmp_path):
    svc = CaseService(store=Store(tmp_path / "state"))
    app = create_app(auto_rules_check=False, svc=svc, packets_dir=tmp_path / "packets", seed_demo=True)
    with TestClient(app, follow_redirects=False) as c:
        app.state.live = StubScorer()  # after seeding, so the demo's own setup is untouched
        yield c, app.state.live, svc


def test_case_page_renders_without_running_the_models(unscored):
    client, scorer, svc = unscored
    case_id = svc.queue()[0].case.case_id
    r = client.get(f"/cases/{case_id}")
    assert r.status_code == 200
    assert f"/cases/{case_id}/now" in r.text  # the skeleton says where its content comes from
    assert scorer.waits == 0
    assert not copy_law.FORBIDDEN.search(r.text)  # the stand-in copy is held to the same law as the plan


def test_now_fragment_scores_and_returns_just_the_section(unscored):
    client, scorer, svc = unscored
    case_id = svc.queue()[0].case.case_id
    r = client.get(f"/cases/{case_id}/now")
    assert r.status_code == 200
    assert scorer.waits == 1
    assert 'id="now"' in r.text
    assert "<header class=\"bar\"" not in r.text  # a fragment, not a whole page
