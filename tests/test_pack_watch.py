"""Source watch: a CDCP publication becomes a reviewed pack version, never an automatic one.

This file covers text normalization, the source check, the board's status line and which pack is in force.
Drafting is in test_pack_draft.py, approval in test_pack_approve.py.
"""

from __future__ import annotations

import re
import shutil
from datetime import date
from pathlib import Path

import pytest

from ophi.casegen.dsl import load_case
from ophi.rules import loader, watch
from ophi.rules.loader import load_pack, pack_in_force
from ophi.web.present import rules_check
from tests._pack_watch import (  # noqa: F401 — cdcp is a fixture
    BASE,
    FIX,
    NEW_DOC,
    PAGE,
    TODAY,
    WATCH,
    cdcp,
    fetcher,
    served,
)

PAGE_HTML = """<!DOCTYPE html><html lang="en"><head><title>Guide</title><script>var v = "{nonce}";</script></head>
<body><nav><a href="/en.html">Home {nonce}</a></nav><main>
<h1>CDCP Dental Benefits Guide</h1>
<p>Crowns   require preauthorization.</p>{extra}
<gcds-date-modified>{stamp}</gcds-date-modified>
<p>Date modified: {stamp}</p>
</main><footer>Terms {nonce}</footer></body></html>"""


def _page(nonce="a1", stamp="2026-01-26", extra="") -> bytes:
    return PAGE_HTML.format(nonce=nonce, stamp=stamp, extra=extra).encode()


# --- normalize and fingerprint ---------------------------------------------------------------------


def test_to_text_keeps_visible_text_only():
    text = watch.to_text((FIX / "new-factsheet.html").read_bytes())
    assert "99112, 99113 → 99122, 99123" in text
    assert "dataLayer" not in text and "Terms and conditions" not in text and "2027-02-10" not in text


def test_chrome_whitespace_and_date_stamp_churn_keep_the_fingerprint():
    a = watch.fingerprint(watch.to_text(_page()))
    churned = _page(nonce="zz99", stamp="2026-09-26").replace(b"<p>", b'<p class="x"  >').replace(b"\n", b"\r\n  ")
    assert watch.fingerprint(watch.to_text(churned)) == a


def test_a_real_text_change_moves_the_fingerprint():
    a = watch.fingerprint(watch.to_text(_page()))
    b = watch.fingerprint(watch.to_text(_page(extra="<p>Bridges require preauthorization.</p>")))
    assert a != b


def test_wet_date_modified_footer_churn_keeps_the_fingerprint():
    def wet(stamp: str) -> bytes:
        return (f"<!DOCTYPE html><html><body><main><p>Crowns require preauthorization.</p>"
                f"<dl id=\"wb-dtmd\"><dt>Date modified:</dt><dd><time>{stamp}</time></dd></dl></main></body></html>").encode()
    assert watch.to_text(wet("2026-01-26")) == watch.to_text(wet("2026-09-26"))


def test_a_missing_head_close_does_not_blank_the_page():
    assert "Crowns need a PA." in watch.to_text(b"<html><head><title>T</title><body><p>Crowns need a PA.</p></body></html>")


def test_a_header_inside_main_is_content_the_page_header_is_not():
    html = b"<html><body><header>Canada.ca menu</header><main><header><h1>6.3.5 Crowns</h1></header></main></body></html>"
    text = watch.to_text(html)
    assert "6.3.5 Crowns" in text and "menu" not in text


# --- discovery -------------------------------------------------------------------------------------


def test_page_links_keeps_english_documents_only():
    html = b"""<html><body>
    <a href="/en/services/benefits/dental/dental-care-plan/providers/bulletin-may-2027.html">Provider bulletin</a>
    <a href="https://www.canada.ca/content/dam/x/dental/cdcp-guide-2027-fr.pdf">Guide (PDF, French)</a>
    <a href="/fr/services/prestations/dentaire/fournisseurs/fact-sheet.html">Fiche</a>
    <a href="/en/services/benefits/dental/dental-care-plan/providers/toolkit.html">Promotional toolkit</a>
    <a href="/en/services/benefits/dental/dental-care-plan/apply.html">Apply for the plan</a>
    <a href="#main">Skip to content</a>
    <a href="mailto:cdcp@example.ca">Guide questions</a>
    </body></html>"""
    assert watch.page_links(html, PAGE) == {
        "https://www.canada.ca/en/services/benefits/dental/dental-care-plan/providers/bulletin-may-2027.html":
            "Provider bulletin"}


