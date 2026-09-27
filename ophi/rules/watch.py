"""Watch the documents a rule pack cites, and the CDCP pages where new ones are published.

A pack is only as current as its sources. Each pack version keeps a baseline (`sources.lock.json` plus a
normalized text snapshot per source); a check re-fetches and compares text, not bytes, so page chrome
churn never raises an alert. Nothing here changes a rule: a found change becomes a draft a person reviews.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import subprocess
import tempfile
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urljoin

import yaml

from ophi.rules.loader import CDCP_DIR, load_pack
from ophi.rules.schema import RulePack

WATCH_FILE = CDCP_DIR / "watch.yaml"
LOCK_NAME = "sources.lock.json"
STATUS_NAME = "rules-watch.json"
DIFF_LINES = 40
MAX_BYTES = 20 * 1024 * 1024
PDFTOTEXT_SECONDS = 120
# A fetch whose text is under this share of the baseline is an error or holding page, not a rewrite.
MIN_TEXT_SHARE = 0.5

Fetch = Callable[[str], bytes]

# One honest client name with a contact; Ophi never poses as a browser. A source behind a bot wall (the Sun Life
# grid) is marked `manual` in watch.yaml and checked from a hand-downloaded copy (`--file grid=<path>`).
USER_AGENT = "ophi-rules-watch/1 (+https://cortico.health)"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*", "Accept-Language": "en-CA,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError(f"larger than {MAX_BYTES // (1024 * 1024)} MB")
    return raw


def local_files(fetcher: Fetch, pack: RulePack, files: dict[str, Path]) -> Fetch:
    """Serve the named sources from local copies (e.g. a grid downloaded by hand) and the rest from `fetcher`."""
    unknown = set(files) - set(pack.sources)
    if unknown:
        raise KeyError(f"not a source of pack {pack.version}: {', '.join(sorted(unknown))}")
    local = {pack.sources[k].url: Path(p) for k, p in files.items()}
    return lambda url: local[url].read_bytes() if url in local else fetcher(url)


# --- text ------------------------------------------------------------------------------------------

_SKIP_TAGS = {"script", "style", "noscript", "template", "title", "nav", "footer", "svg", "gcds-date-modified"}
_SKIP_IDS = {"wb-dtmd"}  # canada.ca (WET) "Date modified" footer
_CONTENT_TAGS = {"main", "article"}  # a <header> inside these is content, not page chrome
_BLOCK_TAGS = {"p", "div", "br", "li", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article",
               "dt", "dd", "dl", "table", "ul", "ol", "caption", "figcaption", "blockquote", "pre", "main", "aside",
               "details", "summary", "header"}
# canada.ca stamps every page; a republish that only moves this date is not a change.
_DATE_MODIFIED = re.compile(r"^date modified:?\s*\d{4}-\d{2}-\d{2}$", re.I)


class _Visible(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._skip: list[str] = []  # open skipped elements, innermost last
        self._content = 0
        self._href: str | None = None
        self._anchor: list[str] = []

    def _starts_skip(self, tag: str, attrs: dict) -> bool:
        return tag in _SKIP_TAGS or attrs.get("id") in _SKIP_IDS or (tag == "header" and not self._content)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self._starts_skip(tag, a) or (self._skip and tag == self._skip[-1]):
            self._skip.append(tag)
        elif not self._skip and tag in _BLOCK_TAGS:
            self.parts.append("\n")
        if tag in _CONTENT_TAGS:
            self._content += 1
        if tag == "a":
            self._href, self._anchor = a.get("href"), []

    def handle_endtag(self, tag):
        if self._skip:
            if tag == self._skip[-1]:
                self._skip.pop()
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")
        if tag in _CONTENT_TAGS:
            self._content = max(0, self._content - 1)
        if tag == "a" and self._href:
            self.links.append((self._href, " ".join("".join(self._anchor).split())))
            self._href = None

    def handle_data(self, data):
        self._anchor.append(data)
        if not self._skip:
            self.parts.append(data)


def is_pdf(raw: bytes) -> bool:
    return raw.lstrip()[:5] == b"%PDF-"


def is_html(raw: bytes) -> bool:
    head = raw.lstrip()[:512].lower()
    return head.startswith(b"<!doctype html") or b"<html" in head


def normalize(text: str) -> str:
    lines = (" ".join(line.split()) for line in text.splitlines())
    return "\n".join(line for line in lines if line and not _DATE_MODIFIED.match(line)) + "\n"


def pdf_text(raw: bytes) -> str:
    try:
        out = subprocess.run(["pdftotext", "-layout", "-", "-"], input=raw, capture_output=True, check=True,
                             timeout=PDFTOTEXT_SECONDS)
    except FileNotFoundError:
        raise RuntimeError("pdftotext is not installed (poppler-utils); it is needed to read PDF sources") from None
    return out.stdout.decode("utf-8", "replace")


def to_text(raw: bytes) -> str:
    if is_pdf(raw):
        return normalize(pdf_text(raw))
    if is_html(raw):
        p = _Visible()
        p.feed(raw.decode("utf-8", "replace"))
        return normalize("".join(p.parts))
    return normalize(raw.decode("utf-8", "replace"))


def fingerprint(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


# --- discovery -------------------------------------------------------------------------------------

_DOC_WORDS = ("guide", "grid", "fact-sheet", "factsheet", "fact sheet", "bulletin", "update", "supporting-documentation",
              "supporting documentation", "preauthori", "claims-processing", "payment terms")


def _plausible(url: str, anchor: str) -> bool:
    """A CDCP guide, grid, factsheet or bulletin in English, as opposed to navigation and promotion."""
    u = url.lower()
    if not u.startswith("http") or "/fr/" in u or u.endswith("-fr.pdf") or "toolkit" in u:
        return False
    if not (u.endswith((".pdf", ".html", "/")) and ("dental" in u or "cdcp" in u)):
        return False
    return any(w in u or w in anchor.lower() for w in _DOC_WORDS)


def page_links(raw: bytes, base: str) -> dict[str, str]:
    """Plausible document links on a watch page: absolute url -> anchor text."""
    p = _Visible()
    p.feed(raw.decode("utf-8", "replace"))
    out: dict[str, str] = {}
    for href, anchor in p.links:
        url = urldefrag(urljoin(base, href)).url
        if url != base and _plausible(url, anchor):
            out.setdefault(url, anchor)
    return out


@dataclass
class Watch:
    """What watch.yaml says: the pages to scan for new documents, and the sources checked by hand (key -> label)."""
    pages: list[str]
    manual: dict[str, str] = field(default_factory=dict)


def load_watch(path: Path = WATCH_FILE) -> Watch:
    d = yaml.safe_load(path.read_text())
    manual = {k: v.get("label", k) for k, v in (d.get("sources") or {}).items() if v.get("manual")}
    return Watch(d["pages"], manual)


# --- baseline files --------------------------------------------------------------------------------


def latest_pack_dir(cdcp_dir: Path = CDCP_DIR) -> Path:
    """The newest reviewed pack, in force or not: new publications are compared against what a person last saw."""
    return sorted(cdcp_dir.glob("*/pack.yaml"))[-1].parent


def read_lock(pack_dir: Path) -> dict:
    path = pack_dir / LOCK_NAME
    return json.loads(path.read_text()) if path.exists() else {"sources": {}, "seen_links": []}


def read_snapshots(pack_dir: Path) -> dict[str, str]:
    """Source key -> the normalized text a pack (or draft) was checked against."""
    return {p.stem: p.read_text() for p in (pack_dir / "sources").glob("*.txt")}


def write_json(path: Path, data: dict) -> None:
    """Replace `path` whole, so a reader never sees half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(fd, "w") as f:
        f.write(json.dumps(data, indent=2) + "\n")
    os.replace(tmp, path)


