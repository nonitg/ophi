#!/usr/bin/env python3
"""Step 6 of the ingestion plan: diff-after-action probes against the ABELDent database.

    probe.py snapshot A            # hash every row of every table; keep full rows of small tables
    <do one thing in the ABELDent UI>
    probe.py snapshot B
    probe.py diff A B              # which tables changed, which rows, which columns

Read-only, via `vm sql`. Snapshots live in lab/out/probe/<name>.json and are never committed —
they are Fictional Data, but the habit matters.

Why hashes and not triggers or CDC: we never create an object inside the vendor database.
Why full rows for small tables: a probe is only useful if it says "column jneedsxrays went from
'' to 'Y'", not just "table jcf changed". Small tables (<= ROW_CAP rows) are stored whole so the
diff can show before/after per column; big ones are hash-only and the diff fetches the changed
rows' current values from the live database.
"""
import argparse
import csv
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
VM = LAB / "vm" / "vm"
OUT = LAB / "out" / "probe"
CATALOG = LAB / "out"  # columns.csv, pks.csv written by the recon queries

ROW_CAP = 600          # tables at or under this many rows are stored in full
BATCH_ROWS = 4000      # rows per vm sql round trip (one guest file pull per call)
NULL = "<NULL>"
BINARY = {"binary", "varbinary", "image", "timestamp", "rowversion"}
TEXTY = {"text", "ntext", "xml"}
DATE_RE = re.compile(r"^/Date\((-?\d+)\)/$")


# ---------------------------------------------------------------- catalog

def load_catalog():
    cols = defaultdict(list)
    with open(CATALOG / "columns.csv", newline="") as f:
        for r in csv.DictReader(f):
            cols[r["tbl"]].append((int(r["column_id"]), r["col"], r["type"]))
    for t in cols:
        cols[t].sort()
    pks = defaultdict(list)
    with open(CATALOG / "pks.csv", newline="") as f:
        for r in csv.DictReader(f):
            pks[r["tbl"]].append((int(r["key_ordinal"]), r["col"]))
    pks = {t: [c for _, c in sorted(v)] for t, v in pks.items()}
    return cols, pks


def refresh_catalog():
    """Re-pull columns.csv, pks.csv and row counts. Run after an ABELDent update."""
    q = {
        "columns.csv": "SELECT t.name tbl, c.column_id, c.name col, ty.name type, c.max_length FROM sys.columns c "
                       "JOIN sys.tables t ON t.object_id=c.object_id JOIN sys.types ty ON ty.user_type_id=c.user_type_id "
                       "ORDER BY t.name, c.column_id",
        "pks.csv": "SELECT t.name tbl, c.name col, ic.key_ordinal FROM sys.indexes i "
                   "JOIN sys.index_columns ic ON ic.object_id=i.object_id AND ic.index_id=i.index_id "
                   "JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id "
                   "JOIN sys.tables t ON t.object_id=i.object_id WHERE i.is_primary_key=1 ORDER BY t.name, ic.key_ordinal",
    }
    for name, query in q.items():
        r = subprocess.run([str(VM), "sql", query, "", "csv"], capture_output=True, text=True, check=True)
        (CATALOG / name).write_text(r.stdout.strip() + "\n")
        print(f"wrote {CATALOG / name}")


def row_counts():
    rows = sql_json("SELECT t.name tbl, ISNULL(SUM(p.rows),0) n FROM sys.tables t LEFT JOIN sys.partitions p "
                    "ON p.object_id=t.object_id AND p.index_id IN (0,1) GROUP BY t.name")
    return {r["tbl"]: int(r["n"]) for r in rows[0]}


# ---------------------------------------------------------------- sql plumbing

def sql_json(query):
    """Run a batch (possibly several statements); return one list of rows per result set."""
    t0 = datetime.now()
    r = subprocess.run([str(VM), "sql", query, "", "json"], capture_output=True, text=True)
    body = r.stdout.strip()
    print(f"    sql {len(query):>7}B {len(body):>8}B out {(datetime.now() - t0).total_seconds():5.1f}s", file=sys.stderr)
    if not body or body.startswith("REFUSED") or "Exception" in body[:300]:
        raise RuntimeError(f"vm sql failed: {(body or r.stderr)[:500]}\n--- query head ---\n{query[:300]}")
    sets = []
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        if isinstance(data, dict):
            data = data["value"] if "value" in data and "Count" in data else [data]
        sets.append(data)
    return sets


