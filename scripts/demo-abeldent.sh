#!/usr/bin/env bash
# Demo with the lab ABELDent VM: the demo cases, plus the requests ABELDent sent and Sun Life's answers
# (lab/fixtures/fake-sunlife-responses.sql). Keys such as ANTHROPIC_API_KEY (letter reading) come from .env.
# Usage: ./scripts/demo-abeldent.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
set -a; [ -f "$ROOT/.env" ] && . "$ROOT/.env"; set +a
export OPHI_ABELDENT=1
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8765}"
"$ROOT/lab/vm/vm" sql "SELECT 1 AS one" >/dev/null || { echo "ABELDent VM unreachable: lab/vm/vm status" >&2; exit 1; }
echo "Ophi demo — cases/demo + ABELDent VM sync on http://${HOST}:${PORT}"
exec "$ROOT/.venv/bin/python" -m ophi.cli serve --host "$HOST" --port "$PORT" "$@"
