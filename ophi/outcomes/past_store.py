"""Past preauth requests in Supabase (outcomes.past_request): loaded from the export folders, read back for
training, the Past outcomes page and similar-request links.

Each clinic is the sending office (the export's provider_id), the same unit training splits by.
"""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from ophi.dental.notation import tooth_class
from ophi.outcomes import store
from ophi.outcomes.adapter import hash_id
from ophi.outcomes.training_set import SENT, Example, examples_from, features, load_examples
from ophi.rules.schema import RulePack

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [ROOT / "fixtures" / d for d in ("cdcp_crowns", "cdcp_approvals", "cdcp_denials")]
TRAINING_SOURCE = "cdcp_crowns"  # the only export with the full feature set (perio values, plan, dated films)
FULL_SCHEMA = "cdcp-preauth-export/2"


def to_row(d: dict, source: str, pack: RulePack) -> dict:
    svc, dec, fu = d["services"][0], d["decision"], d.get("followup")
    sent = {k: d[k] for k in SENT if k in d}
    sent["member"] = {**d["member"], "member_id": hash_id(d["member"]["member_id"])}
    tooth = int(svc["tooth"]) if svc.get("tooth") else None
    full = d.get("schema") == FULL_SCHEMA
    return {
        "preauth_id": d["preauth_id"], "clinic_id": d["provider"]["provider_id"], "source": source,
        "procedure_code": svc["procedure_code"], "tooth_fdi": tooth, "tooth_class": tooth_class(tooth) if tooth else None,
        "age_band": d["member"]["age_band"], "channel": d["submission_channel"],
        "submitted_on": d["submitted_date"], "decided_on": d.get("decision_date"),
        "status": dec["status"], "reason_code": dec.get("reason_code"), "reason_category": dec.get("reason_category"),
        "letter": dec.get("explanation_of_benefits_text"),
        "followup_type": (fu or {}).get("type"), "followup_outcome": (fu or {}).get("outcome"),
        "sent": Jsonb(sent), "decision": Jsonb(dec), "followup": Jsonb(fu) if fu else None,
        # clinic_denial_rate depends on when a request is scored, so it is computed at training time, not stored
        "features": Jsonb(features(examples_from(d)[0], pack, None)) if full else None,
        "pack_version": pack.version if full else None,
        "truth": Jsonb(d["_generator_truth"]) if "_generator_truth" in d else None,
    }


def save_all(conn: psycopg.Connection, pack: RulePack, roots: list[Path] = SOURCES) -> dict[str, int]:
    """Idempotent: re-running replaces each request's row, so a new pack re-reads every request."""
    rows = [to_row(json.loads(f.read_text()), root.name, pack) for root in roots for f in sorted(root.glob("*.json"))]
    clinics = sorted({r["clinic_id"] for r in rows})
    cols = list(rows[0])
    with conn.cursor() as cur:
        cur.executemany("insert into outcomes.clinic values (%s, %s) on conflict (clinic_id) do nothing",
                        [(c, f"Clinic {c.removeprefix('SYN-P-')}") for c in clinics])
        cur.executemany(
            f"insert into outcomes.past_request ({', '.join(cols)}) values ({', '.join(['%s'] * len(cols))}) "
            f"on conflict (preauth_id) do update set {', '.join(f'{c} = excluded.{c}' for c in cols[1:])}, ingested_at = now()",
            [tuple(r[c] for c in cols) for r in rows])
    conn.commit()
    return {"requests": len(rows), "clinics": len(clinics)}


def _export(r: dict) -> dict:
    """A stored row back in export shape, for code that reads exports."""
    return {**r["sent"], "preauth_id": r["preauth_id"], "decision": r["decision"], "followup": r["followup"],
            "decision_date": r["decided_on"] and r["decided_on"].isoformat(), "_generator_truth": r["truth"]}


def training_examples(conn: psycopg.Connection) -> list[Example]:
    """The crown requests Laya and LightGBM train on, in the same order as the export files."""
    cur = conn.cursor(row_factory=dict_row)
    rows = cur.execute("select * from outcomes.past_request where source = %s order by preauth_id", (TRAINING_SOURCE,)).fetchall()
    return [e for r in rows for e in examples_from(_export(r))]


def load_training(from_files: bool = False) -> list[Example]:
    """What the training and eval scripts read: Supabase by default, the export files when offline."""
    if from_files:
        return load_examples()
    with store.connect() as conn:
        return training_examples(conn)


# The app's columns: never the answer key.
_SHOWN = ("preauth_id, clinic_id, source, procedure_code, tooth_fdi, tooth_class, age_band, channel, submitted_on, decided_on, "
          "status, reason_code, reason_category, letter, followup_type, followup_outcome, sent, decision, followup, features")


def requests(conn: psycopg.Connection, clinic_id: str | None = None) -> list[dict]:
    """Every past request (one clinic's, if given), newest first."""
    cur = conn.cursor(row_factory=dict_row)
    where, args = ("where clinic_id = %s", (clinic_id,)) if clinic_id else ("", ())
    return cur.execute(f"select {_SHOWN} from outcomes.past_request {where} order by submitted_on desc, preauth_id", args).fetchall()


def request(conn: psycopg.Connection, preauth_id: str) -> dict | None:
    cur = conn.cursor(row_factory=dict_row)
    return cur.execute(f"select {_SHOWN} from outcomes.past_request where preauth_id = %s", (preauth_id,)).fetchone()


def clinic_denial_rate(conn: psycopg.Connection, clinic_id: str, as_of: date, min_n: int = 3) -> float | None:
    """Share of the clinic's decisions received before as_of that were denials; matches training_set.clinic_denial_rates."""
    n, denied = conn.execute("select count(*), count(*) filter (where status = 'denied') from outcomes.past_request "
                             "where clinic_id = %s and decided_on < %s", (clinic_id, as_of)).fetchone()
    return denied / n if n >= min_n else None


class Cached:
    """All past requests held in memory for a few minutes, so opening a case doesn't query Supabase each time."""

    def __init__(self, connect, ttl_s: float = 300):
        self._connect, self._ttl, self._at, self._rows = connect, ttl_s, 0.0, None

    def rows(self) -> list[dict]:
        if self._rows is None or time.monotonic() - self._at > self._ttl:
            with self._connect() as conn:
                self._rows = requests(conn)
            self._at = time.monotonic()
        return self._rows
