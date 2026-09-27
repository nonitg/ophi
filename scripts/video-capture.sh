#!/usr/bin/env bash
# Capture the pitch video's app stills: a throwaway Postgres holding the 720 past requests (Past outcomes), the
# demo cases and the recorded ABELDent PMS each on a side port with a fixed clock, then stop everything.
# The CDCP rules check fetches canada.ca, so run it with network access. Usage: scripts/video-capture.sh [out_dir]
set -euo pipefail
cd "$(dirname "$0")/.."
out="${1:-video/public/app-v2}"; demo_port=8821; rec_port=8822; pg=ophi-video-pg
for p in $demo_port $rec_port; do lsof -ti "tcp:$p" | xargs kill 2>/dev/null || true; done
pids=()
cleanup() { for p in "${pids[@]}"; do kill "$p" 2>/dev/null || true; done; docker stop "$pg" >/dev/null 2>&1 || true; }
trap cleanup EXIT

if docker info >/dev/null 2>&1; then
  docker rm -f "$pg" >/dev/null 2>&1 || true
  docker run -d --rm --name "$pg" -e POSTGRES_PASSWORD=local -p 127.0.0.1:54339:5432 postgres:17-alpine >/dev/null
  export SUPABASE_DB_URL=postgresql://postgres:local@127.0.0.1:54339/postgres
  until .venv/bin/python -c "import psycopg,os; psycopg.connect(os.environ['SUPABASE_DB_URL'],connect_timeout=1).close()" 2>/dev/null; do sleep 0.5; done
  .venv/bin/python -c "from ophi.outcomes import store; store.migrate(store.connect())"
  .venv/bin/python -m ophi.cli outcomes ingest | tail -1
else
  echo "docker not running: Past outcomes will read as unavailable"
fi
# python.org builds ship without a CA bundle; the rules check needs one to reach canada.ca.
export SSL_CERT_FILE="$(.venv/bin/python -c 'import certifi; print(certifi.where())')"

serve() { # port mode
  local state; state="$(mktemp -d -t "ophi-video-$2-XXXX")"
  PYTHONPATH="$PWD" .venv/bin/python scripts/video-serve.py "$1" "$state" "$2" > "$state/server.log" 2>&1 &
  pids+=($!)
  for _ in $(seq 60); do curl -sf "http://127.0.0.1:$1/" >/dev/null && return; sleep 0.5; done
  echo "server on $1 did not start"; cat "$state/server.log"; exit 1
}
serve $demo_port demo
serve $rec_port recorded
rm -rf "$out"; mkdir -p "$out"
.venv/bin/python scripts/video-capture.py "http://127.0.0.1:$demo_port" "http://127.0.0.1:$rec_port" "$out"
