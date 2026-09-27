"""Turn a source check into a draft rule pack a person can review.

Only code replacements are extracted, and only by pattern: "A, B -> C, D", "→", "replaced by/with", paired by
position. Anything else a changed source says is shown as a diff for a person to read. Nothing is guessed:
unequal code lists, conflicts with the pack, or a missing effective date become "needs a person" items, kept in
draft.json; approve refuses while any are open unless the reviewer acknowledges them.
"""

from __future__ import annotations

import difflib
import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from ophi.evals.run import assess_file, snapshot
from ophi.rules.loader import CDCP_DIR, load_pack, pack_dir_for
from ophi.rules.schema import RulePack
from ophi.rules.watch import (
    READ_STATES,
    CheckReport,
    Fetch,
    add_seen,
    fetch,
    fingerprint,
    read_lock,
    read_snapshots,
    read_source,
    write_baseline,
    write_json,
)

CASES_DIR = CDCP_DIR.parents[1] / "cases"
DRAFTS_DIR = CDCP_DIR / "drafts"

_CODE = re.compile(r"(?<!\d)\d{5}(?!\d)")
_ARROW = re.compile(r"->|→|=>|\breplaced (?:by|with)\b", re.I)
_RETIRED_WORDS = re.compile(r"\b(?:retired|deleted|discontinued|deactivated)\b", re.I)
_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
_DATE = re.compile(rf"\b(?:({_MONTHS})\s+(\d{{1,2}}),?\s+(\d{{4}})|(\d{{4}})-(\d{{2}})-(\d{{2}}))\b")
_EFFECTIVE_WORDS = re.compile(r"\b(?:effective|as of|starting)\b", re.I)
DATE_WINDOW = 4  # lines either side of a change where an "effective ..." date may be stated
DRAFT_JSON = "draft.json"


@dataclass
class Change:
    old: str
    new: str
    source: str
    quote: str
    effective_on: date | None


@dataclass
class DraftResult:
    changes: list[Change] = field(default_factory=list)  # applied to the draft
    out_of_scope: list[Change] = field(default_factory=list)
    already_in_pack: list[Change] = field(default_factory=list)
    needs_person: list[str] = field(default_factory=list)
    chains: list[str] = field(default_factory=list)  # older replacements that now resolve through a new one
    impact: list[str] = field(default_factory=list)
    cases: int = 0  # how many cases the impact check assessed
    dir: Path | None = None
    report_md: str = ""


class DraftBlocked(ValueError):
    """The draft cannot be trusted as written, e.g. a quote is not in its source."""


# --- extraction ------------------------------------------------------------------------------------


def _date_on(line: str) -> date | None:
    m = _DATE.search(line)
    if not m:
        return None
    try:
        if m.group(1):
            return date(int(m.group(3)), _MONTHS.split("|").index(m.group(1)) + 1, int(m.group(2)))
        return date(int(m.group(4)), int(m.group(5)), int(m.group(6)))
    except ValueError:  # "February 30": not a date, so no date
        return None


def effective_near(lines: list[str], i: int, allowed: set[int] | None = None) -> date | None:
    """The date on line i, else the closest date within the window on a line that calls it effective ("effective",
    "as of", "starting"). Only `allowed` lines count, so an unchanged neighbour never dates a new change."""
    if found := _date_on(lines[i]):
        return found
    for d in range(1, DATE_WINDOW + 1):
        for j in (i - d, i + d):
            if 0 <= j < len(lines) and (allowed is None or j in allowed) and _EFFECTIVE_WORDS.search(lines[j]):
                if found := _date_on(lines[j]):
                    return found
    return None


def extract(key: str, text: str, only_lines: set[int] | None = None) -> tuple[list[Change], list[str]]:
    """Code replacements stated in `text` (restricted to `only_lines` when given), and lines a person must read."""
    lines = text.splitlines()
    changes, unclear = [], []
    for i, line in enumerate(lines):
        if only_lines is not None and i not in only_lines:
            continue
        m = _ARROW.search(line)
        if not m:
            if _RETIRED_WORDS.search(line) and _CODE.search(line):
                unclear.append(f"{key}: codes retired without a stated replacement: \"{line}\"")
            continue
        old, new = _CODE.findall(line[:m.start()]), _CODE.findall(line[m.end():])
        if not old and not new:
            continue
        if not old or not new or len(old) != len(new) or len(_ARROW.findall(line)) > 1:
            unclear.append(f"{key}: replacement codes cannot be paired one to one: \"{line}\"")
            continue
        eff = effective_near(lines, i, only_lines)
        changes += [Change(o, n, key, line, eff) for o, n in zip(old, new)]
    return changes, unclear


