#!/usr/bin/env bash
# Diff every demo page rendered by this worktree against a ref (default main), each from a fresh var dir.
# Usage: scripts/demo-parity.sh <scratch_dir> [ref]
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
scratch=$1; ref=${2:-main}
rm -rf "$scratch/ref" "$scratch/v1" "$scratch/v2" "$scratch/o1" "$scratch/o2"
git -C "$here" worktree add --detach "$scratch/ref" "$ref" -q
trap 'git -C "$here" worktree remove --force "$scratch/ref"' EXIT
mkdir -p "$scratch/v1" "$scratch/v2"
(cd "$scratch/ref" && OPHI_VAR_DIR="$scratch/v1" PYTHONPATH=. "$here/.venv/bin/python" "$here/scripts/demo-parity.py" "$scratch/o1")
(cd "$here" && OPHI_VAR_DIR="$scratch/v2" PYTHONPATH=. .venv/bin/python scripts/demo-parity.py "$scratch/o2")
diff -r "$scratch/o1" "$scratch/o2" && echo "demo output identical to $ref"
