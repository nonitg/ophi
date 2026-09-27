#!/usr/bin/env bash
# Demo with live ABELDent data from the lab VM: every patient with a planned crown becomes a case, and the
# predeterminations ABELDent sent bring Sun Life's answers (lab/fixtures/fake-sunlife-responses.sql).
# Keys such as ANTHROPIC_API_KEY (letter reading) come from .env. State lives apart from the demo files' in var/abeldent.
# Usage: ./scripts/demo-abeldent.sh  — or:  make demo-abeldent. Demo files instead: scripts/demo-real.sh
# Laya + LightGBM run on every case page by default; OPHI_LIVE_ML=0 skips them (fast start, no fix plan).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
set -a; [ -f "$ROOT/.env" ] && . "$ROOT/.env"; set +a
export USE_ABELDENT_PMS=true
export OPHI_VAR_DIR="${OPHI_VAR_DIR:-$ROOT/var/abeldent}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8765}"
"$ROOT/lab/vm/vm" sql "SELECT 1 AS one" >/dev/null || { echo "ABELDent VM unreachable: lab/vm/vm status" >&2; exit 1; }
echo "Ophi demo — ABELDent VM data (USE_ABELDENT_PMS=true, PmsRepository=AbelDent) on http://${HOST}:${PORT}"
exec "$ROOT/.venv/bin/python" -m ophi.cli serve --host "$HOST" --port "$PORT" "$@"
