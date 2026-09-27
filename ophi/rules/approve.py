"""A named person turns a draft into a new pack version. Older packs are never touched: packets cite them by
version and content hash, and requests submitted under them must stay explainable."""

from __future__ import annotations

import json
import os
import re
import shutil
import unicodedata
from datetime import date
from pathlib import Path

from ophi.rules import watch
from ophi.rules.draft import (
    DRAFT_JSON,
    Change,
    DraftBlocked,
    date_problems,
    verify_quotes,
)
from ophi.rules.loader import CDCP_DIR, load_pack, pack_dir_for
from ophi.rules.schema import RulePack

_VERSION = re.compile(r"\d{4}\.\d{2}\.\d{2}")


def _added(pack: RulePack, parent: RulePack) -> list[Change]:
    """The retirements the draft adds over the pack it supersedes, as quoted changes."""
    before = {(r.code, r.replaced_by) for r in parent.schedule.retired_codes}
    return [Change(r.code, r.replaced_by, r.clause.source, r.clause.quote or "", r.effective_on)
            for r in pack.schedule.retired_codes if (r.code, r.replaced_by) not in before]


def validate(draft_dir: Path, today: date, cdcp_dir: Path = CDCP_DIR) -> tuple[RulePack, RulePack, list[Change], list[str]]:
    """Everything approval rests on, re-checked from the files as they are now (a person may have edited them).
    Returns the draft pack, its parent, the retirements it adds and the open needs-a-person items."""
    pack = load_pack(draft_dir / "pack.yaml")
    if not (_VERSION.fullmatch(pack.version) and pack.supersedes and _VERSION.fullmatch(pack.supersedes)):
        raise DraftBlocked(f"version and supersedes must look like 2026.09.26 (got {pack.version!r}, {pack.supersedes!r})")
    if (existing := pack_dir_for(pack.version, cdcp_dir)).exists():
        raise DraftBlocked(f"pack {pack.version} already exists at {existing}")
    newest = load_pack(watch.latest_pack_dir(cdcp_dir) / "pack.yaml")
    if pack.supersedes != newest.version:
        raise DraftBlocked(f"draft was made from {pack.supersedes} but the newest pack is {newest.version}; draft again")
    parent = load_pack(pack_dir_for(pack.supersedes, cdcp_dir) / "pack.yaml")
    if problems := date_problems(pack.effective_from, parent, today):
        raise DraftBlocked(problems[0])
    meta = draft_dir / DRAFT_JSON
    if not meta.exists():
        raise DraftBlocked(f"{draft_dir} has no {DRAFT_JSON}; it was not written by `ophi pack draft`")
    meta = json.loads(meta.read_text())
    snaps = watch.read_snapshots(draft_dir)
    drifted = sorted(k for k in {*snaps, *meta.get("snapshots", {})}
                     if meta.get("snapshots", {}).get(k) != (watch.fingerprint(snaps[k]) if k in snaps else None))
    if drifted:
        raise DraftBlocked(f"source snapshots changed since drafting: {', '.join(drifted)}; draft again")
    added = _added(pack, parent)
    # What a reviewer saw (draft.json, on /rules) must be what goes in force.
    if str(pack.effective_from) != meta.get("effective_from"):
        raise DraftBlocked(f"pack.yaml's effective_from {pack.effective_from} differs from the reviewed "
                           f"{meta.get('effective_from')}; draft again")
    shown = {(c.get("old"), c.get("new")) for c in meta.get("changes") or [] if isinstance(c, dict)}
    if {(c.old, c.new) for c in added} != shown:
        raise DraftBlocked("pack.yaml's code changes differ from the reviewed ones in draft.json; draft again")
    unknown = [c for c in added if c.source not in pack.sources]
    if unknown:
        raise DraftBlocked("retirement cites an unknown source: " + ", ".join(f"{c.old} ({c.source})" for c in unknown))
    verify_quotes(added, snaps)
    return pack, parent, added, meta.get("needs_person", [])


def approve(draft_dir: Path, by: str, today: date, cdcp_dir: Path = CDCP_DIR, ack: bool = False,
            status: Path | None = None) -> Path:
    """Re-validate the draft, write packs/cdcp/<version>/ recording who reviewed it and when, log it, and remove
    the draft. Open needs-a-person items block unless `ack`, which the changelog records. Returns the new pack dir."""
    by = by.strip()
    if not by:
        raise ValueError("approval needs the name of the person who reviewed the draft")
    if any(unicodedata.category(ch).startswith("C") for ch in by):
        raise ValueError("the reviewer's name has control characters")
    drafts = (cdcp_dir / "drafts").resolve()
    if drafts not in Path(draft_dir).resolve().parents:
        raise DraftBlocked(f"drafts live under {drafts}; {draft_dir} is not one")
    pack, parent, added, open_items = validate(draft_dir, today, cdcp_dir)
    if open_items and not ack:
        raise DraftBlocked(f"{len(open_items)} needs-a-person items are open (see report.md); resolve them in the "
                           "draft, or approve with --ack: " + " | ".join(open_items))
    if pack.effective_from == today and not ack:
        raise DraftBlocked(f"effective_from {today} is today: requests checked today would change; approve with --ack")
    target = pack_dir_for(pack.version, cdcp_dir)
    text = (draft_dir / "pack.yaml").read_text()
    m = re.search(r"^supersedes:.*\n", text, flags=re.M)
    text = text[:m.end()] + f"reviewed_by: {json.dumps(by)}\nreviewed_on: {today}\n" + text[m.end():]
    # Built beside the drafts, where the loader never looks, then moved into place in one step: a request never
    # sees half a pack.
    staging = drafts / f".approving-{pack.version}"
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir()
    try:
        (staging / "pack.yaml").write_text(text)
        shutil.copytree(draft_dir / "sources", staging / "sources")
        shutil.copy(draft_dir / watch.LOCK_NAME, staging / watch.LOCK_NAME)
        parent_map = pack_dir_for(parent.version, cdcp_dir) / "denial_map.yaml"
        if parent_map.exists():
            shutil.copy(parent_map, staging / "denial_map.yaml")
        load_pack(staging / "pack.yaml")
        os.rename(staging, target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    swaps = ", ".join(f"{c.old} -> {c.new}" for c in added) or "no code changes"
    acked = f"; acknowledged {len(open_items)} open items: " + " | ".join(open_items) if open_items else ""
    with (cdcp_dir / "CHANGELOG.md").open("a") as log:
        log.write(f"- {today}: {pack.version} (effective {pack.effective_from}, from {parent.version}) reviewed by "
                  f"{by}: {swaps}{acked}\n")
    shutil.rmtree(draft_dir)
    watch.mark_reviewed(status)
    return target
