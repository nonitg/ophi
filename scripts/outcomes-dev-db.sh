#!/usr/bin/env bash
# A long-lived local stand-in for the Supabase outcomes schema on 127.0.0.1:54330: migrate + ingest every
# fixture folder. Use with: export SUPABASE_DB_URL=postgresql://postgres:local@127.0.0.1:54330/postgres
# `scripts/outcomes-dev-db.sh stop` removes it.
set -euo pipefail
cd "$(dirname "$0")/.."
name=ophi-outcomes-dev
PY=${PY:-/home/arch/Desktop/code/colombus/.venv/bin/python}
if [[ "${1:-}" == "stop" ]]; then docker rm -f "$name" >/dev/null; exit; fi
docker rm -f "$name" >/dev/null 2>&1 || true
docker run -d --name "$name" -e POSTGRES_PASSWORD=local -p 127.0.0.1:54330:5432 postgres:17-alpine >/dev/null
export SUPABASE_DB_URL=postgresql://postgres:local@127.0.0.1:54330/postgres
until $PY -c "import psycopg,os; psycopg.connect(os.environ['SUPABASE_DB_URL'],connect_timeout=1).close()" 2>/dev/null; do sleep 0.5; done
PYTHONPATH=. $PY -c "from ophi.outcomes import store; store.migrate(store.connect())"
PYTHONPATH=. $PY -m ophi.cli outcomes ingest
