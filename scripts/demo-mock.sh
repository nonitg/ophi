#!/usr/bin/env bash
# Demo with dummy (mock) PMS data — mocks/*.json + mocks/pms/*.json, no VM
# Usage: ./scripts/demo-mock.sh  — or:  make demo-mock
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export USE_MOCK_PMS_API=true
# optional: keep aliases in sync for callers that check them
export USE_MOCK_DATA=true
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8765}"
echo "Colombus demo — MOCK data (mocks/, PmsRepository=Mock) on http://${HOST}:${PORT}"
echo "Toggle: USE_MOCK_PMS_API=true (dummy). Use scripts/demo-real.sh for real cases."
exec "$ROOT/.venv/bin/python" -m colombus.cli serve --host "$HOST" --port "$PORT" "$@"