def write_baseline(pack_dir: Path, texts: dict[str, str], urls: dict[str, str], fetched_on: dict[str, str | None],
                   seen: list[str], note: str | None = None) -> None:
    """Lock and snapshots for `pack_dir`. `fetched_on` is the day each text was actually read."""
    (pack_dir / "sources").mkdir(exist_ok=True)
    lock: dict = {"note": note} if note else {}
    lock["sources"] = {}
    for key, url in urls.items():
        if key in texts:
            (pack_dir / "sources" / f"{key}.txt").write_text(texts[key])
        lock["sources"][key] = {"url": url, "sha256": fingerprint(texts[key]) if key in texts else None,
                                "fetched_on": fetched_on.get(key)}
    lock["seen_links"] = sorted(set(seen))
    write_json(pack_dir / LOCK_NAME, lock)


def add_seen(pack_dir: Path, urls: list[str]) -> None:
    """Record links nobody needs to look at again (e.g. a new document with nothing for this pack)."""
    lock = read_lock(pack_dir)
    lock["seen_links"] = sorted(set(lock.get("seen_links", [])) | set(urls))
    write_json(pack_dir / LOCK_NAME, lock)


# --- check -----------------------------------------------------------------------------------------


READ_STATES = ("unchanged", "changed", "shrank")  # the text was read today