def added_lines(old: str, new: str) -> set[int]:
    """Indices of lines in `new` that are not in `old`: only what a source newly says can be a new rule."""
    sm = difflib.SequenceMatcher(None, old.splitlines(), new.splitlines(), autojunk=False)
    return {j for tag, _, _, j1, j2 in sm.get_opcodes() if tag in ("insert", "replace") for j in range(j1, j2)}


# --- scope -----------------------------------------------------------------------------------------


def schedule_codes(pack: RulePack) -> set[str]:
    s = pack.schedule
    return set(s.preauth_always) | {r.code for r in s.retired_codes} | {r.replaced_by for r in s.retired_codes}


def in_scope(c: Change) -> bool:
    """The engine checks only lab fee codes against retirements, so only a 99xxx swap can be applied."""
    return c.old.startswith("99") and c.new.startswith("99")


def _triage(found: list[Change], pack: RulePack, r: DraftResult) -> None:
    retired = {x.code: x.replaced_by for x in pack.schedule.retired_codes}
    for c in found:
        if c.old.startswith("27") or (c.old in schedule_codes(pack) and not in_scope(c)):
            r.needs_person.append(f"{c.source}: crown code {c.old} is replaced by {c.new}; the pack's schedule and "
                                  f"frequency code lists need an engineer's edit.")
        elif c.old.startswith("99") and not in_scope(c):
            r.needs_person.append(f"{c.source}: lab code {c.old} is replaced by {c.new}, which is not a lab fee code.")
        elif not in_scope(c):
            r.out_of_scope.append(c)
        elif retired.get(c.old) == c.new:
            r.already_in_pack.append(c)
        elif c.old in retired:
            r.needs_person.append(f"{c.source}: says {c.old} is replaced by {c.new}; the pack says {retired[c.old]}.")
        elif c.new in retired:
            r.needs_person.append(f"{c.source}: says {c.old} is replaced by {c.new}, but the pack retires {c.new} "
                                  f"(replaced by {retired[c.new]}).")
        else:
            r.changes.append(c)
            r.chains += [f"{k} now resolves to {c.new} through {c.old}" for k, v in retired.items() if v == c.old]


# --- pack text edits (keeps the SME's comments) ----------------------------------------------------


def _set_line(text: str, key: str, value: str) -> str:
    new, n = re.subn(rf"^{key}:.*$", f"{key}: {value}", text, count=1, flags=re.M)
    if not n:
        raise DraftBlocked(f"pack.yaml has no top-level {key}")
    return new


def _without(text: str, key: str) -> str:
    return re.sub(rf"^{key}:.*\n", "", text, flags=re.M)


def _insert_after(text: str, pattern: str, block: str) -> str:
    m = re.search(pattern, text, flags=re.M)
    if not m:
        raise DraftBlocked(f"pack.yaml has no line matching {pattern!r}")
    end = text.index("\n", m.end()) + 1
    return text[:end] + block + text[end:]


def _retired_line(c: Change) -> str:
    ref = "Code replacements" + (f", effective {c.effective_on}" if c.effective_on else "")
    eff = f", effective_on: {c.effective_on}" if c.effective_on else ""
    return (f"    - {{ code: \"{c.old}\", replaced_by: \"{c.new}\"{eff}, clause: {{ source: {c.source}, "
            f"ref: {json.dumps(ref)}, quote: {json.dumps(c.quote, ensure_ascii=False)} }} }}\n")


