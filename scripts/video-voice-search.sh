#!/usr/bin/env bash
# Search the ElevenLabs shared voice library for character narrators; prints the top hits per term.
set -euo pipefail
for term in "$@"; do
  echo "=== $term"
  elevenlabs voices get_shared --search "$term" --language en --sort usage_character_count_1y --page-size 8 --format json \
    --query 'voices[].{id: voice_id, name: name, g: gender, age: age, acc: accent, d: descriptive, use: use_case, clones: cloned_by_count, desc: description}' \
  | python3 -c "
import json,sys
for v in json.load(sys.stdin):
    print(f\"{v['id']}  {v['name'][:38]:38} {v['g'] or '':6} {v['age'] or '':11} {v['acc'] or '':10} {v['d'] or '':12} {v['use'] or '':22} clones={v['clones']}  | {(v['desc'] or '')[:90]}\")
"
done
