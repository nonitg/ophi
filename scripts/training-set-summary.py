"""Summarize the Laya / tree-model training set built from fixtures/cdcp_crowns: sizes per split, label
balance per note question, reason classes, and the longest request text (Laya's context is 512 tokens)."""
import sys
from collections import Counter

from ophi.outcomes.training_set import NOTE_QUESTIONS, VAGUE, features, clinic_denial_rates, load_examples, note_labels, request_text, split_by_clinic
from ophi.rules.loader import default_pack

examples = load_examples()
parts = split_by_clinic(examples)
print(f"{len(examples)} examples ({sum(e.truth is None for e in examples)} resubmissions)")
for name, rows in parts.items():
    named = sum(e.decision not in (VAGUE,) for e in rows)
    print(f"  {name:5}: {len(rows):3} examples, {len({e.clinic for e in rows})} clinics, {named} with a known decision, "
          f"{sum(e.decision == VAGUE for e in rows)} vague letters")

labelled = [note_labels(e) for e in parts["train"] if e.truth]
print("note questions (train, share true):")
for q in NOTE_QUESTIONS:
    print(f"  {q:22} {sum(l[q] for l in labelled) / len(labelled):.2f}")
print("decision classes (train):", dict(Counter(e.decision for e in parts["train"]).most_common()))

longest = max(examples, key=lambda e: len(request_text(e)))
print(f"\nlongest request text: {len(request_text(longest))} chars, {len(request_text(longest).split())} words ({longest.preauth_id})")
print(request_text(examples[int(sys.argv[1]) if len(sys.argv) > 1 else 10]))

rates = clinic_denial_rates(examples)
f = features(examples[10], default_pack(), rates[examples[10].preauth_id])
print("\nfeatures:", {k: v for k, v in f.items()})