def edit_pack(text: str, *, version: str, supersedes: str, effective: date, today: date,
              new_sources: dict[str, tuple[str, str]], changes: list[Change]) -> str:
    for k in ("supersedes", "reviewed_by", "reviewed_on"):
        text = _without(text, k)
    text = _set_line(text, "version", json.dumps(version))
    text = _insert_after(text, r"^version:", f"supersedes: {json.dumps(supersedes)}\n")
    text = _set_line(text, "effective_from", f"{effective}   # drafted {today} from a source check")
    text = _set_line(text, "verified_on", today.isoformat())
    block = "".join(f"  {k}:\n    title: {json.dumps(t, ensure_ascii=False)}\n    url: {json.dumps(u)}\n"
                    for k, (t, u) in new_sources.items())
    text = _insert_after(text, r"^sources:", block) if block else text
    lines = text.splitlines(keepends=True)
    at = next((i for i, x in enumerate(lines) if x.strip() == "retired_codes:"), None)
    if at is None:
        raise DraftBlocked("pack.yaml has no schedule.retired_codes")
    end = at + 1
    while end < len(lines) and lines[end].startswith("    "):
        end += 1
    text = "".join(lines[:end] + [_retired_line(c) for c in changes] + lines[end:])
    return _undated_copy(text) if changes else text


# The April 2026 pack's lab code copy names 2026 as the only retirement date; a pack adding later ones must not.
_DATED_COPY = {
    "label: Laboratory fee codes are valid for the 2026 date of service":
        "label: Laboratory fee codes are valid for the date of service",
    "why: Codes retired on 2026-04-01 are invalid for 2026 dates of service; a stale PMS fee table is a silent "
    "denial generator.":
        "why: A lab fee code is invalid for dates of service after its retirement; a stale PMS fee table is a "
        "silent denial generator.",
}


def _undated_copy(text: str) -> str:
    for old, new in _DATED_COPY.items():
        text = text.replace(old, new)
    return text


# --- impact ----------------------------------------------------------------------------------------


def case_files(cases_dir: Path = CASES_DIR) -> list[Path]:
    return sorted(p for p in cases_dir.rglob("*.yaml") if "lookback" not in p.parts)  # as the eval runner does


def impact(current: RulePack, proposed: RulePack, cases_dir: Path = CASES_DIR) -> list[str]:
    """Cases whose verdict or requirement results would differ under the proposed pack."""
    out = []
    for f in case_files(cases_dir):
        a, b = snapshot(assess_file(f, current)), snapshot(assess_file(f, proposed))
        diffs = [f"verdict {a['verdict']} -> {b['verdict']}"] if a["verdict"] != b["verdict"] else []
        diffs += [f"{rid} {a['requirements'].get(rid)} -> {b['requirements'].get(rid)}"
                  for rid in sorted(set(a["requirements"]) | set(b["requirements"]))
                  if a["requirements"].get(rid) != b["requirements"].get(rid)]
        if a["top_action"] != b["top_action"]:
            diffs.append(f"first action \"{a['top_action'] or 'none'}\" -> \"{b['top_action'] or 'none'}\"")
        if diffs:
            out.append(f"{f.relative_to(cases_dir)}: " + "; ".join(diffs))
    return out


# --- draft -----------------------------------------------------------------------------------------


def _new_key(url: str, title: str, today: date, taken: set[str]) -> str:
    s = (url + " " + title).lower()
    kind = next((k for k, words in (("factsheet", ("fact-sheet", "factsheet", "fact sheet")), ("grid", ("grid",)),
                                    ("guide", ("guide",)), ("matrix", ("supporting-documentation", "supporting documentation")))
                 if any(w in s for w in words)), "bulletin")
    key, n = f"{kind}_{today:%Y_%m_%d}", 2
    while key in taken:
        key, n = f"{kind}_{today:%Y_%m_%d}_{n}", n + 1
    return key


def verify_quotes(changes: list[Change], texts: dict[str, str]) -> None:
    """Every change cites a non-empty quote that is in its source's text and that itself states the change."""
    bad = [c for c in changes if not c.quote or c.quote not in texts.get(c.source, "")]
    if bad:
        raise DraftBlocked("quote not found in its source: " + "; ".join(f"{c.source}: {c.quote!r}" for c in bad))
    unstated = [c for c in changes if (c.old, c.new) not in {(x.old, x.new) for x in extract(c.source, c.quote)[0]}]
    if unstated:
        raise DraftBlocked("quote does not state the change: " + "; ".join(f"{c.old} -> {c.new}: {c.quote!r}" for c in unstated))


def date_problems(effective: date, parent: RulePack, today: date) -> list[str]:
    """Dates approval can never accept: on or before the pack it supersedes (pack_in_force goes by date, so it
    would never be in force), or already past (requests checked since would change without notice)."""
    out = []
    if effective <= parent.effective_from:
        out.append(f"effective_from {effective} is not after {parent.version}'s {parent.effective_from}; the new pack "
                   "would never be in force.")
    if effective < today:
        out.append(f"effective_from {effective} is in the past; set a date from today on.")
    return out


