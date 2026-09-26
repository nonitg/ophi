#!/bin/bash
# Restart the side-port app with fresh seeded state and screenshot the given paths (desktop + phone).
#   scripts/app-reshoot.sh <out_dir> [path ...]   — port 8801; paths default to app-shots.py's list
cd "$(dirname "$0")/.." || exit 1
out="$1"; shift
lsof -ti tcp:8801 | xargs kill 2>/dev/null
sleep 0.5
nohup scripts/app-serve.sh 8801 >/dev/null 2>&1 &
for _ in $(seq 1 40); do curl -sf -o /dev/null http://127.0.0.1:8801/ && break; sleep 0.25; done
.venv/bin/python scripts/app-shots.py http://127.0.0.1:8801 "$out" "$@" >/dev/null && echo "shots in $out"