# --- check -----------------------------------------------------------------------------------------


def test_check_reports_unchanged_sources_and_a_new_document(cdcp: Path):
    r = watch.check(cdcp / BASE, TODAY, fetcher(served(cdcp / BASE)), config=WATCH)
    assert {s.state for s in r.sources} == {"unchanged"}
    assert [n.url for n in r.new_links] == [NEW_DOC]  # guide already a source; toolkit and French pages ignored
    assert r.new_links[0].found_on == PAGE and r.pending


def test_check_tells_changed_unchanged_and_unreachable_apart(cdcp: Path):
    pack_dir = cdcp / BASE
    web = served(pack_dir, page=b"<html><body></body></html>",
                 guide=(pack_dir / "sources" / "guide.txt").read_bytes() + b"Crowns on implants need a PA film.\n")
    del web[load_pack(pack_dir / "pack.yaml").sources["grid"].url]
    r = watch.check(pack_dir, TODAY, fetcher(web), config=WATCH)
    states = {s.key: s.state for s in r.sources}
    assert states == {"matrix": "unchanged", "guide": "changed", "grid": "unreachable", "factsheet": "unchanged"}
    assert "+Crowns on implants need a PA film." in r.changed[0].diff
    assert [s.key for s in r.unreachable] == ["grid"] and r.unreachable[0].error


def test_unreachable_sources_and_pages_never_count_as_a_change(cdcp: Path):
    r = watch.check(cdcp / BASE, TODAY, fetcher({}), config=WATCH)
    assert {s.state for s in r.sources} == {"unreachable"} and r.unreachable_pages == [PAGE]
    assert not r.changed and not r.new_links and not r.pending


