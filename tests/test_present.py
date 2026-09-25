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
    assert "3 items Ophi cannot verify" in sub
    assert "1 chart finding to confirm" in sub


def test_queue_lead_prefers_chart_work_and_hides_internal_ids(svc):
    lead = present.queue_lead(svc.view("tremblay"))
    assert lead["title"] == "Confirm: Treatment plan details stated in the clinical note"
    assert lead["more"] == 4
    assert present.queue_lead(svc.view("whitfield")) is None


def test_strip_covers_every_pack_requirement_grouped_by_family(svc):
    a = svc.view("singh").assessment
    fams = present.strip(a)
    cells = [c for f in fams for c in f["cells"]]
    assert [f["family"] for f in fams] == ["Chart", "Limits", "Clinical"]
    assert len(cells) == len(a.requirements)  # N/A cells keep queue columns aligned
    applicable = [c for c in cells if c["applicable"]]
    assert len(applicable) == a.completeness["applicable"] == 13
    assert [c["cls"] for c in applicable].count("ok") == a.completeness["satisfied"] == 9
    assert present.completeness_parts(a) == [{"cls": "bad", "text": "1 missing or stale"}, {"cls": "ask", "text": "3 awaiting the dentist"}]


def test_unseen_imaging_reads_cannot_verify_not_awaiting_the_dentist(svc):
    view = svc.view("rosco")
    cells = {c["id"]: c for f in present.strip(view.assessment) for c in f["cells"]}
    assert cells["radiograph_pa"]["status"] == "Cannot verify"
    assert cells["restorability"]["status"] == "Awaiting dentist"
    assert {"cls": "unknown", "text": "3 cannot verify"} in present.completeness_parts(view.assessment)
    lanes = {lane["key"]: lane for lane in present.chart_timeline(view)["lanes"]}
    assert lanes["pa"]["unseen"] and not lanes["perio"]["unseen"]  # imaging is Unknown; perio is a confirmed gap


def test_stage_names_where_each_case_stands(svc):
    assert [present.stage(svc.view(c))["label"] for c in ("singh", "tremblay", "whitfield")] == ["Blocked", "Needs input", "Ready to sign"]


def test_waiting_on_splits_open_work_by_who_acts(svc):
    assert [(p["initials"], p["what"]) for p in present.waiting_on(svc.view("singh"))] == [("KO", "1 chart gap"), ("PL", "9 clinical criteria")]
    assert [p["what"] for p in present.waiting_on(svc.view("tremblay"))] == ["1 chart finding to confirm", "10 clinical criteria"]
    assert [p["what"] for p in present.waiting_on(svc.view("whitfield"))] == ["1 packet to sign"]


def test_inbox_counts_what_the_person_acting_owes(svc):
    views = svc.queue()
    dentist = {t["kind"]: t for t in present.inbox(views, present.ACTORS["dentist"])}
    assert dentist["packet to sign"]["cases"] == ["Dana Whitfield"]
    assert dentist["clinical criterion"]["text"] == "46 clinical criteria"
    assert dentist["clinical step"]["cases"] == ["Mei Deng"]  # the pending filling on #47 is clinical work
    assert {t["text"] for t in present.inbox(views, present.ACTORS["coordinator"])} == {
        "6 chart gaps", "3 items Ophi cannot verify", "2 chart findings to confirm"}


def test_documented_rows_name_the_evidence_its_age_and_who_produced_it(svc):
    rows = {d["id"]: d for d in present.documented(svc.view("singh"))}
    assert "radiograph_pa" not in rows  # open requirements stay in the work lanes
    assert (rows["radiograph_bw"]["age"], rows["radiograph_bw"]["source"]) == (46, "chart")
    assert rows["client_age"]["source"] == "ophi"
    assert {d["id"]: d for d in present.documented(svc.view("whitfield"))}["restorability"]["what"] == "7 criteria confirmed by Dr. Priya Lau"


def test_timeline_puts_the_stale_periapical_outside_the_12_month_window(svc):
    tl = present.chart_timeline(svc.view("kowalchuk"))
    pa = next(lane for lane in tl["lanes"] if lane["key"] == "pa")["points"][0]
    assert pa["stale"] and pa["x"] < tl["window_x"] < tl["today_x"]


def test_lookback_months_hold_every_request_and_gaps_rank_the_missing_documents():
    from ophi.lookback import run_lookback
    rep = run_lookback()
    assert sum(len(m["rows"]) for m in present.lookback_months(rep)) == rep.submitted
    top = present.lookback_gaps(rep)[0]
    assert (top["label"], top["count"], top["pct"]) == ("Dated complete periodontal chart, within 12 months", 7, 100)


def test_a_not_met_answer_stays_with_the_dentist_and_hides_no_other_criterion(svc):
    svc.assert_criterion("singh", "ferrule_1_5mm", "not_met", "Dr. Priya Lau", "ON-48213")
    gaps = present.gap_groups(svc.view("singh"))
    assert [w["action"].action_type for w in gaps["clinical"]] == ["criterion_not_met"]
    assert gaps["criteria_pending"] == 8  # 6 restorability criteria still unanswered, plus basic treatment and extensively restored
    assert [p["what"] for p in present.waiting_on(svc.view("singh"))] == ["1 chart gap", "1 clinical step and 8 clinical criteria"]


def test_unseen_sections_never_read_as_empty(svc, tmp_path):
    from ophi.service import ROOT, CaseService, Store
    assert present.evidence_panel(svc.view("rosco"))["empty"]["imaging"] == "Not visible to the connected source (Unknown)."
    adversarial = CaseService(cases_dir=ROOT / "cases" / "adversarial", store=Store(tmp_path / "adv"))
    empty = present.evidence_panel(adversarial.view("history_unknown"))["empty"]
    assert empty["procedure_history"].startswith("Not visible") and empty["imaging"] == "None in the chart."


def test_timeline_window_follows_the_engine_recency_rule(svc, tmp_path):
    from ophi.service import ROOT, CaseService, Store
    view = CaseService(cases_dir=ROOT / "cases" / "adversarial", store=Store(tmp_path / "adv")).view("pa_leap_band")
    tl = present.chart_timeline(view)
    pa = next(lane for lane in tl["lanes"] if lane["key"] == "pa")["points"][0]
    assert pa["risk"] and pa["x"] >= tl["window_x"]  # at risk between conventions, still inside the window


def test_stage_rail_counts_cases_and_dollars_per_stage(svc):
    rail = {s["key"]: s for s in present.stage_rail(svc.queue())}
    assert (rail["blocked"]["count"], rail["needs"]["count"], rail["ready"]["count"], rail["signed"]["count"]) == (4, 1, 1, 0)
    assert rail["ready"]["dollars"] == svc.view("whitfield").dollars_at_risk


def test_handoff_opens_sign_off_only_once_documented(svc):
    assert (present.handoff(svc.view("singh"))["sign"], present.handoff(svc.view("whitfield"))["sign"]) == ("locked", "ready")
