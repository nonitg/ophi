#!/usr/bin/env bash
# Serve the app on live Supabase (SUPABASE_DB_URL from .env) and screenshot the screens that read from it.
# Usage: scripts/supabase-demo-check.sh [out-dir]   (port 8820)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-/home/arch/Desktop/code/colombus/.venv/bin/python}
out=${1:-/tmp}
mkdir -p "$out"
env -u SUPABASE_DB_URL PYTHONPATH=. $PY -m ophi.cli serve --port 8820 >"$out/serve.log" 2>&1 & srv=$!
trap 'kill $srv 2>/dev/null' EXIT
until curl -s -o /dev/null http://127.0.0.1:8820/; do sleep 1; done
for page in "/" "/outcomes" "/outcomes?status=denied" "/cases/kowalchuk" "/cases/tremblay" "/past/PA-SYN-300066?from=kowalchuk"; do
  printf '%-40s %s\n' "$page" "$(curl -s -o /dev/null -w '%{http_code} %{time_total}s' "http://127.0.0.1:8820$page")"
done
$PY scripts/app-shot.py http://127.0.0.1:8820/ "$out/live-board.png" --full
$PY scripts/app-shot.py "http://127.0.0.1:8820/cases/kowalchuk" "$out/live-kowalchuk.png" --full
$PY scripts/app-shot.py http://127.0.0.1:8820/outcomes "$out/live-outcomes.png"
grep -E "ML |Supabase|WARNING|ERROR" "$out/serve.log" | sed -E 's#postgresql://[^ ]+#<url>#g' | tail -15
