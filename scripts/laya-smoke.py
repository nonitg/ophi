"""Smoke test: load the pinned Laya checkpoint on GPU and ask note questions of one synthetic crown request.

Run: .venv/bin/python scripts/laya-smoke.py   (after scripts/laya-download.sh)
"""
import json
import statistics
import time
from pathlib import Path

import torch
import laya
from laya.common import build_sequence

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "var/models/laya"
FIXTURE = ROOT / "fixtures/cdcp_crowns/PA-SYN-300010.json"
REPEATS = 5

QUESTIONS = {
    "cusp_loss": {
        "type": "noul",
        "instructions": "Does the note document a fractured cusp or lost incisal edge on the requested tooth?",
    },
    # Same question as a neutral-key choice: the card warns noul can follow its false/true labels (#156).
    "cusp_loss_ab": {
        "type": "choice",
        "instructions": "Does the note document a fractured cusp or lost incisal edge on the requested tooth?",
        "criteria": {"A": "no fractured cusp or lost incisal edge is documented",
                     "B": "a fractured cusp or lost incisal edge is documented"},
    },
    "likely_outcome": {
        "type": "choice",
        "instructions": "Which outcome is most likely for this CDCP crown preauthorization?",
        "criteria": {
            "approved": "the crown request is approved",
            "missing_radiograph": "denied: a required radiograph is missing or stale",
            "not_extensively_restored": "denied: the tooth is not extensively restored",
            "active_perio": "denied: active periodontal disease at or around the tooth",
            "other": "denied for some other reason",
        },
    },
}


def timed(fn, repeats):
    """Median wall time (ms) over `repeats` calls, after the caller has warmed up."""
    times = []
    for _ in range(repeats):
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        out = fn()
        torch.cuda.synchronize()
        times.append((time.perf_counter() - t0) * 1000)
    return out, statistics.median(times)


def main():
    note = json.loads(FIXTURE.read_text())["clinical_notes"]
    print("note:", note)

    torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    agent = laya.Agent(str(MODEL_DIR), device="cuda")
    print("load: %.1fs | device=%s amp=%s dtype=%s | params=%.1fM" % (
        time.perf_counter() - t0, agent.device, agent.amp_enabled, agent.dtype,
        sum(p.numel() for p in agent.model.parameters()) / 1e6))

    # The exact sequence the model sees for the noul question.
    q = agent._to_internal(QUESTIONS["cusp_loss"])
    ids, markers = build_sequence(agent.tok, note, q, agent.cfg["max_len"], agent.cfg["head_max_len"])
    print("sequence (%d tokens, markers at %s):\n  %s" % (len(ids), markers, agent.tok.decode(ids)))

    agent.predict(note, QUESTIONS)  # warm-up (CUDA kernels, allocator)
    for qid, qdef in QUESTIONS.items():
        res, ms = timed(lambda: agent.predict(note, {qid: qdef}), REPEATS)
        print("\n[%s] %s  median %.1f ms/call" % (qid, qdef["type"], ms))
        print(json.dumps(res["answers"][qid], indent=2))

    _, ms_all = timed(lambda: agent.predict(note, QUESTIONS), REPEATS)
    print("\nall %d questions in one forward pass: median %.1f ms" % (len(QUESTIONS), ms_all))
    print("peak GPU memory allocated: %.0f MiB (reserved %.0f MiB)" % (
        torch.cuda.max_memory_allocated() / 2**20, torch.cuda.max_memory_reserved() / 2**20))


if __name__ == "__main__":
    main()
