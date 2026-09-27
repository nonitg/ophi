#!/usr/bin/env bash
# Put the whole demo back where it started, so the workflow can be walked again from the top:
# ABELDent's fake chart and claim rows are re-seeded from lab/fixtures/, and every answer, signature,
# decision, follow-up and audit line Ophi recorded is cleared and re-seeded to its opening timeline.
# Usage: ./scripts/reset-demo.sh  — or:  make reset.  ABELDent mode: USE_ABELDENT_PMS=true ./scripts/reset-demo.sh
# The app is safe to leave running: it re-reads ABELDent within 30s, so reload the board after that.
set -euo pipefail
. "$(dirname "$0")/demo-env.sh"

if [ "${USE_ABELDENT_PMS:-}" = "true" ]; then
  "$ROOT/lab/vm/vm" sql "SELECT 1 AS one" >/dev/null || { echo "ABELDent VM unreachable: lab/vm/vm status" >&2; exit 1; }
  # Each fixture deletes its own rows before inserting, so re-running is the reset.
  for f in abeldent-variety fake-sunlife-responses; do
    echo "seeding $f.sql into ABELDent"
    "$ROOT/lab/vm/vm" sql "$(cat "$ROOT/lab/fixtures/$f.sql")" "" json '{}' write >/dev/null
  done
fi

"$ROOT/.venv/bin/python" - <<'PY'
from ophi import db_store, demo
from ophi.outcomes.weights import load as load_weights
from ophi.service import CaseService

svc = db_store.service_from_env(weights=load_weights()) or CaseService(weights=load_weights())
svc.reset()
demo.seed(svc)
print(f"Ophi state cleared and re-seeded ({len(svc.case_ids())} cases)")
PY
