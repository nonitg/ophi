#!/bin/bash
# Serve the app exactly as the Vercel demo runs it (recorded PMS, /demo-4ajsmu base path, no models, fresh
# throwaway state), for rehearsing the live walkthrough locally.
#   scripts/demo-deployed-serve.sh [port]   — kills any server already on that port first
cd "$(dirname "$0")/.." || exit 1
port="${1:-8802}"
lsof -ti "tcp:$port" | xargs kill 2>/dev/null
export OPHI_BASE_PATH="/demo-4ajsmu" USE_MOCK_PMS_API=true PYTHONPATH="$PWD"
OPHI_VAR_DIR="$(mktemp -d -t ophi-deployed-XXXX)"; export OPHI_VAR_DIR
unset USE_ABELDENT_PMS SUPABASE_DB_URL
echo "deployed-mode demo on http://127.0.0.1:$port$OPHI_BASE_PATH  state: $OPHI_VAR_DIR"
exec .venv/bin/python -m uvicorn ophi.web.app:app --host 127.0.0.1 --port "$port" --log-level warning
