#!/usr/bin/env bash
# Full pixel parity between two running builds: baseline captured twice (to learn the noise) plus the candidate,
# each in three parallel shards, then both comparisons.
# Usage: site-parity-pair.sh <out dir> <baseline url> <candidate url>
set -uo pipefail
OUT=${1:?out dir}; BASE=${2:?baseline url}; CAND=${3:?candidate url}
ROOT=$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)
PY="$ROOT/.venv/bin/python"; PARITY="$ROOT/scripts/site-parity.py"
for run in "base1 $BASE" "base2 $BASE" "cand $CAND"; do
  set -- $run
  for i in 0 1 2; do "$PY" "$PARITY" capture "$OUT/$1" "$2" --shard "$i/3" > "$OUT/$1-$i.log" 2>&1 & done
  wait
done
echo "== noise (base1 vs base2)"; "$PY" "$PARITY" compare "$OUT/base1" "$OUT/base2"
echo "== change (base1 vs cand)"; "$PY" "$PARITY" compare "$OUT/base1" "$OUT/cand"
