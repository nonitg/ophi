#!/usr/bin/env bash
# On live Supabase: list the similar-past-request links each fix step shows on a case page.
# Usage: scripts/supabase-similar-check.sh [case_id]   (port 8821)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-/home/arch/Desktop/code/colombus/.venv/bin/python}
case=${1:-kowalchuk}
log=$(mktemp)
env -u SUPABASE_DB_URL PYTHONPATH=. $PY -m ophi.cli serve --port 8821 >"$log" 2>&1 & srv=$!
trap 'kill $srv 2>/dev/null; rm -f "$log"' EXIT
until curl -s -o /dev/null http://127.0.0.1:8821/; do sleep 1; done
html=$(curl -s "http://127.0.0.1:8821/cases/$case")
echo "$html" | grep -o 'Past requests like this[^<]*' | head
echo "$html" | grep -o 'href="[^"]*/past/PA-SYN-[0-9]*[^"]*"' | sort -u
