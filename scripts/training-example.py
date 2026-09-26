"""Show one training example the three ways the scripts see it: the request text Laya reads, the exact
token sequences and gold answers it trains on, and the feature row LightGBM gets.

Run: .venv/bin/python scripts/training-example.py [PREAUTH_ID]   (default PA-SYN-300010)
"""
import json
import sys
from pathlib import Path

import laya
from laya.common import build_sequence
from transformers import AutoTokenizer

from ophi.outcomes.laya_questions import QUESTIONS, gold
from ophi.outcomes.training_set import clinic_denial_rates, features, load_examples, request_text
from ophi.rules.loader import default_pack

TOKENIZER = Path(__file__).resolve().parent.parent / "var/models/laya/tokenizer"

examples = load_examples()
e = next(x for x in examples if x.preauth_id == (sys.argv[1] if len(sys.argv) > 1 else "PA-SYN-300010"))
print(f"== {e.preauth_id} | clinic {e.clinic} | decision label: {e.decision} | true reason: {e.true_reason}\n")
print("-- 1. request text (Laya's input) --")
print(request_text(e))

tok = AutoTokenizer.from_pretrained(str(TOKENIZER))
targets = gold(e)
print(f"\n-- 2. training items: {len(targets)} questions have a label --")
for qid, target in list(targets.items())[:2] + [(q, t) for q, t in targets.items() if q == "decision"]:
    ids, markers = build_sequence(tok, request_text(e), laya.Agent._to_internal(QUESTIONS[qid]), 512, 192)
    head = tok.decode(ids[:markers[-1] + 6]).replace("\n", " ")
    print(f"{qid}: {len(ids)} tokens, {len(markers)} options, target {target if len(target) <= 2 else [round(t) for t in target]}")
    print(f"   {head[:260]}{' …' if len(head) > 260 else ''}")

print("\n-- 3. LightGBM feature row --")
f = features(e, default_pack(), clinic_denial_rates(examples)[e.preauth_id])
print(json.dumps(f, indent=1))
