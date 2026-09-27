"""Drafting a pack update from a source check: only stated code replacements are applied, and anything
ambiguous is left for a person, never guessed."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from ophi.rules import draft as draft_mod
from ophi.rules import watch
from ophi.rules.draft import Change, DraftBlocked, DraftResult, extract
from ophi.rules.loader import load_pack
from tests._pack_watch import (  # noqa: F401 — cdcp and cases are fixtures
    BASE,
    NEW_DOC,
    PAGE,
    TODAY,
    WATCH,
    cases,
    cdcp,
    draft_fixture,
    fetcher,
    served,
)

SHIPPED = load_pack(Path(__file__).resolve().parents[1] / "packs" / "cdcp" / BASE / "pack.yaml")


def _pairs(changes: list[Change]) -> list[tuple[str, str]]:
    return [(c.old, c.new) for c in changes]


# --- extract ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("line", ["99112 -> 99122", "99112 → 99122", "99112 => 99122", "Code 99112 replaced by 99122",
                                  "Code 99112 is Replaced With 99122."])
def test_extract_reads_each_replacement_form(line: str):
    changes, unclear = extract("f", line)
    assert _pairs(changes) == [("99112", "99122")] and not unclear
    assert changes[0].quote == line and changes[0].source == "f"


def test_extract_pairs_codes_by_position():
    changes, unclear = extract("f", "Effective April 1, 2027\n99112, 99113 → 99122, 99123\n99001 -> 99002, 99003\n")
    assert [(c.old, c.new, c.effective_on) for c in changes] == [("99112", "99122", date(2027, 4, 1)),
                                                                 ("99113", "99123", date(2027, 4, 1))]
    assert len(unclear) == 1  # unequal lists are never guessed


@pytest.mark.parametrize("line", ["99112 -> 99122 -> 99132",  # two arrows: which is current?
                                  "99112, 99113 -> 99122",  # unequal lists
                                  "99112 replaced by a new code",  # no new code
                                  "Lab code 99112 retired",  # retired, no replacement
                                  "Code 27211 deleted from the grid"])
def test_extract_leaves_ambiguous_lines_for_a_person(line: str):
    changes, unclear = extract("f", line)
    assert changes == [] and len(unclear) == 1 and line in unclear[0]


def test_extract_ignores_arrows_without_codes_and_text_without_arrows():
    assert extract("f", "Fees -> increased\nCrowns need a PA radiograph.\n") == ([], [])


def test_extract_only_reads_the_lines_it_is_given():
    changes, _ = extract("f", "99222 -> 99112\n99112 -> 99122\n", only_lines={1})
    assert _pairs(changes) == [("99112", "99122")]


def test_added_lines_are_what_a_source_newly_says():
    assert draft_mod.added_lines("a\nb\nc\n", "a\nB\nc\nd\n") == {1, 3}


# --- effective date --------------------------------------------------------------------------------


def test_effective_date_is_the_nearest_stated_one():
    text = "Updated January 5, 2027\n\n\nNew codes effective 2027-04-01\n99112 -> 99122\n"
    assert extract("f", text)[0][0].effective_on == date(2027, 4, 1)


def test_a_nearby_date_that_is_not_called_effective_is_not_used():
    assert extract("f", "Published January 5, 2027\n99112 -> 99122\n")[0][0].effective_on is None


def test_a_date_on_an_unchanged_line_never_dates_a_new_change():
    text = "Effective April 1, 2026\n99112 -> 99122\n"
    assert extract("f", text, only_lines={1})[0][0].effective_on is None


def test_a_date_beyond_the_window_is_not_used():
    text = "Effective April 1, 2027\n" + "text\n" * draft_mod.DATE_WINDOW + "99112 -> 99122\n"
    assert extract("f", text)[0][0].effective_on is None


# --- scope and triage ------------------------------------------------------------------------------


def _triage(*pairs: tuple[str, str]) -> DraftResult:
    r = DraftResult()
    draft_mod._triage([Change(o, n, "f", f"{o} -> {n}", None) for o, n in pairs], SHIPPED, r)
    return r


def test_only_lab_codes_are_applied_crown_codes_go_to_a_person_sedation_is_out_of_scope():
    r = _triage(("99444", "99445"), ("27215", "27216"), ("92211", "92215"))
    assert _pairs(r.changes) == [("99444", "99445")]
    assert _pairs(r.out_of_scope) == [("92211", "92215")]
    assert len(r.needs_person) == 1 and "crown code 27215" in r.needs_person[0]


def test_a_replacement_the_pack_already_has_is_not_applied_again():
    r = _triage(("99222", "99112"))
    assert _pairs(r.already_in_pack) == [("99222", "99112")] and not r.changes and not r.needs_person


def test_a_conflict_with_the_pack_is_never_applied():
    r = _triage(("99222", "99999"))
    assert not r.changes and r.needs_person == ["f: says 99222 is replaced by 99999; the pack says 99112."]


def test_retiring_a_prior_replacement_carries_the_original_along():
    r = _triage(("99112", "99122"))
    assert _pairs(r.changes) == [("99112", "99122")] and not r.needs_person
    assert r.chains == ["99222 now resolves to 99122 through 99112"]


def test_retiring_a_schedule_b_crown_code_is_left_for_a_person():
    r = _triage(("27211", "27212"))
    assert not r.changes and any("crown code 27211" in x for x in r.needs_person)


# --- verify_quotes ---------------------------------------------------------------------------------


def test_a_quote_not_in_its_source_blocks_the_draft():
    good = Change("99112", "99122", "f", "99112 -> 99122", None)
    draft_mod.verify_quotes([good], {"f": "intro\n99112 -> 99122\n"})
    with pytest.raises(DraftBlocked, match="quote not found"):
        draft_mod.verify_quotes([good], {"f": "intro\n99112 -> 99123\n"})
    with pytest.raises(DraftBlocked):
        draft_mod.verify_quotes([good], {})  # source missing altogether


# --- draft -----------------------------------------------------------------------------------------


def test_draft_from_new_factsheet(cdcp: Path, cases: Path, tmp_path: Path):
    d = draft_fixture(cdcp, cases)
    assert _pairs(d.changes) == [("99112", "99122"), ("99113", "99123")]
    assert _pairs(d.out_of_scope) == [("92211", "92215"), ("92212", "92216")]
    assert "99222 now resolves to 99122 through 99112" in d.chains and d.needs_person == []
    pack = load_pack(d.dir / "pack.yaml")
    assert pack.effective_from == date(2027, 4, 1) and pack.supersedes == "2026.01.26"
    assert pack.version == "2026.09.26" and pack.verified_on == TODAY and pack.reviewed_by is None
    assert "factsheet_2026_09_26" in pack.sources
    added = [r for r in pack.schedule.retired_codes if r.effective_on]
    assert [(r.code, r.replaced_by, r.clause.source) for r in added] == [("99112", "99122", "factsheet_2026_09_26"),
                                                                         ("99113", "99123", "factsheet_2026_09_26")]
    assert added[0].clause.quote in (d.dir / "sources" / "factsheet_2026_09_26.txt").read_text()
    assert "## Impact" in (d.dir / "report.md").read_text()
    assert json.loads((d.dir / "draft.json").read_text())["needs_person"] == []


def test_the_draft_keeps_the_smes_comments(cdcp: Path, cases: Path, tmp_path: Path):
    before = (cdcp / BASE / "pack.yaml").read_text()
    after = (draft_fixture(cdcp, cases).dir / "pack.yaml").read_text()
    comments = [x.strip() for x in before.splitlines() if x.strip().startswith("#")]
    assert comments and all(c in after for c in comments)


def test_impact_lists_only_cases_whose_result_changes(cdcp: Path, cases: Path, tmp_path: Path):
    d = draft_fixture(cdcp, cases)
    assert d.cases == 3
    assert len(d.impact) == 1 and d.impact[0].startswith("adversarial/current_lab_code.yaml:")  # 99113 retires
    assert "lab_codes_current satisfied -> unsatisfied" in d.impact[0]
    assert "1 of 3 cases change." in d.report_md


def _check_with_factsheet(cdcp: Path, factsheet: str) -> tuple[watch.CheckReport, object]:
    """A check where the pack's own factsheet source now also says `factsheet`, and no new documents appeared."""
    pack_dir = cdcp / BASE
    snap = (pack_dir / "sources" / "factsheet.txt").read_bytes()
    get = fetcher(served(pack_dir, page=b"<html></html>", factsheet=snap + factsheet.encode()))
    return watch.check(pack_dir, TODAY, get, config=WATCH), get


