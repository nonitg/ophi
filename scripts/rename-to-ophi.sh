#!/usr/bin/env bash
# One-off: rename app "Ophi" -> "Ophi" everywhere except site/ and .git/
set -euo pipefail
cd "$(dirname "$0")/.."

# Case-preserving text replacement in all tracked/work files
find . -path ./site -prune -o -path ./.git -prune -o -path ./uv.lock -prune -o -type f -print |
  while read -r f; do
    sed -i 's/OPHI/OPHI/g; s/Ophi/Ophi/g; s/ophi/ophi/g' "$f"
  done

# Rename the python package directory
mv ophi ophi

echo "Done. Remaining matches:"
rg -il "ophi|columbus" --glob '!site/**' -g '!uv.lock' || true
