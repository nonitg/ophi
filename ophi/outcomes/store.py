"""Write past submissions + the engine's reading of them to the outcomes schema; read the lift back.

Connects with SUPABASE_DB_URL from the environment; the URL never appears in code, logs or output.
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg

from ophi.engine.models import Assessment
from ophi.outcomes.adapter import PastSubmission
from ophi.rules.schema import RulePack

MIGRATIONS = Path(__file__).resolve().parents[2] / "supabase" / "migrations"


def connect(url: str | None = None) -> psycopg.Connection:
    url = url or os.environ.get("SUPABASE_DB_URL")
    if not url:
        raise RuntimeError("SUPABASE_DB_URL is not set")
    return psycopg.connect(url)


def migrate(conn: psycopg.Connection) -> None:
    for f in sorted(MIGRATIONS.glob("*.sql")):
        conn.execute(f.read_text())
    conn.commit()


def save_denial_map(conn: psycopg.Connection, pack: RulePack, dmap: dict[str, list[str]]) -> None:
    conn.execute("delete from outcomes.denial_map where pack_version = %s", (pack.version,))
    rows = [(pack.version, code, rid) for code, ids in dmap.items() for rid in (ids or [None])]
    with conn.cursor() as cur:
        cur.executemany("insert into outcomes.denial_map values (%s, %s, %s)", rows)


def save(conn: psycopg.Connection, sub: PastSubmission, a: Assessment | None) -> None:
    """Idempotent per preauth_id: a re-ingest under a new pack replaces the old reading."""
    conn.execute(
        """insert into outcomes.submission (preauth_id, member_hash, provider_hash, code, tooth_fdi, age_band, channel,
                                            submitted_on, unmodelled_attachments, pack_version, pack_hash, verdict)
           values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           on conflict (preauth_id) do update set pack_version = excluded.pack_version, pack_hash = excluded.pack_hash,
             verdict = excluded.verdict, unmodelled_attachments = excluded.unmodelled_attachments, ingested_at = now()""",
        (sub.preauth_id, sub.member_hash, sub.provider_hash, sub.code, sub.tooth_fdi, sub.age_band, sub.channel,
         sub.submitted_on, sub.unmodelled_attachments, a and a.ruleset.version, a and a.ruleset.content_hash, a and str(a.verdict)))
    o = sub.outcome
    conn.execute(
        """insert into outcomes.decision values (%s, %s, %s, %s, %s, %s)
           on conflict (preauth_id) do update set status = excluded.status, reason_code = excluded.reason_code,
             reason_category = excluded.reason_category, followup_type = excluded.followup_type,
             followup_outcome = excluded.followup_outcome""",
        (sub.preauth_id, o.status, o.reason_code, o.reason_category, o.followup_type, o.followup_outcome))
    conn.execute("delete from outcomes.requirement_result where preauth_id = %s", (sub.preauth_id,))
    if a:
        with conn.cursor() as cur:
            cur.executemany("insert into outcomes.requirement_result values (%s, %s, %s, %s)",
                            [(sub.preauth_id, r.requirement_id, r.status.value, r.satisfied_via) for r in a.requirements])


def denial_lift(conn: psycopg.Connection, pack_version: str) -> list[dict]:
    cur = conn.execute("select * from outcomes.v_requirement_denial_lift where pack_version = %s order by requirement_id",
                       (pack_version,))
    cols = [c.name for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def blind_spots(conn: psycopg.Connection) -> list[dict]:
    cur = conn.execute("select * from outcomes.v_pack_blind_spots order by kind, reason_code, preauth_id")
    cols = [c.name for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
