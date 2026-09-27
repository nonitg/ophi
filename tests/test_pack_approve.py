"""Approving a draft: a named person turns it into a new pack version; older packs are never touched, and the
pack in force (and so Ophi's own fixes) switches only on the new version's effective date."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import date
from pathlib import Path

import pytest

from ophi import cli, fixes
from ophi.casegen.dsl import load_case
from ophi.engine.assess import assess
from ophi.extract.proposer import propose_for_case
from ophi.rules import approve as approve_mod
from ophi.rules import watch
from ophi.rules.draft import DraftBlocked
from ophi.rules.loader import load_pack, pack_in_force
from tests._pack_watch import (  # noqa: F401 — cdcp, cases and status are fixtures
    BASE,
    PAGE,
    ROOT,
    TODAY,
    WATCH,
    cases,
    cdcp,
    draft_fixture,
    fetcher,
    served,
    status,
)

NEW = "2026-09-26"
BEFORE, ON = date(2027, 3, 31), date(2027, 4, 1)


def _hashes(d: Path) -> dict[str, str]:
    return {str(p.relative_to(d)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.rglob("*")) if p.is_file()}


@pytest.fixture
def drafted(cdcp: Path, cases: Path, tmp_path: Path, status: Path) -> Path:
    """The April 2027 factsheet draft, with the board showing it as pending."""
    d = draft_fixture(cdcp, cases)
    watch.save_status(watch.CheckReport(str(cdcp / BASE), "2026.01.26", TODAY, [], [watch.NewLink("u", "t", PAGE)], []),
                      status)
    return d.dir


def test_approval_needs_a_name(drafted: Path, cdcp: Path):
    with pytest.raises(ValueError, match="name"):
        approve_mod.approve(drafted, "   ", TODAY, cdcp_dir=cdcp)
    assert drafted.exists() and not (cdcp / NEW).exists()


def test_approve_writes_a_new_version_and_leaves_the_old_one_alone(drafted: Path, cdcp: Path, status: Path):
    old = _hashes(cdcp / BASE)
    draft_lock = (drafted / watch.LOCK_NAME).read_text()
    target = approve_mod.approve(drafted, "  Dr. Maya Chen ", TODAY, cdcp_dir=cdcp, status=status)

    assert target == cdcp / NEW and _hashes(cdcp / BASE) == old
    pack = load_pack(target / "pack.yaml")
    assert (pack.reviewed_by, pack.reviewed_on, pack.supersedes) == ("Dr. Maya Chen", TODAY, "2026.01.26")
    assert (target / watch.LOCK_NAME).read_text() == draft_lock
    assert {p.name for p in (target / "sources").iterdir()} == {"matrix.txt", "guide.txt", "grid.txt", "factsheet.txt",
                                                                "factsheet_2026_09_26.txt"}
    assert (target / "denial_map.yaml").read_bytes() == (cdcp / BASE / "denial_map.yaml").read_bytes()
    assert (cdcp / "CHANGELOG.md").read_text().endswith(
        "- 2026-09-26: 2026.09.26 (effective 2027-04-01, from 2026.01.26) reviewed by Dr. Maya Chen: "
        "99112 -> 99122, 99113 -> 99123\n")
    assert not drafted.exists()
    assert json.loads(status.read_text())["pending"] is False


def test_an_approved_pack_waits_for_its_effective_date(drafted: Path, cdcp: Path):
    approve_mod.approve(drafted, "Dr. Maya Chen", TODAY, cdcp_dir=cdcp)
    assert pack_in_force(BEFORE, cdcp).version == "2026.01.26"
    assert pack_in_force(ON, cdcp).version == "2026.09.26"


def test_a_quote_edited_after_drafting_blocks_approval(drafted: Path, cdcp: Path):
    text = (drafted / "pack.yaml").read_text()
    (drafted / "pack.yaml").write_text(text.replace("99112, 99113 → 99122, 99123", "99112, 99113 → 99122, 99124", 1))
    with pytest.raises(DraftBlocked, match="quote not found"):
        approve_mod.approve(drafted, "Dr. Maya Chen", TODAY, cdcp_dir=cdcp)
    assert not (cdcp / NEW).exists() and drafted.exists()


def test_an_existing_version_is_never_overwritten(drafted: Path, cdcp: Path):
    (cdcp / NEW).mkdir()
    (cdcp / NEW / "pack.yaml").write_text("keep")
    with pytest.raises(DraftBlocked, match="already exists"):
        approve_mod.approve(drafted, "Dr. Maya Chen", TODAY, cdcp_dir=cdcp)
    assert (cdcp / NEW / "pack.yaml").read_text() == "keep"


def test_a_retirement_added_without_a_quote_blocks_approval(drafted: Path, cdcp: Path):
    text = (drafted / "pack.yaml").read_text()
    unquoted = '    - { code: "99555", replaced_by: "99556", clause: { source: factsheet, ref: "added by hand" } }\n'
    (drafted / "pack.yaml").write_text(re.sub(r"(  retired_codes:\n)", r"\1" + unquoted, text, count=1))
    with pytest.raises(DraftBlocked):
        approve_mod.approve(drafted, "Dr. Maya Chen", TODAY, cdcp_dir=cdcp)


# --- Ophi's own fix follows the pack in force ------------------------------------------------------


def _assess(case, pack):
    return assess(case.with_artifacts(propose_for_case(case)), pack)


def _lab_result(case, pack):
    return next(r for r in _assess(case, pack).requirements if r.requirement_id == "lab_codes_current")


def test_the_lab_code_fix_follows_the_pack_in_force(drafted: Path, cdcp: Path):
    approve_mod.approve(drafted, "Dr. Maya Chen", TODAY, cdcp_dir=cdcp)
    case = load_case(ROOT / "cases" / "adversarial" / "current_lab_code.yaml")  # lab code 99113
    before, on = pack_in_force(BEFORE, cdcp), pack_in_force(ON, cdcp)

    assert _lab_result(case, before).status.value == "satisfied" and fixes.title(case, "lab_codes_current", before) == ""
    r = _lab_result(case, on)
    assert r.status.value == "unsatisfied" and r.detail == "99113 was replaced by 99123 on 2027-04-01"
    assert fixes.title(case, "lab_codes_current", on) == "Replace lab code 99113 with 99123"
    fixed = fixes.apply(case, ["lab_codes_current"], on)
    assert fixed.treatment.lab_codes == ["99123"] and _lab_result(fixed, on).status.value == "satisfied"


def test_a_retirement_without_a_date_keeps_the_april_2026_detail(cdcp: Path):
    case = load_case(ROOT / "cases" / "adversarial" / "retired_lab_code.yaml")  # lab code 99333
    assert _lab_result(case, pack_in_force(TODAY, cdcp)).detail == "99333 was replaced by 99113 on 2026-04-01"


def test_the_lab_code_fix_follows_a_chain_of_replacements(drafted: Path, cdcp: Path):
    approve_mod.approve(drafted, "Dr. Maya Chen", TODAY, cdcp_dir=cdcp)
    on = pack_in_force(ON, cdcp)
    case = load_case(ROOT / "cases" / "adversarial" / "retired_lab_code.yaml")  # lab code 99333
    fixed = fixes.apply(case, ["lab_codes_current"], on)
    assert _lab_result(fixed, on).status.value == "satisfied"


# --- re-validation ---------------------------------------------------------------------------------


def _edit(drafted: Path, old: str, new: str) -> None:
    text = (drafted / "pack.yaml").read_text()
    assert old in text
    (drafted / "pack.yaml").write_text(text.replace(old, new, 1))


def test_a_hand_edited_replacement_blocks_approval(drafted: Path, cdcp: Path):
    _edit(drafted, 'replaced_by: "99122"', 'replaced_by: "99124"')  # the quote still says 99122
    with pytest.raises(DraftBlocked, match="differ from the reviewed"):
        approve_mod.approve(drafted, "Dr. Maya Chen", TODAY, cdcp_dir=cdcp)


def test_an_effective_date_not_after_the_parent_blocks_approval(drafted: Path, cdcp: Path):
    _edit(drafted, "effective_from: 2027-04-01", "effective_from: 2026-04-01")
    with pytest.raises(DraftBlocked, match="never be in force"):
        approve_mod.approve(drafted, "Dr. Maya Chen", TODAY, cdcp_dir=cdcp, ack=True)


def test_a_draft_of_an_older_pack_is_refused(drafted: Path, cdcp: Path):
    newer = cdcp / "2026-06-01"
    shutil.copytree(cdcp / BASE, newer)
    (newer / "pack.yaml").write_text((newer / "pack.yaml").read_text().replace('version: "2026.01.26"', 'version: "2026.06.01"'))
    with pytest.raises(DraftBlocked, match="newest pack is 2026.06.01"):
        approve_mod.approve(drafted, "Dr. Maya Chen", TODAY, cdcp_dir=cdcp)


def test_open_items_need_an_acknowledgement_which_is_logged(drafted: Path, cdcp: Path):
    meta = json.loads((drafted / "draft.json").read_text())
    (drafted / "draft.json").write_text(json.dumps({**meta, "needs_person": ["check the grid"]}))
    with pytest.raises(DraftBlocked, match="1 needs-a-person items are open"):
        approve_mod.approve(drafted, "Dr. Maya Chen", TODAY, cdcp_dir=cdcp)
    approve_mod.approve(drafted, 'Dr. "Maya" Chen', TODAY, cdcp_dir=cdcp, ack=True)
    assert "acknowledged 1 open items: check the grid" in (cdcp / "CHANGELOG.md").read_text()
    assert load_pack(cdcp / NEW / "pack.yaml").reviewed_by == 'Dr. "Maya" Chen'  # the name cannot break the YAML


def test_only_a_draft_under_drafts_is_approved(drafted: Path, cdcp: Path, tmp_path: Path):
    elsewhere = shutil.copytree(drafted, tmp_path / "elsewhere")
    with pytest.raises(DraftBlocked, match="drafts live under"):
        approve_mod.approve(elsewhere, "Dr. Maya Chen", TODAY, cdcp_dir=cdcp)
    assert elsewhere.exists()


# --- CLI -------------------------------------------------------------------------------------------


@pytest.fixture
def env(cdcp: Path, cases: Path, status: Path) -> cli.PackEnv:
    """`ophi pack ...` against the scratch pack and a fake web."""
    return cli.PackEnv(fetcher=fetcher(served(cdcp / BASE)), cdcp_dir=cdcp, cases_dir=cases, config=WATCH,
                       status=status, today=TODAY)


def test_cli_check_draft_approve(env: cli.PackEnv, cdcp: Path, status: Path, capsys):
    assert cli.main(["pack", "check"], env) == 0
    out = capsys.readouterr().out
    assert "0 changed, 0 shrank, 1 new documents, 0 unreachable" in out and "fact-sheet-guide-grids-april-2027" in out
    assert json.loads(status.read_text())["pending"] is True
    assert not (cdcp / "drafts").exists()  # check never drafts

    assert cli.main(["pack", "draft"], env) == 0
    assert "2 changes" in capsys.readouterr().out
    draft_dir = cdcp / "drafts" / TODAY.isoformat()
    assert (draft_dir / "report.md").exists()

    with pytest.raises(SystemExit):
        cli.main(["pack", "approve", str(draft_dir)], env)  # no reviewer named
    assert cli.main(["pack", "approve", str(draft_dir), "--by", "Dr. Maya Chen"], env) == 0
    assert f"approved: {cdcp / NEW}" in capsys.readouterr().out
    assert json.loads(status.read_text())["pending"] is False


def test_cli_check_reads_a_hand_downloaded_source(env: cli.PackEnv, cdcp: Path, tmp_path: Path, capsys):
    grid_url = load_pack(cdcp / BASE / "pack.yaml").sources["grid"].url
    web = served(cdcp / BASE)
    grid = tmp_path / "grid.txt"
    grid.write_bytes(web.pop(grid_url))
    env.fetcher = fetcher(web)
    assert cli.main(["pack", "check"], env) == 0
    assert "1 unreachable" in capsys.readouterr().out
    assert cli.main(["pack", "check", "--file", f"grid={grid}"], env) == 0
    assert "0 unreachable" in capsys.readouterr().out


def test_the_gap_copy_gives_each_step_its_own_date(drafted: Path, cdcp: Path):
    approve_mod.approve(drafted, "Dr. Maya Chen", TODAY, cdcp_dir=cdcp)
    case = load_case(ROOT / "cases" / "adversarial" / "retired_lab_code.yaml")  # lab code 99333
    assert _lab_result(case, pack_in_force(ON, cdcp)).detail == \
        "99333 was replaced by 99113 on 2026-04-01, and 99113 by 99123 on 2027-04-01"


def test_approve_leaves_no_half_built_pack(drafted: Path, cdcp: Path):
    approve_mod.approve(drafted, "Dr. Maya Chen", TODAY, cdcp_dir=cdcp)
    assert sorted(p.name for p in cdcp.iterdir() if p.is_dir()) == [BASE, NEW, "drafts"]
    assert list((cdcp / "drafts").iterdir()) == []


def test_an_edited_snapshot_blocks_approval(drafted: Path, cdcp: Path):
    snap = drafted / "sources" / "guide.txt"
    snap.write_text(snap.read_text() + "a line nobody reviewed\n")
    with pytest.raises(DraftBlocked, match="snapshots changed since drafting: guide"):
        approve_mod.approve(drafted, "Dr. Maya Chen", TODAY, cdcp_dir=cdcp)


def test_a_past_effective_date_blocks_and_today_needs_an_ack(drafted: Path, cdcp: Path):
    with pytest.raises(DraftBlocked, match="in the past"):
        approve_mod.approve(drafted, "Dr. Maya Chen", date(2027, 4, 2), cdcp_dir=cdcp, ack=True)
    with pytest.raises(DraftBlocked, match="is today"):
        approve_mod.approve(drafted, "Dr. Maya Chen", ON, cdcp_dir=cdcp)
    approve_mod.approve(drafted, "Dr. Maya Chen", ON, cdcp_dir=cdcp, ack=True)


def test_a_name_with_control_characters_is_refused(drafted: Path, cdcp: Path):
    with pytest.raises(ValueError, match="control characters"):
        approve_mod.approve(drafted, "Dr. Maya\nChen", TODAY, cdcp_dir=cdcp)


def test_cli_baseline_takes_a_hand_downloaded_source(env: cli.PackEnv, cdcp: Path, tmp_path: Path, capsys):
    grid_url = load_pack(cdcp / BASE / "pack.yaml").sources["grid"].url
    web = served(cdcp / BASE)
    grid = tmp_path / "grid.txt"
    grid.write_bytes(web.pop(grid_url))
    env.fetcher, env.config = fetcher(web), watch.Watch([PAGE], {"grid": "Sun Life grid"})
    assert cli.main(["pack", "baseline", "--force", "--file", f"grid={grid}"], env) == 0
    assert watch.read_lock(cdcp / BASE)["sources"]["grid"]["fetched_on"] == TODAY.isoformat()
