"""A fake CDCP web for trying the source watch offline: every pack source serves its baseline snapshot, and the
providers page lists a new April 2027 factsheet (fixtures/pack_watch/). Used by scripts/pack-watch-fixture.py
and the pack watch tests; never by the app."""

from __future__ import annotations

from pathlib import Path

from ophi.rules.loader import load_pack
from ophi.rules.watch import Fetch, Watch

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "pack_watch"
PAGE = "https://www.canada.ca/en/services/benefits/dental/dental-care-plan/providers.html"
NEW_DOC = "https://www.canada.ca/en/services/benefits/dental/dental-care-plan/providers/fact-sheet-guide-grids-april-2027.html"
WATCH = Watch([PAGE])  # one watch page, every source fetched (none marked manual)


def served(pack_dir: Path, page: bytes | None = None, **overrides: bytes) -> dict[str, bytes]:
    """The web as the baseline saw it: each source serves its snapshot; the watch page and new factsheet as given.
    `overrides` replaces a source's bytes by its key."""
    pack = load_pack(pack_dir / "pack.yaml")
    web = {s.url: overrides.get(k, (pack_dir / "sources" / f"{k}.txt").read_bytes()) for k, s in pack.sources.items()}
    web[PAGE] = page if page is not None else (FIX / "providers-page.html").read_bytes()
    web[NEW_DOC] = (FIX / "new-factsheet.html").read_bytes()
    return web


def fetcher(web: dict[str, bytes]) -> Fetch:
    def get(url: str) -> bytes:
        if url not in web:
            raise OSError(f"unreachable: {url}")
        return web[url]
    return get
