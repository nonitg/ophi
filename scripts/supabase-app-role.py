"""Make the app's Supabase login without the password ever leaving this machine.

Generates a random password, writes SUPABASE_DB_URL into the main checkout's gitignored .env, and prints
only the SQL that creates the `ophi_app` role from a SCRAM hash of it. Run that SQL through the Supabase
MCP (or the SQL editor). The role can reach the outcomes schema and nothing else.

    python scripts/supabase-app-role.py --ref <project-ref> --region ca-central-1 > role.sql
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import os
import secrets
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / ".env"
if ".claude/worktrees" in str(ENV):
    ENV = Path(str(ENV).split("/.claude/worktrees")[0]) / ".env"  # worktrees share the main checkout's .env


def scram_verifier(password: str, iterations: int = 4096) -> str:
    salt = os.urandom(16)
    salted = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    client_key = hmac.new(salted, b"Client Key", "sha256").digest()
    stored = hashlib.sha256(client_key).digest()
    server = hmac.new(salted, b"Server Key", "sha256").digest()
    b64 = lambda b: base64.b64encode(b).decode()
    return f"SCRAM-SHA-256${iterations}:{b64(salt)}${b64(stored)}:{b64(server)}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--region", required=True)
    ap.add_argument("--pooler", default="aws-0", help="pooler host prefix: aws-0 or aws-1")
    args = ap.parse_args()
    existing = ENV.read_text() if ENV.exists() else ""
    if "SUPABASE_DB_URL=" in existing:
        raise SystemExit(f"{ENV} already has SUPABASE_DB_URL; remove it first to rotate")
    password = secrets.token_urlsafe(32)
    url = f"postgresql://ophi_app.{args.ref}:{password}@{args.pooler}-{args.region}.pooler.supabase.com:5432/postgres"
    ENV.write_text(existing + f"SUPABASE_DB_URL={url}\n")
    ENV.chmod(0o600)
    print(f"""do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'ophi_app') then create role ophi_app login; end if;
end $$;
alter role ophi_app with login password '{scram_verifier(password)}';
grant usage on schema outcomes to ophi_app;
grant select, insert, update, delete on all tables in schema outcomes to ophi_app;
alter default privileges in schema outcomes grant select, insert, update, delete on tables to ophi_app;
do $$ declare t text; begin
  for t in select tablename from pg_tables where schemaname = 'outcomes' loop
    execute format('drop policy if exists app_all on outcomes.%I', t);
    execute format('create policy app_all on outcomes.%I for all to ophi_app using (true) with check (true)', t);
  end loop;
end $$;""")


if __name__ == "__main__":
    main()
