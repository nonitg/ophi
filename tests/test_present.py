"""Glance layer: the sentence, the bar and the lead line the templates render. Page-level coverage is in test_web."""

from __future__ import annotations

import pytest

from ophi.service import CaseService, Store
from ophi.web import present


@pytest.fixture
def svc(tmp_path):
    return CaseService(store=Store(tmp_path / "state"))


def test_headline_counts_gaps_and_criteria_in_plain_words(svc):
    view = svc.view("singh")
    head = present.headline(view, present.gap_groups(view))
    assert head["title"] == "Not ready to submit."
    assert head["sub"] == "1 chart gap and 9 clinical criteria for Dr. Priya Lau to confirm before the packet can go out."
    assert [c["label"] for c in present.gap_groups(view)["confirms"]][-1] == "Restorability criteria confirmed by the treating dentist (7 criteria)"


def test_headline_pluralises_each_kind_of_work(svc):
    view = svc.view("rosco")
    sub = present.headline(view, present.gap_groups(view))["sub"]
    assert "3 items the connected source cannot see" in sub
    assert "1 chart finding to confirm" in sub


def test_queue_lead_prefers_chart_work_and_hides_internal_ids(svc):
    lead = present.queue_lead(svc.view("tremblay"))
    assert lead["title"] == "Confirm: Treatment plan details stated in the clinical note"
    assert lead["more"] == 4
    assert present.queue_lead(svc.view("whitfield")) is None


def test_segments_cover_every_applicable_requirement(svc):
    a = svc.view("singh").assessment
    segs = present.segments(a)
    assert len(segs) == a.completeness["applicable"] == 13
    assert [s["cls"] for s in segs].count("ok") == a.completeness["satisfied"] == 9
    assert present.completeness_parts(a) == [{"cls": "bad", "text": "1 missing or stale"}, {"cls": "ask", "text": "3 awaiting the dentist"}]
