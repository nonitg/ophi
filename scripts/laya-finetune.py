"""Fine-tune Laya on past CDCP crown requests (docs/plan/05-outcomes-learning.md §4.2, §7 step 3).

One model, two kinds of question (ophi/outcomes/laya_questions.py): the note questions, labelled from the
generator's answer key, and "what will Sun Life decide", labelled from letters that name a reason. Trains
on the train clinics, keeps the epoch with the lowest loss on the calibration clinics, fits a temperature
per question size there, and never reads the test clinics. Writes a checkpoint laya.Agent loads.

Loss is soft cross-entropy on the option logits, the term that dominates the official notebook's objective
(NandhaKishorM/laya notebooks/laya_finetune_typed_decisions_2xT4_kaggle.ipynb); learning rates are its.

Run: .venv/bin/python scripts/laya-finetune.py [--epochs 4] [--out var/models/laya-cdcp]
     (after scripts/laya-download.sh)
"""
import argparse
import hashlib
import json
import shutil
import time
from datetime import date
from pathlib import Path

import laya
import torch
from laya.common import QTYPES, build_sequence, clamp_temperature, collate_items, serialize_state, temp_bucket
from safetensors.torch import load_file, save_file

from ophi.outcomes.laya_questions import QUESTIONS, gold
from ophi.outcomes.training_set import CROWNS, load_examples, request_text, split_by_clinic

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "var/models/laya"
BATCH, LR_ENCODER, LR_HEAD, LR_MIN = 16, 2.5e-5, 1.0e-4, 1e-6
TENSORS = ("input_ids", "attention_mask", "marker_pos", "marker_mask", "qtype", "target")


def build_items(examples, tok, cfg) -> list[dict]:
    """One item per (request, labelled question), encoded exactly as laya.Agent encodes at run time."""
    items = []
    for e in examples:
        state = request_text(e)
        state_ids = tok(serialize_state(state).replace(tok.mask_token, " "), add_special_tokens=False)["input_ids"]
        for qid, target in gold(e).items():
            q = laya.Agent._to_internal(QUESTIONS[qid])
            ids, markers = build_sequence(tok, state, q, cfg["max_len"], cfg["head_max_len"], state_ids=state_ids)
            assert len(markers) == len(target), f"{qid}: options do not fit head_max_len"
            items.append({"ids": ids, "markers": markers, "qtype": QTYPES[q["t"]], "target": target})
    return items


def batches(items, pad_id, gen=None):
    order = torch.randperm(len(items), generator=gen).tolist() if gen else list(range(len(items)))
    for s in range(0, len(order), BATCH):
        b = collate_items([[items[i] for i in order[s:s + BATCH]]], pad_id)
        yield {k: b[k].cuda() for k in TENSORS}


def forward(model, b) -> torch.Tensor:
    with torch.autocast("cuda", dtype=torch.bfloat16):
        logits, _ = model(*(b[k] for k in TENSORS[:-1]))
    return logits.float()


def soft_ce(logits, target, mask) -> torch.Tensor:
    return -(target * torch.log_softmax(logits.masked_fill(~mask, -1e4), -1)).sum(-1)


@torch.no_grad()
def calib_logits(model, items, pad_id) -> dict[str, tuple[torch.Tensor, torch.Tensor]]:
    """Raw option logits and targets on the calibration clinics, grouped the way laya applies temperatures."""
    model.eval()
    rows: dict[str, list] = {}
    for b in batches(items, pad_id):
        logits = forward(model, b)
        for z, y, m, qt in zip(logits, b["target"], b["marker_mask"], b["qtype"]):
            k = int(m.sum())
            rows.setdefault(temp_bucket(int(qt), k), []).append((z[:k].cpu(), y[:k].cpu()))
    model.train()
    return {bucket: (torch.stack([z for z, _ in r]), torch.stack([y for _, y in r])) for bucket, r in rows.items()}


def fit_temperature(z: torch.Tensor, y: torch.Tensor) -> float:
    """One temperature minimizing held-out cross-entropy, fitted on log T so it stays positive."""
    log_t = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([log_t], lr=0.1, max_iter=200)

    def closure():
        opt.zero_grad()
        loss = -(y * torch.log_softmax(z / log_t.exp(), -1)).sum(-1).mean()
        loss.backward()
        return loss
    opt.step(closure)
    return log_t.exp().item()


