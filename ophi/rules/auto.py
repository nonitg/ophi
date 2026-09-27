"""Keep the source check current without anyone running a command.

A page visit starts a check when the last one is a week old (a day, after a failed attempt), in a background
thread, so the page is never held up. The job checks and, when something relevant is pending and no draft is
waiting for it, drafts. It never puts a draft in force: a person does that on the review page (/rules).
"""

from __future__ import annotations

import fcntl
import json
import logging
import threading
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from ophi.rules import watch
from ophi.rules.loader import CDCP_DIR, load_pack

log = logging.getLogger(__name__)

CHECK_EVERY = timedelta(days=7)
RETRY_AFTER = timedelta(days=1)  # after a failed attempt, e.g. the network was down
STALE_RUN = timedelta(minutes=30)  # a check marked running for longer than this died with its process

_running = threading.Lock()  # one check per process; the status file's marker covers other processes


@dataclass
class PackEnv:
    """Where the source check reads and writes, and how it fetches; unset fields take the real ones. Tests point
    it at scratch dirs and a fake web."""
    fetcher: Callable[[str], bytes] | None = None
    cdcp_dir: Path | None = None
    cases_dir: Path | None = None
    config: watch.Watch | None = None  # None: packs/cdcp/watch.yaml
    status: Path | None = None
    today: date | None = None

    def resolved(self) -> PackEnv:
        from ophi.rules.draft import CASES_DIR

        return replace(self, fetcher=self.fetcher or watch.fetch, cdcp_dir=self.cdcp_dir or CDCP_DIR,
                       cases_dir=self.cases_dir or CASES_DIR, status=self.status or watch.status_path(),
                       today=self.today or date.today())


def _when(stamp: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(stamp) if stamp else None
    except (TypeError, ValueError):
        return None


def checking(status: dict | None, now: datetime) -> bool:
    """A check is running (its marker is set and not left behind by a dead process)."""
    started = _when((status or {}).get("checking_since"))
    return bool(started and now - started < STALE_RUN)


def due(status: dict | None, now: datetime) -> bool:
    """Whether a visit at `now` should start a check."""
    if not status:
        return True
    if checking(status, now):
        return False
    last = _when(status.get("attempted_at"))
    if last is None:
        return True
    return now - last >= (RETRY_AFTER if status.get("last_error") else CHECK_EVERY)


@contextmanager
def _status_lock(status: Path):
    """Serialize read-then-write of the status file across processes (several workers, a CLI run)."""
    status.parent.mkdir(parents=True, exist_ok=True)
    with open(status.with_name(status.name + ".lock"), "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _claim(status: Path, now: datetime, force: bool) -> bool:
    """Mark a check as running unless one already is (or, without `force`, none is due)."""
    with _status_lock(status):
        current = watch.load_status(status)
        if checking(current, now) or (not force and not due(current, now)):
            return False
        watch.write_json(status, {**(current or {}), "checking_since": now.isoformat()})
        return True


def _record_failure(status: Path, now: datetime, error: str) -> None:
    with _status_lock(status):
        current = watch.load_status(status) or {}
        watch.write_json(status, {**current, "attempted_at": now.isoformat(), "last_error": error, "checking_since": None})


def current_draft(cdcp_dir: Path = CDCP_DIR) -> Path | None:
    """The draft waiting for review of the newest pack, if any (a draft of an older pack can no longer be used)."""
    newest = load_pack(watch.latest_pack_dir(cdcp_dir) / "pack.yaml").version
    from ophi.rules.draft import DRAFT_JSON

    for meta in sorted((cdcp_dir / "drafts").glob(f"*/{DRAFT_JSON}"), reverse=True):
        try:
            if json.loads(meta.read_text()).get("supersedes") == newest:
                return meta.parent
        except (OSError, ValueError, AttributeError):
            continue
    return None


def _network_down(r: watch.CheckReport) -> bool:
    """Nothing fetched could be read: the check learned nothing, so it is retried sooner."""
    fetched = [s for s in r.sources if s.state != "manual"]
    return bool(fetched) and all(s.state == "unreachable" for s in fetched) and not r.links


def run(env: PackEnv, now: datetime | None = None, force: bool = False) -> str:
    """Check the sources and draft if something relevant is pending and no draft is waiting. Never approves.
    Returns what happened: "busy", "not due", "failed", "checked", "drafted" or "nothing relevant"."""
    e, now = env.resolved(), now or datetime.now(UTC)
    if not _running.acquire(blocking=False):
        return "busy"
    try:
        if not _claim(e.status, now, force):
            return "busy" if force else "not due"
        try:
            r = watch.check(watch.latest_pack_dir(e.cdcp_dir), e.today, e.fetcher, e.config)
        except Exception as err:  # noqa: BLE001 — recorded, retried after RETRY_AFTER
            log.exception("rules check failed")
            _record_failure(e.status, now, str(err) or type(err).__name__)
            return "failed"
        if _network_down(r):
            _record_failure(e.status, now, "no source or watch page could be reached")
            return "failed"
        with _status_lock(e.status):
            watch.save_status(r, e.status, attempted_at=now)
        return _draft_if_needed(r, e)
    finally:
        _running.release()


def _draft_if_needed(r: watch.CheckReport, e: PackEnv) -> str:
    if not r.pending:
        return "checked"
    if current_draft(e.cdcp_dir):
        return "checked"  # a person has one to review already
    from ophi.rules.draft import DraftBlocked, draft

    try:
        d = draft(r, e.today, e.fetcher, cases_dir=e.cases_dir, drafts_dir=e.cdcp_dir / "drafts")
    except DraftBlocked as err:
        log.warning("rules draft blocked: %s", err)
        return "checked"
    if d.dir is None:
        watch.mark_reviewed(e.status)  # the new documents had nothing for this pack and are now recorded as seen
        return "nothing relevant"
    return "drafted"


def maybe_start(env: PackEnv, now: datetime | None = None, force: bool = False) -> threading.Thread | None:
    """On a page visit: start a background check if one is due (or, with `force`, "Check now": unless one is
    running). Returns the thread, or None."""
    e, now = env.resolved(), now or datetime.now(UTC)
    status = watch.load_status(e.status)
    wanted = not checking(status, now) if force else due(status, now)
    if _running.locked() or not wanted:
        return None
    t = threading.Thread(target=_safe_run, args=(env, now, force), name="rules-check", daemon=True)
    t.start()
    return t


def _safe_run(env: PackEnv, now: datetime, force: bool = False) -> None:
    try:
        run(env, now, force)
    except Exception:  # noqa: BLE001 — a background job must never take the server down
        log.exception("background rules check crashed")


def review_status(env: PackEnv) -> dict | None:
    """The status for the board, plus whether a draft is waiting for review."""
    e = env.resolved()
    status = watch.load_status(e.status)
    try:
        waiting = current_draft(e.cdcp_dir) is not None
    except Exception:  # noqa: BLE001 — the board must render even if the packs are unreadable
        waiting = False
    return {**(status or {}), "draft_waiting": waiting} if status or waiting else None
