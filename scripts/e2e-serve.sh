#!/usr/bin/env bash
# Start the ABELDent-backed app for an E2E run, with live Laya + LightGBM, logging to var/e2e-serve.log.
#   scripts/e2e-serve.sh [port]   — kills whatever holds the port first, waits until the worklist answers 200.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-8765}"
LOG="$ROOT/var/e2e-serve.log"
fuser -k "$PORT/tcp" 2>/dev/null || true
: > "$LOG"
PORT="$PORT" nohup "$ROOT/scripts/demo-abeldent.sh" >>"$LOG" 2>&1 &
for _ in $(seq 1 180); do
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/" || true)
  [ "$code" = "200" ] && { echo "up on $PORT"; exit 0; }
  sleep 2
done
echo "did not come up; last 40 log lines:" >&2; tail -40 "$LOG" >&2; exit 1