def mean_loss(buckets) -> float:
    n = sum(len(z) for z, _ in buckets.values())
    return sum(float(-(y * torch.log_softmax(z, -1)).sum()) for z, y in buckets.values()) / n


def save_weights(model, out: Path):
    save_file({k: v.detach().half().cpu().contiguous() for k, v in model.state_dict().items()}, out / "model.safetensors")


def data_hash(root: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(root.glob("*.json")):
        h.update(f.read_bytes())
    return "sha256:" + h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--out", type=Path, default=ROOT / "var/models/laya-cdcp")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    torch.manual_seed(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    agent = laya.Agent(str(BASE), device="cuda")
    model, tok, cfg = agent.model, agent.tok, agent.cfg
    model.encoder.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.head_checkpointing = True
    model.train()

    parts = split_by_clinic(load_examples())
    train, calib = build_items(parts["train"], tok, cfg), build_items(parts["calib"], tok, cfg)
    print(f"items: train {len(train)}, calib {len(calib)} | longest {max(len(i['ids']) for i in train + calib)} tokens")

    enc = [p for n, p in model.named_parameters() if n.startswith("encoder.")]
    head = [p for n, p in model.named_parameters() if not n.startswith("encoder.")]
    # fused: the default multi-tensor AdamW needs full-size temporaries that don't fit beside fp32 Adam state in 8 GB
    opt = torch.optim.AdamW([{"params": enc, "lr": LR_ENCODER}, {"params": head, "lr": LR_HEAD}], weight_decay=0.01, fused=True)
    steps = args.epochs * -(-len(train) // BATCH)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps, eta_min=LR_MIN)
    gen = torch.Generator().manual_seed(args.seed)

    history, best = [mean_loss(calib_logits(model, calib, tok.pad_token_id))], None
    print(f"epoch 0 | calib soft-CE {history[0]:.4f} (base checkpoint)")
    for epoch in range(1, args.epochs + 1):
        t0, total = time.perf_counter(), 0.0
        for b in batches(train, tok.pad_token_id, gen):
            loss = soft_ce(forward(model, b), b["target"], b["marker_mask"]).mean()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad(set_to_none=True)
            total += loss.item() * len(b["qtype"])
        history.append(mean_loss(calib_logits(model, calib, tok.pad_token_id)))
        improved = best is None or history[-1] < history[best]
        if improved:
            best = epoch
            save_weights(model, args.out)
        print(f"epoch {epoch} | train soft-CE {total / len(train):.4f} | calib soft-CE {history[-1]:.4f}{' (kept)' if improved else ''} | "
              f"{time.perf_counter() - t0:.0f}s | peak {torch.cuda.max_memory_allocated() / 2**20:.0f} MiB")

    if best != args.epochs:
        model.load_state_dict(load_file(args.out / "model.safetensors"), strict=True)
    fitted = {bucket: fit_temperature(z, y) for bucket, (z, y) in calib_logits(model, calib, tok.pad_token_id).items()}
    for bucket, t in fitted.items():
        print(f"temperature {bucket}: {t:.3f}" + (f" (clamped to {clamp_temperature(t):.3f})" if clamp_temperature(t) != t else ""))

    # Fitted buckets replace the shipped ones, which were fitted to other tasks; other sizes fall back per type.
    out_cfg = {**cfg, "temperature_by_options": {b: clamp_temperature(t) for b, t in fitted.items()},
               "training": {"base_model": f"convaiinnovations/laya@{(BASE / '.revision').read_text().strip()}",
                            "data": data_hash(CROWNS), "split_seed": 2026, "seed": args.seed, "trained_on": str(date.today()),
                            "epochs": args.epochs, "kept_epoch": best, "calib_soft_ce": [round(x, 4) for x in history],
                            "items": {"train": len(train), "calib": len(calib)}, "temperature_fitted": fitted}}
    (args.out / "rl_agent_config.json").write_text(json.dumps(out_cfg, indent=2))
    for d in ("tokenizer", "encoder"):
        shutil.copytree(BASE / d, args.out / d, dirs_exist_ok=True)
    print(f"saved {args.out} (epoch {best})")


if __name__ == "__main__":
    main()
