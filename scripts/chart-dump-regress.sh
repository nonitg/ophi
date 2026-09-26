#!/usr/bin/env bash
# Live regression check: dump every planned-work chart from the VM into a scratch dir and diff
# against the committed fixtures. Volatile fields (extraction timestamps) are expected to differ.
set -uo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-$(mktemp -d)}"
time .venv/bin/python lab/tools/chart_dump.py --out "$OUT" || exit 1
echo "--- files only on one side"
diff <(ls fixtures/abeldent/fictional) <(ls "$OUT")
echo "--- content diffs (per file, first lines)"
for f in "$OUT"/*.json; do
  n="$(basename "$f")"
  [ -f "fixtures/abeldent/fictional/$n" ] || continue
  d="$(diff <(python3 -m json.tool --sort-keys "fixtures/abeldent/fictional/$n") <(python3 -m json.tool --sort-keys "$f"))"
  [ -n "$d" ] && { echo "## $n"; echo "$d" | head -"${LINES_PER_FILE:-12}"; }
done
echo "out: $OUT"