def test_nothing_relevant_changed_writes_no_draft(cdcp: Path, cases: Path, tmp_path: Path):
    report, get = _check_with_factsheet(cdcp, "Sedation codes 92211 replaced by 92215, effective April 1, 2027\n")
    d = draft_mod.draft(report, TODAY, get, cases_dir=cases, drafts_dir=tmp_path / "drafts")
    assert d.dir is None and not (tmp_path / "drafts").exists()
    assert _pairs(d.out_of_scope) == [("92211", "92215")] and "no draft written" in d.report_md


def test_a_change_with_no_stated_date_takes_effect_today_and_is_flagged(cdcp: Path, cases: Path, tmp_path: Path):
    report, get = _check_with_factsheet(cdcp, "text\n" * 5 + "Lab code 99444 -> 99445\n")  # clear of the old dates
    d = draft_mod.draft(report, TODAY, get, cases_dir=cases, drafts_dir=tmp_path / "drafts")
    assert load_pack(d.dir / "pack.yaml").effective_from == TODAY
    assert any("No effective date is stated" in x for x in d.needs_person)


def test_changes_on_different_dates_take_the_latest_and_are_flagged(cdcp: Path, cases: Path, tmp_path: Path):
    report, get = _check_with_factsheet(cdcp, "Effective April 1, 2027\nLab code 99444 -> 99445\n"
                                              + "text\n" * 9 + "Effective 2027-07-01\nLab code 99446 -> 99447\n")
    d = draft_mod.draft(report, TODAY, get, cases_dir=cases, drafts_dir=tmp_path / "drafts")
    assert [c.effective_on for c in d.changes] == [date(2027, 4, 1), date(2027, 7, 1)]
    assert load_pack(d.dir / "pack.yaml").effective_from == date(2027, 7, 1)
    assert any("different dates" in x for x in d.needs_person)


