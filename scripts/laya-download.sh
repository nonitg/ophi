#!/usr/bin/env bash
# Fetch the pinned Laya English checkpoint into var/models/laya (gitignored).
# Only the files laya.Agent loads (+ the model card); the repo's *.py are never executed, so skipped.
# Provenance of this repo/sha is checked by scripts/laya-provenance.sh.
set -euo pipefail

REPO="convaiinnovations/laya"
REVISION="55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"   # main as of 2026-09-24 (laya 0.3.20 notes)
WEIGHTS_SHA256="891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c"
DEST="$(cd "$(dirname "$0")/.." && pwd)/var/models/laya"

if [[ -f "$DEST/.revision" && "$(cat "$DEST/.revision")" == "$REVISION" && -f "$DEST/model.safetensors" ]]; then
  echo "present: $DEST @ $REVISION"
  exit 0
fi

mkdir -p "$DEST"
hf download "$REPO" --revision "$REVISION" --local-dir "$DEST" \
  --include "rl_agent_config.json" --include "model.safetensors" \
  --include "tokenizer/*" --include "encoder/*" --include "README.md"

echo "$WEIGHTS_SHA256  $DEST/model.safetensors" | sha256sum -c -
echo "$REVISION" > "$DEST/.revision"
# hf records the commit it resolved for each file; show it so a moved ref would be visible.
echo "resolved revision: $(head -1 "$DEST/.cache/huggingface/download/model.safetensors.metadata")"
du -sh "$DEST"