def _read_changed(report: CheckReport, texts: dict[str, str], r: DraftResult) -> list[Change]:
    """Replacements a changed source newly states; `texts` takes the new text."""
    found = []
    for s in report.shrank:
        r.needs_person.append(f"{s.key} shrank ({s.error}); read the diff: a holding page or a rewrite.")
        texts[s.key] = s.text
    for s in report.changed:
        got, unclear = extract(s.key, s.text, added_lines(texts.get(s.key, ""), s.text))
        found += got
        r.needs_person += unclear
        if not got and not unclear:
            r.needs_person.append(f"{s.key} changed but states no code replacement; read the diff for rule changes.")
        texts[s.key] = s.text
    return found


def _read_new(report: CheckReport, today: date, fetcher: Fetch, texts: dict[str, str], urls: dict[str, str],
              r: DraftResult) -> tuple[list[Change], dict[str, tuple[str, str]], list[str]]:
    """Replacements stated by newly found documents, the documents to add as sources, and the ones with nothing
    for this pack (safe to mark seen)."""
    found, new_sources, nothing = [], {}, []
    for link in report.new_links:
        try:
            text = read_source(link.url, fetcher)
        except Exception as e:  # noqa: BLE001
            r.needs_person.append(f"New document could not be fetched: {link.url} ({e}).")
            continue
        key = _new_key(link.url, link.title, today, set(urls))
        got, unclear = extract(key, text)
        if not got and not unclear:
            r.needs_person.append(f"New document states no code replacement; read it: {link.title or link.url} ({link.url}).")
            continue
        found += got
        r.needs_person += unclear
        if not unclear and not any(in_scope(c) or c.old.startswith("27") for c in got):
            nothing.append(link.url)  # listed as out of scope, not cited by the pack
            continue
        new_sources[key], urls[key], texts[key] = (link.title or link.url, link.url), link.url, text
    return found, new_sources, nothing


def _effective(r: DraftResult, today: date, parent: RulePack) -> date:
    dates = sorted({c.effective_on for c in r.changes if c.effective_on})
    if not dates:
        r.needs_person.append(f"No effective date is stated with the changes; the draft uses {today}. Set effective_from.")
    elif len(dates) > 1:
        r.needs_person.append(f"Changes take effect on different dates ({', '.join(map(str, dates))}); the draft uses the latest.")
    effective = dates[-1] if dates else today
    r.needs_person += date_problems(effective, parent, today)
    if effective == today:
        r.needs_person.append(f"effective_from {effective} is today: once approved, requests already checked today "
                              "change without notice. Approve with --ack if that is right.")
    return effective


def draft(report: CheckReport, today: date, fetcher: Fetch = fetch, cases_dir: Path = CASES_DIR,
          drafts_dir: Path = DRAFTS_DIR) -> DraftResult:
    """Write drafts/<today>/ with the proposed pack, source snapshots, draft.json and report.md, or nothing if
    nothing relevant changed."""
    pack_dir = Path(report.pack_dir)
    pack = load_pack(pack_dir / "pack.yaml")
    lock, texts = read_lock(pack_dir), read_snapshots(pack_dir)
    urls = {k: s.url for k, s in pack.sources.items()}
    r = DraftResult()
    found = _read_changed(report, texts, r)
    got, new_sources, nothing = _read_new(report, today, fetcher, texts, urls, r)
    _triage(found + got, pack, r)
    if not r.changes and not r.needs_person:
        add_seen(pack_dir, nothing)  # nothing for this pack in them: stop reporting them as new
        r.report_md = "Nothing relevant to this crowns pack changed; no draft written.\n"
        return r
    verify_quotes(r.changes, texts)
    effective = _effective(r, today, pack)
    version = today.strftime("%Y.%m.%d")
    if pack_dir_for(version, pack_dir.parent).exists():
        raise DraftBlocked(f"a pack version {version} already exists")

    out = drafts_dir / today.isoformat()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "pack.yaml").write_text(edit_pack((pack_dir / "pack.yaml").read_text(), version=version, supersedes=pack.version,
                                             effective=effective, today=today, new_sources=new_sources, changes=r.changes))
    # a source that could not be read today keeps the day it was last read
    fetched = {k: v.get("fetched_on") for k, v in lock["sources"].items()}
    fetched |= {s.key: today.isoformat() for s in report.sources if s.state in READ_STATES}
    fetched |= dict.fromkeys(new_sources, today.isoformat())
    write_baseline(out, texts, urls, fetched, [*lock.get("seen_links", []), *report.links])
    proposed = load_pack(out / "pack.yaml")
    r.impact = impact(pack, proposed, cases_dir)
    r.cases = len(case_files(cases_dir))
    # everything the review page shows, plus what approve re-checks (needs_person, snapshots)
    write_json(out / DRAFT_JSON, {
        "version": version, "supersedes": pack.version, "drafted_on": today.isoformat(),
        "effective_from": effective.isoformat(), "needs_person": r.needs_person,
        "snapshots": {k: fingerprint(t) for k, t in read_snapshots(out).items()},
        "changes": [_change_json(c) for c in r.changes], "chains": r.chains,
        "out_of_scope": [_change_json(c) for c in r.out_of_scope], "impact": r.impact, "cases": r.cases,
        "sources_changed": [x.key for x in report.changed + report.shrank],
        "new_documents": [{"title": n.title, "url": n.url} for n in report.new_links]})
    r.dir = out
    r.report_md = render_report(report, r, pack, proposed)
    (out / "report.md").write_text(r.report_md)
    return r


