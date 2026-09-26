"""Ask the fine-tuned Laya the note questions about each planned crown in the ABELDent fictional charts.

Qualitative only: these charts have no Sun Life decision, so there is nothing to score against. It shows
how the model reads real-PMS-shaped notes, which are longer and messier than the synthetic ones.

Run: .venv/bin/python scripts/laya-abeldent-smoke.py [--model var/models/laya-cdcp]
"""
import argparse
import json
from pathlib import Path

import laya

from ophi.dental.notation import tooth_class
from ophi.outcomes.laya_questions import DECISION, QUESTIONS, YES
from ophi.outcomes.training_set import NOTE_QUESTIONS

ROOT = Path(__file__).resolve().parent.parent
CHARTS = ROOT / "fixtures/abeldent/fictional"


def crown_states() -> list[tuple[str, str]]:
    """(label, request text) per planned crown: notes on that tooth, else the chart's latest three notes."""
    out = []
    for f in sorted(CHARTS.glob("*.json"), key=lambda p: int(p.stem)):
        chart = json.loads(f.read_text())
        notes = sorted(chart["clinical_notes"]["items"], key=lambda n: n["date"])
        for p in (p for p in chart["planned_procedures"]["items"] if p["code"].startswith("27") and p["tooth_fdi"]):
            t = p["tooth_fdi"]
            about = [n for n in notes if n["tooth_fdi"] == t] or notes[-3:]
            text = " ".join(n["text"].strip() for n in about) or "(no notes)"
            out.append((f"chart {f.stem} #{t}", f"Crown {p['code']} on tooth {t} ({tooth_class(t).replace('_', ' ')}).\nNote: {text}"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=ROOT / "var/models/laya-cdcp")
    args = ap.parse_args()
    states = crown_states()
    res = laya.Agent(str(args.model), device="cuda").predict_batch([s for _, s in states], QUESTIONS, batch_size=8)
    short = {q: q[:10] for q in NOTE_QUESTIONS}
    print(f"{'crown':16}" + "".join(f"{short[q]:>11}" for q in NOTE_QUESTIONS) + "   top decision")
    for (label, _), r in zip(states, res):
        a = r["answers"]
        dec = a[DECISION]["probabilities"]
        top = max(dec, key=dec.get)
        print(f"{label:16}" + "".join(f"{a[q]['probabilities'][YES]:11.2f}" for q in NOTE_QUESTIONS) + f"   {top} {dec[top]:.2f}")
    print(f"\nexample text ({states[0][0]}):\n{states[0][1][:400]}")


if __name__ == "__main__":
    main()