def q(name):
    return f"[{name}]"


def as_text(col, typ):
    c = q(col)
    if typ in BINARY:
        return f"ISNULL(CONVERT(varchar(max), CONVERT(varbinary(max), {c}), 2), '{NULL}')"
    if typ in TEXTY:
        return f"ISNULL(CONVERT(nvarchar(max), {c}), '{NULL}')"
    if typ in ("datetime", "datetime2", "smalldatetime", "date", "time", "datetimeoffset"):
        return f"ISNULL(CONVERT(nvarchar(max), {c}, 121), '{NULL}')"
    return f"ISNULL(CONVERT(nvarchar(max), {c}), '{NULL}')"


def hash_stmt(tbl, cols, pk):
    body = ", ".join(as_text(c, t) for _, c, t in cols)
    # Style 121 keeps seconds/milliseconds; the default datetime→string drops seconds, so two
    # Notes rows one second apart collapsed into one key and the diff hid a version flip.
    key = (" + '|' + ".join(f"ISNULL(CONVERT(nvarchar(max), {q(c)}, 121), '{NULL}')" for c in pk)
           if pk else "''")
    # CONCAT_WS wants >= 3 arguments; pad so one-column tables do not error out the whole batch.
    return (f"SELECT '{tbl}' t, {key} k, CONVERT(varchar(64), HASHBYTES('SHA2_256', CONCAT_WS('|', '', '', {body})), 2) h "
            f"FROM {q(tbl)}")


def rows_stmt(tbl, cols, where=""):
    proj = ", ".join(
        f"CONVERT(varchar(max), CONVERT(varbinary(max), {q(c)}), 2) AS {q(c)}" if t in BINARY
        else f"CONVERT(nvarchar(max), {q(c)}, 121) AS {q(c)}" if t.startswith("date") or t in ("smalldatetime", "time")
        else f"CONVERT(nvarchar(max), {q(c)}) AS {q(c)}" if t in TEXTY
        else q(c)
        for _, c, t in cols)
    return f"SELECT {proj} FROM {q(tbl)} {where}"


def batches(items, weight):
    """Group (tbl, ...) items so each batch carries <= BATCH_ROWS rows (a lone big table is its own batch)."""
    cur, cur_w = [], 0
    for it in items:
        w = max(1, weight(it))
        if cur and cur_w + w > BATCH_ROWS:
            yield cur
            cur, cur_w = [], 0
        cur.append(it)
        cur_w += w
    if cur:
        yield cur


# ---------------------------------------------------------------- snapshot

def snapshot(name, note):
    cols, pks = load_catalog()
    counts = row_counts()
    tables = sorted(t for t in cols if t in counts)
    snap = {"name": name, "note": note, "taken": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "counts": counts, "hashes": {}, "rows": {}, "nopk": []}

    # Pass 1: row hashes for every table (empty ones included — a probe may populate them).
    todo = [(t, counts[t]) for t in tables]
    n_calls = 0
    for batch in batches(todo, lambda it: it[1]):
        stmts = [hash_stmt(t, cols[t], pks.get(t, [])) for t, _ in batch]
        try:
            sets = sql_json(";\n".join(stmts))
        except RuntimeError:
            # One table in the batch has a type CONCAT_WS/HASHBYTES will not take. Isolate it.
            sets = []
            for t, _ in batch:
                try:
                    sets.extend(sql_json(hash_stmt(t, cols[t], pks.get(t, []))))
                except RuntimeError as e:
                    print(f"  ! {t}: {str(e).splitlines()[0][:120]}", file=sys.stderr)
                    sets.append([])
        n_calls += 1
        for (t, _), rows in zip(batch, sets):
            h = defaultdict(list)
            for r in rows:
                h[r["k"] if pks.get(t) else r["h"]].append(r["h"])
            snap["hashes"][t] = {k: (v[0] if len(v) == 1 else v) for k, v in h.items()}
            if not pks.get(t):
                snap["nopk"].append(t)
        print(f"  hashed {sum(1 for _ in batch):>3} tables ({sum(c for _, c in batch):>6} rows)  call {n_calls}", file=sys.stderr)

    # Pass 2: full rows for small tables, keyed like the hashes so diff can show columns.
    small = [(t, counts[t]) for t in tables if 0 < counts[t] <= ROW_CAP]
    for batch in batches(small, lambda it: it[1]):
        sets = sql_json(";\n".join(rows_stmt(t, cols[t]) for t, _ in batch))
        for (t, _), rows in zip(batch, sets):
            pk = pks.get(t, [])
            keyed = {}
            for r in rows:
                r = {k: fix_date(v) for k, v in r.items()}
                k = "|".join(str(r[c]) if r[c] is not None else NULL for c in pk) if pk else json.dumps(r, sort_keys=True, default=str)
                keyed[k] = r
            snap["rows"][t] = keyed
        print(f"  stored {len(batch):>3} small tables in full", file=sys.stderr)

    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{name}.json"
    p.write_text(json.dumps(snap, default=str))
    total = sum(len(v) for v in snap["hashes"].values())
    print(f"{p}  tables={len(snap['hashes'])} rows={total} full_rows_tables={len(snap['rows'])}")