def test_a_changed_source_without_code_changes_is_left_for_a_person(cdcp: Path, cases: Path, tmp_path: Path):
    report, get = _check_with_factsheet(cdcp, "Crowns on primary teeth now need a PA radiograph.\n")
    d = draft_mod.draft(report, TODAY, get, cases_dir=cases, drafts_dir=tmp_path / "drafts")
    assert not d.changes and any("factsheet changed but states no code replacement" in x for x in d.needs_person)
    assert "+Crowns on primary teeth now need a PA radiograph." in d.report_md  # the diff is shown for reading


def test_an_effective_date_before_the_current_pack_is_flagged(cdcp: Path, cases: Path, tmp_path: Path):
    report, get = _check_with_factsheet(cdcp, "Effective January 1, 2026\nLab code 99444 -> 99445\n")
    d = draft_mod.draft(report, TODAY, get, cases_dir=cases, drafts_dir=tmp_path / "drafts")
    assert load_pack(d.dir / "pack.yaml").effective_from < SHIPPED.effective_from  # the precondition
    assert any("2026-04-01" in x for x in d.needs_person)


def test_a_change_dated_today_or_earlier_is_flagged(cdcp: Path, cases: Path, tmp_path: Path):
    report, get = _check_with_factsheet(cdcp, "Effective September 1, 2026\nLab code 99444 -> 99445\n")
    d = draft_mod.draft(report, TODAY, get, cases_dir=cases, drafts_dir=tmp_path / "drafts")
    assert any("in the past" in x for x in d.needs_person)
    assert json.loads((d.dir / "draft.json").read_text())["needs_person"] == d.needs_person


def test_a_new_document_with_nothing_for_this_pack_is_marked_seen(cdcp: Path, cases: Path, tmp_path: Path):
    pack_dir = cdcp / BASE
    web = served(pack_dir)
    web[NEW_DOC] = b"Sedation codes 92211 -> 92215, effective April 1, 2027\n"
    get = fetcher(web)
    d = draft_mod.draft(watch.check(pack_dir, TODAY, get, config=WATCH), TODAY, get, cases_dir=cases,
                        drafts_dir=tmp_path / "drafts")
    assert d.dir is None and not watch.check(pack_dir, TODAY, get, config=WATCH).new_links


def test_a_replacement_by_a_retired_code_goes_to_a_person():
    r = _triage(("99444", "99222"))
    assert not r.changes and "the pack retires 99222" in r.needs_person[0]


def test_a_new_pack_drops_the_2026_only_lab_code_copy(cdcp: Path, cases: Path):
    text = (draft_fixture(cdcp, cases).dir / "pack.yaml").read_text()
    assert "2026 date of service" not in text and "invalid for 2026 dates" not in text
    assert "Laboratory fee codes are valid for the date of service" in text