def _change_json(c: Change) -> dict:
    return asdict(c) | {"effective_on": str(c.effective_on or "")}


def render_report(report: CheckReport, r: DraftResult, current: RulePack, proposed: RulePack) -> str:
    def change(c: Change) -> str:
        eff = f"effective {c.effective_on}" if c.effective_on else "no effective date stated"
        return f"- {c.old} -> {c.new} ({eff})\n  - {c.source}: \"{c.quote}\""

    out = [f"# Draft rule pack {proposed.version}",
           "",
           f"Drafted {proposed.verified_on} from a source check of pack {current.version}. Effective from "
           f"{proposed.effective_from}. Nothing applies until a person approves it with "
           f"`ophi pack approve <this dir> --by \"Name\"` (add `--ack` to approve with needs-a-person items open).",
           "", "## Sources that changed", ""]
    out += [f"### {s.key}{' (shrank: needs a person)' if s.state == 'shrank' else ''}\n\n{s.url}\n\n```diff\n{s.diff}\n```\n"
            for s in report.changed + report.shrank] or ["None.", ""]
    if report.new_links:
        out += ["## New documents", ""] + [f"- {n.title or '(untitled)'}: {n.url} (found on {n.found_on})"
                                          for n in report.new_links] + [""]
    if report.unreachable or report.unreachable_pages:
        out += ["## Could not be checked", ""] + [f"- {s.key}: {s.url} ({s.error})" for s in report.unreachable]
        out += [f"- watch page {p}" for p in report.unreachable_pages] + [""]
    hand = [x for x in report.sources if x.state == "manual"]
    if hand:
        out += ["## Checked by hand, not read this time", ""]
        out += [f"- {x.manual_label or x.key}: last read {x.last_read or 'never'}" for x in hand] + [""]
    out += ["## Changes in this draft", ""] + ([change(c) for c in r.changes] or ["None."]) + [""]
    if r.chains:
        out += ["Older replacements follow the new code (the engine and Ophi's lab code fix follow the chain):", ""]
        out += [f"- {x}" for x in r.chains] + [""]
    out += ["## Needs a person", ""] + ([f"- {x}" for x in r.needs_person] or ["None."]) + [""]
    out += ["## Out of scope for the crowns pack (not applied)", ""] + ([change(c) for c in r.out_of_scope] or ["None."])
    if r.already_in_pack:
        out += ["", "## Already in the pack", ""] + [change(c) for c in r.already_in_pack]
    out += ["", "## Impact", "",
            "Every case under cases/ assessed with the current pack and with this draft, as if the draft applied to "
            "it. Once approved, each request is checked under the pack in force on its own date, so only requests "
            "dated on or after the effective date change.",
            "", f"{len(r.impact)} of {r.cases} cases change.", ""] + [f"- {x}" for x in r.impact]
    return "\n".join(out) + "\n"