def test_an_empty_page_is_unreachable_a_much_shorter_one_shrank(cdcp: Path):
    pack_dir = cdcp / BASE
    guide = (pack_dir / "sources" / "guide.txt").read_bytes()
    get = fetcher(served(pack_dir, guide=guide[:len(guide) // 4], matrix=b"<html></html>"))
    r = watch.check(pack_dir, TODAY, get, config=watch.Watch([]))
    states = {s.key: s.state for s in r.sources}
    assert states["matrix"] == "unreachable" and states["guide"] == "shrank" and r.pending
    with pytest.raises(watch.BaselineRefused):
        watch.baseline(pack_dir, TODAY, get, config=watch.Watch([]))
    watch.baseline(pack_dir, TODAY, get, config=watch.Watch([]), force=True)  # a person read it: take it
    assert (pack_dir / "sources" / "guide.txt").read_text() == watch.normalize(guide[:len(guide) // 4].decode())


def test_a_manual_source_is_not_fetched_until_a_copy_is_given(cdcp: Path, tmp_path: Path):
    pack_dir = cdcp / BASE
    web = served(pack_dir)
    grid = web.pop(load_pack(pack_dir / "pack.yaml").sources["grid"].url)
    config = watch.Watch([], {"grid": "Sun Life grid"})
    r = watch.check(pack_dir, TODAY, fetcher(web), config)
    s = next(x for x in r.sources if x.key == "grid")
    assert s.state == "manual" and s.last_read == "2026-09-26" and not r.unreachable
    (tmp_path / "grid.pdf").write_bytes(grid)
    r = watch.check(pack_dir, date(2026, 10, 3), fetcher(web), config, files={"grid": tmp_path / "grid.pdf"})
    status = watch.save_status(r, tmp_path / "status.json")
    assert status["manual"] == [{"key": "grid", "label": "Sun Life grid", "checked_on": "2026-10-03"}]
    assert rules_check(status)[1] == "Sun Life grid last checked by hand on Oct 3, 2026."


def test_no_pages_means_none_are_scanned(cdcp: Path):
    r = watch.check(cdcp / BASE, TODAY, fetcher(served(cdcp / BASE)), config=watch.Watch([]))
    assert not r.new_links and not r.unreachable_pages


def test_baseline_refuses_to_absorb_a_pending_change(cdcp: Path):
    pack_dir = cdcp / BASE
    with pytest.raises(watch.BaselineRefused, match="fact-sheet-guide-grids-april-2027"):
        watch.baseline(pack_dir, TODAY, fetcher(served(pack_dir)), config=WATCH)
    watch.baseline(pack_dir, TODAY, fetcher(served(pack_dir)), config=WATCH, force=True)


def test_baseline_keeps_an_unreachable_source_as_it_was(cdcp: Path):
    pack_dir = cdcp / BASE
    before = watch.read_lock(pack_dir)["sources"]["grid"]
    web = served(pack_dir)
    del web[load_pack(pack_dir / "pack.yaml").sources["grid"].url]
    watch.baseline(pack_dir, date(2026, 10, 1), fetcher(web), config=watch.Watch([]))
    after = watch.read_lock(pack_dir)["sources"]
    assert after["grid"] == before and after["guide"]["fetched_on"] == "2026-10-01"


def test_links_seen_at_baseline_are_not_new(cdcp: Path):
    pack_dir = cdcp / BASE
    get = fetcher(served(pack_dir))
    watch.baseline(pack_dir, TODAY, get, config=WATCH, force=True)
    r = watch.check(pack_dir, TODAY, get, config=WATCH)
    assert not r.new_links and not r.pending
    assert NEW_DOC in watch.read_lock(pack_dir)["seen_links"]


def test_long_diffs_are_cut_with_a_count():
    diff = watch.text_diff("", "\n".join(f"line {i}" for i in range(100)), "guide")
    assert len(diff.splitlines()) == watch.DIFF_LINES + 1 and diff.endswith("more diff lines")


# --- status for the board --------------------------------------------------------------------------


def _report(day: date, state: str = "changed") -> watch.CheckReport:
    return watch.CheckReport("p", "2026.01.26", day, [watch.SourceCheck("guide", "u", state)], [], [])


def test_board_line_reads_the_status_file(tmp_path: Path):
    status = watch.save_status(_report(TODAY), tmp_path / "status.json")
    assert rules_check(status) == ["Rules checked against CDCP sources on Sep 26, 2026.",
                                   "CDCP published changes on Sep 26, 2026. A rule update is waiting for review."]


def test_found_on_holds_the_first_day_until_reviewed(tmp_path: Path):
    path = tmp_path / "status.json"
    watch.save_status(_report(date(2026, 9, 26)), path)
    assert watch.save_status(_report(date(2026, 9, 30)), path)["found_on"] == "2026-09-26"
    watch.mark_reviewed(path)
    assert watch.load_status(path)["pending"] is False
    assert watch.save_status(_report(date(2026, 10, 2)), path)["found_on"] == "2026-10-02"


def test_the_board_says_when_sources_could_not_be_reached(tmp_path: Path):
    status = watch.save_status(_report(TODAY, "unreachable"), tmp_path / "status.json")
    assert rules_check(status) == ["Could not reach 1 CDCP source on Sep 26, 2026."]


def test_a_broken_status_file_reads_as_no_status(tmp_path: Path):
    (tmp_path / "status.json").write_text("{not json")
    assert watch.load_status(tmp_path / "status.json") is None and watch.load_status(tmp_path / "missing.json") is None
    assert rules_check({"pending": True}) == []


def test_board_line_never_claims_approval_or_coverage(tmp_path: Path):
    lines = rules_check(watch.save_status(_report(TODAY), tmp_path / "a.json"))
    lines += rules_check(watch.save_status(_report(TODAY, "unreachable"), tmp_path / "b.json"))
    assert rules_check(None) == []
    assert not re.search(r"\b(approved?|eligible|covered|coverage)\b", " ".join(lines), re.I)


# --- which pack is in force ------------------------------------------------------------------------


def _future_pack(cdcp: Path, version: str = "2026.09.26", effective: str = "2027-04-01") -> Path:
    """An approved pack dated after the shipped one, as `ophi pack approve` leaves it."""
    target = cdcp / version.replace(".", "-")
    shutil.copytree(cdcp / BASE, target)
    text = (target / "pack.yaml").read_text()
    text = re.sub(r"^version:.*$", f'version: "{version}"', text, count=1, flags=re.M)
    text = re.sub(r"^effective_from:.*$", f"effective_from: {effective}", text, count=1, flags=re.M)
    (target / "pack.yaml").write_text(text)
    return target


def test_pack_in_force_waits_for_a_future_dated_pack(cdcp: Path):
    _future_pack(cdcp)
    assert pack_in_force(date(2026, 4, 1), cdcp).version == "2026.01.26"
    assert pack_in_force(date(2027, 3, 31), cdcp).version == "2026.01.26"
    assert pack_in_force(date(2027, 4, 1), cdcp).version == "2026.09.26"
    assert pack_in_force(date(2028, 1, 1), cdcp).version == "2026.09.26"
    assert pack_in_force(date(2026, 3, 31), cdcp).version == "2026.01.26"  # before the first pack: the first pack


def test_on_equal_effective_dates_the_later_pack_wins(cdcp: Path):
    _future_pack(cdcp, effective="2026-04-01")
    assert pack_in_force(date(2026, 9, 26), cdcp).version == "2026.09.26"


def test_default_pack_cache_does_not_leak_across_dates(cdcp: Path, monkeypatch):
    assert loader.default_pack(date(2027, 4, 1), cdcp).version == "2026.01.26"
    _future_pack(cdcp)  # approved while the process runs: picked up without a restart
    assert loader.default_pack(date(2027, 3, 31), cdcp).version == "2026.01.26"
    assert loader.default_pack(date(2027, 4, 1), cdcp).version == "2026.09.26"

    class Tomorrow(date):
        @classmethod
        def today(cls):
            return date(2027, 4, 1)

    monkeypatch.setattr(loader, "date", Tomorrow)
    assert loader.default_pack(cdcp_dir=cdcp).version == "2026.09.26"  # a long-running process picks up the pack on its day


def test_before_the_first_pack_the_first_pack_stands_in(cdcp: Path):
    assert loader.default_pack(date(2025, 9, 23), cdcp).version == "2026.01.26"


def test_each_request_takes_the_pack_for_its_own_date(cdcp: Path):
    _future_pack(cdcp)
    case = load_case(Path(__file__).resolve().parents[1] / "cases" / "adversarial" / "current_lab_code.yaml")
    seated = case.model_copy(update={"as_of": date(2027, 3, 25), "treatment": case.treatment.model_copy(
        update={"planned_date": date(2027, 3, 20), "appointment_date": date(2027, 4, 15)})})
    assert loader.pack_for(case, cdcp).version == "2026.01.26"
    assert loader.pack_for(seated, cdcp).version == "2026.09.26"  # the date of service, not when the plan was written
    unbooked = seated.model_copy(update={"treatment": seated.treatment.model_copy(update={"appointment_date": None})})
    assert loader.pack_for(unbooked, cdcp).version == "2026.01.26"  # the chart's date, not the older plan date


def test_a_pack_that_does_not_load_is_skipped_but_none_loading_fails(cdcp: Path):
    broken = cdcp / "2026-12-01"
    broken.mkdir()
    (broken / "pack.yaml").write_text("version: [not a pack")
    assert pack_in_force(date(2027, 1, 1), cdcp).version == "2026.01.26"
    (cdcp / BASE / "pack.yaml").write_text("nope")
    with pytest.raises(FileNotFoundError):
        pack_in_force(date(2027, 1, 1), cdcp)


def test_a_replacement_loop_does_not_load(cdcp: Path):
    path = cdcp / BASE / "pack.yaml"
    loop = '    - { code: "99112", replaced_by: "99222", clause: { source: factsheet, ref: "loop" } }\n'
    path.write_text(re.sub(r"(  retired_codes:\n)", r"\1" + loop, path.read_text(), count=1))
    with pytest.raises(ValueError, match="loops through"):
        load_pack(path)


def test_a_malformed_status_renders_nothing():
    assert rules_check({"checked_on": "yesterday"}) == []
    assert rules_check({"checked_on": "2026-09-26", "manual": ["grid"]}) == []
