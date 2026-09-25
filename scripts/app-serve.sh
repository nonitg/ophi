#!/bin/bash
# Restart the throwaway-state preview server for ophi/web design work (scripts/demo-screens.py on :8799).
# Usage: scripts/app-serve.sh [state_dir]   — waits until the server answers, then returns.
cd "$(dirname "$0")/.." || exit 1
state="${1:-${TMPDIR:-/tmp}/ophi-app-preview}"
pkill -f "demo-screens.py 8799" 2>/dev/null
sleep 0.5
nohup .venv/bin/python scripts/demo-screens.py 8799 "$state" > "$state.log" 2>&1 &
for _ in $(seq 1 40); do
  code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8799/)
  [ "$code" = "200" ] && { echo "preview up on http://127.0.0.1:8799 (state: $state)"; exit 0; }
  sleep 0.25
done
echo "preview did not start; see $state.log"; tail -20 "$state.log"; exit 1
