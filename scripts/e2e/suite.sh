#!/usr/bin/env bash
# Unit + property tests and the golden-case eval, in a throwaway state dir so a running demo is untouched.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/var/e2e/suite"; mkdir -p "$OUT"
export OPHI_VAR_DIR="$(mktemp -d -t ophi-suite-XXXX)"
"$ROOT/.venv/bin/python" -m pytest -q >"$OUT/pytest.txt" 2>&1; echo "pytest exit $?" >>"$OUT/pytest.txt"
"$ROOT/.venv/bin/python" -m ophi.cli eval >"$OUT/eval.txt" 2>&1; echo "eval exit $?" >>"$OUT/eval.txt"
tail -5 "$OUT/pytest.txt"; tail -5 "$OUT/eval.txt"
