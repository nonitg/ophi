#!/bin/bash
# Serve this checkout's app on a side port with fresh, seeded throwaway state (for UI work and screenshots).
#   scripts/app-serve.sh [port]   — kills any server already on that port first
cd "$(dirname "$0")/.." || exit 1
port="${1:-8801}"
py="${PY:-.venv/bin/python}"; [ -x "$py" ] || py="../colombus/.venv/bin/python"
fuser -k "$port/tcp" 2>/dev/null
state="$(mktemp -d -t ophi-screens-XXXX)"
PYTHONPATH="$PWD" exec "$py" scripts/demo-screens.py "$port" "$state"
