"""Walk one crown request through the whole pipeline, interactively, to see what each step returns
(docs/plan/05-outcomes-learning.md §3-5):
  1. rule engine: the certain gaps, each tied to a rule-pack clause
  2. fine-tuned Laya: yes/no answers about the note, and its own guess at Sun Life's decision
  3. LightGBM: denial risk from the structured fields plus Laya's note answers, and what drives it
  4. fixer: each candidate fix applied to a copy of the request and re-scored, to see how much risk it removes

Run: make laya-ask   (after make laya-train)
"""
import argparse
import readline  # noqa: F401  arrow keys and history at the prompt
from textwrap import indent

from dotenv import load_dotenv

from ophi.engine.models import Status
from ophi.outcomes.fixer import plan_fixes
from ophi.outcomes.laya_questions import APPROVED, DECISION, QUESTIONS, YES
from ophi.outcomes.past_store import load_training
from ophi.outcomes.risk import RiskModel
from ophi.outcomes.training_set import (NOTE_QUESTIONS, VAGUE, Example, assess_sent, clinic_denial_rates,
                                        request_text, split_by_clinic)
from ophi.rules.loader import default_pack

HELP = """commands:
  <preauth id>       load a past request, e.g. PA-SYN-300008
  note: <text>       rewrite the loaded request's clinical note and rerun, to see how Laya and the risk move
  ask: <question>    ask Laya your own yes/no question about the loaded request. Untrained questions lean "no":
                     fine-tuning made it a specialist in its 8 trained questions, not a chatbot
  blank line         quit"""
OK = {Status.SATISFIED, Status.PENDING_CONFIRMATION, Status.NOT_APPLICABLE}


def outcome(e: Example) -> str:
    if e.decision == APPROVED:
        return "approved"
    if e.decision == VAGUE:
        return f"denied, vague letter (answer key: {e.true_reason})"
    return f"denied: {e.decision}"


def show(e: Example, header: str, model: RiskModel, pack, rate: float | None):
    text = request_text(e)
    print(f"\n━━ {header} ━━\nWhat Laya reads, built only from what the clinic sent:\n{indent(text, '  ')}")

    a = assess_sent(e, pack)
    gaps = [r.label for r in a.requirements if r.status not in OK]
    print(f"\n1. Rule engine: {a.verdict.value}")
    for g in gaps:
        print(f"   not met or unknown: {g}")

    plan = plan_fixes(e.sent, e.submitted_on, pack, model, rate, e.preauth_id)
    print("\n2. Laya, P(yes) per note question:")
    for q, (question, _) in NOTE_QUESTIONS.items():
        print(f"   {plan.note_answers[q]:.2f}  {question}")
    dec = model.agent.predict(text, {DECISION: QUESTIONS[DECISION]})["answers"][DECISION]["probabilities"]
    print("   its guess at the decision: " + ", ".join(f"{k} {p:.2f}" for k, p in sorted(dec.items(), key=lambda kv: -kv[1])[:3]))

    print(f"\n3. LightGBM denial risk: {plan.now.score:.0%} ({plan.now.level}). What pushes it up (+) or down (-):")
    for d in plan.drivers[:6]:
        print(f"   {d.push:+.2f}  {d.label}")

    after = plan.after_fixes
    print(f"\n4. Fixes, with the change in denial risk each makes alone (— : paperwork the model can't re-score).\n"
          f"   After all of them: {after.score:.0%} ({after.level}{', ' + after.because if after.because else ''})")
    for f in plan.fixes:
        drop = "—" if f.risk_drop is None else f"-{f.risk_drop:.0%}" if f.risk_drop >= 0.005 else "0%"
        cite = f"  [{f.clause.ref}]" if f.clause else ""
        print(f"   {drop:>5}  {f.kind:7} {f.who:7} {f.title}{cite}{'  (wait)' if f.wait else ''}")
    print(f"   {plan.remaining}")


def ask(e: Example, question: str, model: RiskModel):
    """A custom question in the same yes/no format the note questions were trained on."""
    q = {**QUESTIONS[next(iter(NOTE_QUESTIONS))], "instructions": question}
    p = model.agent.predict(request_text(e), {"custom": q})["answers"]["custom"]["probabilities"][YES]
    print(f"   P(yes) = {p:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-files", action="store_true", help="read fixtures/cdcp_crowns instead of Supabase")
    args = ap.parse_args()
    load_dotenv()
    pack, model = default_pack(), RiskModel.load()
    parts = split_by_clinic(load_training(args.from_files))
    by_id = {e.preauth_id: (e, split) for split, rows in parts.items() for e in rows}
    rates = clinic_denial_rates([e for e, _ in by_id.values()])
    print(HELP)
    print("\nfrom test clinics, which neither model trained on:\n  " + "\n  ".join(f"{e.preauth_id}  {outcome(e)}" for e in parts["test"][:12]))

    loaded = current = None
    while True:
        try:
            line = input("\nlaya> ").strip()
        except EOFError:
            break
        if not line:
            break
        cmd, _, arg = line.partition(":")
        if line in by_id:
            loaded, split = by_id[line]
            current = loaded
            show(current, f"{line} · {split} clinic · actual: {outcome(loaded)}", model, pack, rates[line])
        elif cmd in ("note", "ask") and current is None:
            print("load a request first")
        elif cmd == "note":
            current = loaded.model_copy(update={"sent": {**loaded.sent, "clinical_notes": arg.strip()}})
            show(current, f"{loaded.preauth_id} with your note · no real decision for this version", model, pack, rates[loaded.preauth_id])
        elif cmd == "ask":
            ask(current, arg.strip(), model)
        else:
            print(HELP)


if __name__ == "__main__":
    main()