@dataclass
class SourceCheck:
    key: str
    url: str
    state: str  # unchanged | changed | shrank (far shorter: a person decides) | unreachable | manual (not fetched)
    diff: str = ""
    error: str = ""
    text: str = field(default="", repr=False)  # the text read today, for drafting
    manual_label: str = ""  # set for a source checked by hand, e.g. "Sun Life grid"
    by_hand: bool = False  # read today from a local copy
    last_read: str | None = None  # the lock's fetched_on, for a source not read today


@dataclass
class NewLink:
    url: str
    title: str
    found_on: str


@dataclass
class CheckReport:
    pack_dir: str
    pack_version: str
    checked_on: date
    sources: list[SourceCheck]
    new_links: list[NewLink]
    unreachable_pages: list[str]
    links: list[str] = field(default_factory=list)  # every document link on the watch pages, new or not

    @property
    def changed(self) -> list[SourceCheck]:
        return [s for s in self.sources if s.state == "changed"]

    @property
    def shrank(self) -> list[SourceCheck]:
        return [s for s in self.sources if s.state == "shrank"]

    @property
    def unreachable(self) -> list[SourceCheck]:
        return [s for s in self.sources if s.state == "unreachable"]

    @property
    def pending(self) -> bool:
        return bool(self.changed or self.shrank or self.new_links)


def text_diff(old: str, new: str, name: str) -> str:
    lines = list(difflib.unified_diff(old.splitlines(), new.splitlines(), f"{name} (baseline)", f"{name} (now)", n=1,
                                      lineterm=""))
    more = f"\n... {len(lines) - DIFF_LINES} more diff lines" if len(lines) > DIFF_LINES else ""
    return "\n".join(lines[:DIFF_LINES]) + more


def read_source(url: str, fetcher: Fetch) -> str:
    """The document's text now. An empty page is an error, never CDCP deleting the document."""
    text = to_text(fetcher(url))
    if not text.strip():
        raise ValueError("no text")
    return text


def _read_state(key: str, url: str, text: str, lock: dict, snaps: dict[str, str], **kw) -> SourceCheck:
    base = snaps.get(key, "")
    if lock["sources"].get(key, {}).get("sha256") == fingerprint(text):
        return SourceCheck(key, url, "unchanged", text=text, **kw)
    diff = text_diff(base, text, key)
    if base and len(text) < MIN_TEXT_SHARE * len(base):  # a holding page or a gutted rewrite: a person decides
        return SourceCheck(key, url, "shrank", diff=diff, text=text,
                           error=f"text is {100 * len(text) // len(base)}% of the baseline's length", **kw)
    return SourceCheck(key, url, "changed", diff=diff, text=text, **kw)


def check_sources(pack: RulePack, pack_dir: Path, fetcher: Fetch, manual: dict[str, str] | None = None,
                  files: dict[str, Path] | None = None) -> list[SourceCheck]:
    """Each source against the baseline. A `manual` source is read only from a local copy in `files`."""
    lock, snaps, manual, files = read_lock(pack_dir), read_snapshots(pack_dir), manual or {}, files or {}
    fetcher = local_files(fetcher, pack, files)
    out = []
    for key, src in pack.sources.items():
        kw = {"manual_label": manual.get(key, ""), "by_hand": key in files}
        if key in manual and key not in files:
            out.append(SourceCheck(key, src.url, "manual", last_read=lock["sources"].get(key, {}).get("fetched_on"), **kw))
            continue
        try:
            text = read_source(src.url, fetcher)
        except Exception as e:  # noqa: BLE001 — any fetch or parse failure means "not reachable today"
            out.append(SourceCheck(key, src.url, "unreachable", error=str(e) or type(e).__name__, **kw))
            continue
        out.append(_read_state(key, src.url, text, lock, snaps, **kw))
    return out


def scan_pages(pages: list[str], fetcher: Fetch) -> tuple[dict[str, tuple[str, str]], list[str]]:
    """Document links on the watch pages (url -> (title, page)), and the pages that could not be read."""
    found, dead = {}, []
    for page in pages:
        try:
            links = page_links(fetcher(page), page)
        except Exception:  # noqa: BLE001
            dead.append(page)
            continue
        for url, title in links.items():
            found.setdefault(url, (title, page))
    return found, dead