def fix_date(v):
    if isinstance(v, str):
        m = DATE_RE.match(v)
        if m:
            return datetime.fromtimestamp(int(m.group(1)) / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return v


# ---------------------------------------------------------------- diff

def load(name):
    return json.loads((OUT / f"{name}.json").read_text())


def diff(a_name, b_name, show_rows=True, fetch_live=True):
    a, b = load(a_name), load(b_name)
    cols, pks = load_catalog()
    changed_tables = []
    for t in sorted(set(a["hashes"]) | set(b["hashes"])):
        ha, hb = a["hashes"].get(t, {}), b["hashes"].get(t, {})
        added = sorted(set(hb) - set(ha))
        removed = sorted(set(ha) - set(hb))
        changed = sorted(k for k in set(ha) & set(hb) if ha[k] != hb[k])
        if added or removed or changed:
            changed_tables.append((t, added, removed, changed))

    print(f"# probe diff {a_name} -> {b_name}")
    print(f"# A: {a['taken']}  {a.get('note') or ''}\n# B: {b['taken']}  {b.get('note') or ''}")
    if not changed_tables:
        print("no changes")
        return
    print(f"\n{'table':<40} {'+':>5} {'-':>5} {'~':>5}  pk")
    for t, add, rem, chg in changed_tables:
        print(f"{t:<40} {len(add):>5} {len(rem):>5} {len(chg):>5}  {','.join(pks.get(t, [])) or '(none)'}")
    if not show_rows:
        return

    for t, add, rem, chg in changed_tables:
        print(f"\n## {t}")
        ra, rb = a["rows"].get(t, {}), b["rows"].get(t, {})
        live = {}
        if fetch_live and (add or chg) and not rb and pks.get(t):
            live = fetch_rows(t, cols[t], pks[t], add + chg)
        for k in add:
            print(f"  + {k}")
            show(rb.get(k) or live.get(k))
        for k in rem:
            print(f"  - {k}")
            show(ra.get(k))
        for k in chg:
            print(f"  ~ {k}")
            before, after = ra.get(k), rb.get(k) or live.get(k)
            if before and after:
                for c in after:
                    if before.get(c) != after.get(c):
                        print(f"      {c}: {before.get(c)!r} -> {after.get(c)!r}")
            else:
                show(after)


def show(row, indent="      "):
    if not row:
        print(f"{indent}(row values not stored; table over ROW_CAP and no pk to fetch by)")
        return
    for c, v in row.items():
        if v not in (None, "", NULL):
            print(f"{indent}{c} = {v!r}")


def fetch_rows(tbl, cols, pk, keys):
    if len(pk) != 1 or not keys:
        return {}
    ks = ",".join("'" + k.replace("'", "''") + "'" for k in keys)
    where = f"WHERE CONVERT(nvarchar(max), {q(pk[0])}) IN ({ks})"
    rows = sql_json(rows_stmt(tbl, cols, where))[0]
    return {str(fix_date(r[pk[0]])): {k: fix_date(v) for k, v in r.items()} for r in rows}


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot"); s.add_argument("name"); s.add_argument("--note", default="")
    d = sub.add_parser("diff"); d.add_argument("a"); d.add_argument("b")
    d.add_argument("--tables-only", action="store_true"); d.add_argument("--no-live", action="store_true")
    sub.add_parser("refresh-catalog")
    a = ap.parse_args()
    if a.cmd == "snapshot":
        snapshot(a.name, a.note)
    elif a.cmd == "diff":
        diff(a.a, a.b, show_rows=not a.tables_only, fetch_live=not a.no_live)
    else:
        refresh_catalog()


if __name__ == "__main__":
    main()
