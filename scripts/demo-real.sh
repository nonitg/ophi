#!/usr/bin/env bash
# Demo with real (filesystem) PMS data — cases/demo/*.yaml
# Usage: ./scripts/demo-real.sh  — or:  make demo-real
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Ensure mock toggle is off (real is the default)
unset USE_MOCK_PMS_API USE_MOCK_DATA PMS_USE_MOCKS 2>/dev/null || true
# allow callers to override host/port via env
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8765}"
echo "Colombus demo — REAL data (cases/demo/, PmsRepository=FileSystem) on http://${HOST}:${PORT}"
echo "Toggle: USE_MOCK_PMS_API is unset (real). Use scripts/demo-mock.sh for dummy fixtures."
exec "$ROOT/.venv/bin/python" -m colombus.cli serve --host "$HOST" --port "$PORT" "$@"