def check(pack_dir: Path | None = None, today: date | None = None, fetcher: Fetch = fetch,
          config: Watch | None = None, files: dict[str, Path] | None = None) -> CheckReport:
    """Compare every source of the newest pack with its baseline, and list new documents on the watch pages.
    `config` defaults to watch.yaml; `files` reads those sources from local copies."""
    pack_dir = pack_dir or latest_pack_dir()
    config = config or load_watch()
    pack = load_pack(pack_dir / "pack.yaml")
    seen = set(read_lock(pack_dir).get("seen_links", [])) | {s.url for s in pack.sources.values()}
    found, dead = scan_pages(config.pages, fetcher)
    new = [NewLink(url, title, page) for url, (title, page) in found.items() if url not in seen]
    return CheckReport(str(pack_dir), pack.version, today or date.today(),
                       check_sources(pack, pack_dir, fetcher, config.manual, files), new, dead, list(found))


class BaselineRefused(RuntimeError):
    """Re-baselining now would absorb a change nobody has reviewed."""


def baseline(pack_dir: Path, today: date, fetcher: Fetch = fetch, config: Watch | None = None,
             files: dict[str, Path] | None = None, note: str | None = None, force: bool = False) -> CheckReport:
    """Record the sources and watch-page links as they read now as what `pack_dir` was checked against.
    Refuses while the current baseline shows a pending change, unless `force`. A source not read today
    (unreachable, or manual without a local copy) keeps its previous snapshot and fetch date. Returns the check
    it was based on."""
    r = check(pack_dir, today, fetcher, config, files)
    if r.pending and not force and (pack_dir / LOCK_NAME).exists():
        what = [s.key for s in r.changed + r.shrank] + [n.url for n in r.new_links]
        raise BaselineRefused("pending changes would be absorbed without review: " + ", ".join(what))
    pack = load_pack(pack_dir / "pack.yaml")
    lock, texts = read_lock(pack_dir), read_snapshots(pack_dir)
    fetched = {k: v.get("fetched_on") for k, v in lock["sources"].items()}
    for s in r.sources:
        if s.state in READ_STATES:
            texts[s.key], fetched[s.key] = s.text, today.isoformat()
    write_baseline(pack_dir, texts, {k: s.url for k, s in pack.sources.items()}, fetched,
                   [*lock.get("seen_links", []), *r.links], note or lock.get("note"))
    return r


# --- status for the web app ------------------------------------------------------------------------


def status_path() -> Path:
    from ophi.service import VAR_DIR

    return VAR_DIR / STATUS_NAME


def save_status(report: CheckReport, path: Path | None = None, attempted_at: datetime | None = None) -> dict:
    """Record the latest check. `found_on` keeps the day changes were first seen until someone reviews them;
    `attempted_at` is when it ran, which paces the automatic check (ophi.rules.auto)."""
    path = path or status_path()
    prev = load_status(path) or {}
    found_on = (prev.get("found_on") if prev.get("pending") else None) or report.checked_on.isoformat()
    status = {
        "checked_on": report.checked_on.isoformat(),
        "pack_version": report.pack_version,
        "pending": report.pending,
        "found_on": found_on if report.pending else None,
        "changed": [s.key for s in report.changed + report.shrank],
        "new_links": [asdict(n) for n in report.new_links],
        "unreachable": [s.key for s in report.unreachable] + report.unreachable_pages,
        "manual": [{"key": s.key, "label": s.manual_label, "checked_on": _hand_checked(s, report.checked_on, prev)}
                   for s in report.sources if s.manual_label],
        "sources": {s.key: s.state for s in report.sources},
        "attempted_at": (attempted_at or datetime.now(UTC)).isoformat(),
        "last_error": None,
        "checking_since": None,
    }
    write_json(path, status)
    return status


def _hand_checked(s: SourceCheck, today: date, prev: dict) -> str | None:
    """The last day a person checked this source by hand: today if they just did, else the latest day on record."""
    if s.by_hand and s.state in READ_STATES:
        return today.isoformat()
    before = [m.get("checked_on") for m in prev.get("manual") or [] if isinstance(m, dict) and m.get("key") == s.key]
    return max((d for d in [*before, s.last_read] if d), default=None)


def load_status(path: Path | None = None) -> dict | None:
    try:
        status = json.loads((path or status_path()).read_text())
    except (OSError, ValueError):
        return None
    return status if isinstance(status, dict) else None


def mark_reviewed(path: Path | None = None) -> None:
    """A person reviewed the pending change (approved a draft or re-baselined); the board stops asking."""
    path = path or status_path()
    status = load_status(path)
    if status:
        write_json(path, {**status, "pending": False, "found_on": None})
