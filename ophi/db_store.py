"""The app's patients and workflow state in Supabase (schema `app`), in place of cases/demo/*.yaml and var/*.json.

Same interfaces as the file-backed service.Store and FileSystemPmsRepository, so CaseService is unchanged.
Packets stay on local disk: they are generated files, rebuilt from state.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
import os
import shutil
from pathlib import Path

import psycopg
import yaml
from psycopg.types.json import Jsonb

from ophi.casegen.dsl import build_case
from ophi.cdm.models import Case
from ophi.outcomes import store as db
from ophi.service import VAR_DIR, AuditEvent, CaseService, CaseState, FollowUp, Store
from ophi.sources.pms_repository import should_use_mocks


class SupabaseStore(Store):
    def __init__(self, connect: Callable[[], psycopg.Connection] = db.connect, root: Path = VAR_DIR) -> None:
        super().__init__(root)  # root holds packets only
        self._connect, self._conn = connect, None

    @contextmanager
    def _db(self) -> Iterator[psycopg.Connection]:
        """One autocommit connection per process, reopened if dropped: a pooler round trip per page, not a handshake."""
        with self._lock:
            if self._conn is None or self._conn.closed:
                self._conn = self._connect()
                self._conn.autocommit = True
            yield self._conn

    def _one(self, sql: str, args: tuple = ()):
        with self._db() as conn:
            return conn.execute(sql, args).fetchone()

    def _write(self, sql: str, args: tuple = ()) -> None:
        with self._db() as conn:
            conn.execute(sql, args)

    def load(self, case_id: str) -> CaseState:
        row = self._one("select state from app.case_state where case_id = %s", (case_id,))
        return CaseState.model_validate(row[0]) if row else CaseState()

    def save(self, case_id: str, st: CaseState) -> None:
        self._write("insert into app.case_state (case_id, state) values (%s, %s) on conflict (case_id) "
                    "do update set state = excluded.state, updated_at = now()", (case_id, Jsonb(st.model_dump(mode="json"))))

    def record_first_check(self, case_id: str, fc) -> None:
        """Set the first check only if no one has yet, in one statement, so a concurrent write survives."""
        with self._db() as conn:
            conn.execute("insert into app.case_state (case_id, state) values (%s, %s) on conflict do nothing",
                         (case_id, Jsonb(CaseState().model_dump(mode="json"))))
            conn.execute("update app.case_state set state = jsonb_set(state, '{first_check}', %s), updated_at = now() "
                         "where case_id = %s and coalesce(state->'first_check', 'null') = 'null'",
                         (Jsonb(fc.model_dump(mode="json")), case_id))

    def load_followups(self) -> dict[str, FollowUp]:
        with self._db() as conn:
            return {r: FollowUp.model_validate(f) for r, f in conn.execute("select row_id, followup from app.followup").fetchall()}

    def set_followup(self, row_id: str, followup: FollowUp) -> None:
        self._write("insert into app.followup (row_id, followup) values (%s, %s) on conflict (row_id) "
                    "do update set followup = excluded.followup, updated_at = now()", (row_id, Jsonb(followup.model_dump(mode="json"))))

    def audit(self, case_id: str, actor: str, event: str, detail: str, at: datetime | None = None) -> None:
        self._write("insert into app.audit_event (at, case_id, actor, event, detail) values (%s, %s, %s, %s, %s)",
                    (at or datetime.now(UTC), case_id, actor, event, detail))

    def audit_log(self, case_id: str | None = None) -> list[AuditEvent]:
        with self._db() as conn:
            rows = conn.execute("select at, case_id, actor, event, detail from app.audit_event "
                                "where %s::text is null or case_id = %s order by id", (case_id, case_id)).fetchall()
        return [AuditEvent(at=a, case_id=c, actor=ac, event=e, detail=d) for a, c, ac, e, d in rows]

    def reset(self) -> None:
        """Start the demo over: clear workflow state; the patients' charts stay."""
        with self._db() as conn:
            for t in ("case_state", "followup", "audit_event"):  # delete, not truncate: the app role is granted DML only
                conn.execute(f"delete from app.{t}")
        shutil.rmtree(self.root / "packets", ignore_errors=True)


class SupabaseCaseRepository:
    """Patient charts from app.patient_case, cached per process: charts change only when re-seeded."""

    def __init__(self, connect: Callable[[], psycopg.Connection] = db.connect) -> None:
        self._connect, self._raw = connect, None

    def _charts(self) -> dict[str, str]:
        if self._raw is None:
            with self._connect() as conn:
                self._raw = dict(conn.execute("select case_id, chart_yaml from app.patient_case order by case_id").fetchall())
        return self._raw

    def list_case_ids(self) -> list[str]:
        return list(self._charts())

    def get_case(self, case_id: str) -> Case:
        if case_id not in self._charts():
            raise FileNotFoundError(f"No case '{case_id}' in Supabase app.patient_case")
        return build_case(yaml.safe_load(self._charts()[case_id]), case_id)

    def get_cases(self, case_ids: list[str] | None = None) -> list[Case]:
        return [self.get_case(c) for c in (case_ids if case_ids is not None else self.list_case_ids())]


def service_from_env(**kwargs) -> CaseService | None:
    """The demo's service on Supabase when SUPABASE_DB_URL is set. A live ABELDent or mock PMS still supplies
    the charts when switched on; Supabase then holds only the workflow state."""
    if not os.environ.get("SUPABASE_DB_URL"):
        return None
    pms_on = os.environ.get("USE_ABELDENT_PMS", "").lower() in ("1", "true", "yes", "on") or should_use_mocks()
    return CaseService(store=SupabaseStore(), repository=None if pms_on else SupabaseCaseRepository(), **kwargs)


def seed_cases(conn: psycopg.Connection, cases_dir: Path) -> int:
    """Load every chart in cases_dir, replacing a chart with the same id."""
    files = sorted(cases_dir.glob("*.yaml"))
    with conn.cursor() as cur:
        cur.executemany("insert into app.patient_case (case_id, chart_yaml, source) values (%s, %s, %s) on conflict (case_id) "
                        "do update set chart_yaml = excluded.chart_yaml, source = excluded.source, updated_at = now()",
                        [(f.stem, f.read_text(), f"{cases_dir.name}/{f.name}") for f in files])
    conn.commit()
    return len(files)
