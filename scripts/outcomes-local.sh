#!/usr/bin/env bash
# Run the outcomes pipeline against a throwaway local Postgres: migrate, ingest fixtures, print lift.
# With --shot, also serve the app and screenshot /outcomes (desktop + phone) into $SHOTS (default: /tmp).
set -euo pipefail
cd "$(dirname "$0")/.."
name=ophi-outcomes-local
docker rm -f "$name" >/dev/null 2>&1 || true
docker run -d --rm --name "$name" -e POSTGRES_PASSWORD=local -p 127.0.0.1:54329:5432 postgres:17-alpine >/dev/null
trap 'docker stop "$name" >/dev/null' EXIT
export SUPABASE_DB_URL=postgresql://postgres:local@127.0.0.1:54329/postgres
until .venv/bin/python -c "import psycopg,os; psycopg.connect(os.environ['SUPABASE_DB_URL'],connect_timeout=1).close()" 2>/dev/null; do sleep 0.5; done
.venv/bin/python -c "from ophi.outcomes import store; store.migrate(store.connect())"
.venv/bin/python -m ophi.cli outcomes ingest
.venv/bin/python -m ophi.cli outcomes stats
.venv/bin/python -c "
from ophi.outcomes import store
for r in store.blind_spots(store.connect()): print(r['kind'], r['reason_code'], r['preauth_id'], r['unmodelled_attachments'])"

if [[ "${1:-}" == "--shot" ]]; then
  out=${SHOTS:-/tmp}
  .venv/bin/python -m ophi.cli serve --port 8799 >/dev/null 2>&1 & srv=$!
  trap 'kill $srv; docker stop "$name" >/dev/null' EXIT
  until curl -s -o /dev/null http://127.0.0.1:8799/; do sleep 0.5; done
  .venv/bin/python scripts/app-shot.py http://127.0.0.1:8799/outcomes "$out/outcomes.png" --full
  .venv/bin/python scripts/app-shot.py http://127.0.0.1:8799/outcomes "$out/outcomes-phone.png" --w=390 --h=844 --full
  curl -s http://127.0.0.1:8799/outcomes | grep -Eio "approv(al|ed) (odds|chance|likel)|probabilit|likely to be approved|eligible|covered" | sort | uniq -c || echo "copy check: no banned wording"
fi
