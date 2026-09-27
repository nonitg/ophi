#!/usr/bin/env python3
"""Section start/end times of the pitch, from video/src/layout.json and the measured narration (vo.json).

Mirrors video/src/timeline.ts. Import `sections()` from Python, or run it to print `name:start:end` lines.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = json.loads((ROOT / "video/src/layout.json").read_text())
VO = json.loads((ROOT / "video/src/vo.json").read_text())["sections"]


def narrated_seconds(sec):
    lay = LAYOUT["narration"][sec]
    lines = VO[sec]["lines"]
    return lay["lead"] + sum(l["dur"] + (lay["gaps"][i] if i < len(lay["gaps"]) else 0) for i, l in enumerate(lines)) + lay["tail"]


def sections():
    """[(name, start, end)] in seconds, with the end card absorbing the remainder of the runtime (min 4 s)."""
    lengths = {s: narrated_seconds(s) for s in LAYOUT["narration"]}
    lengths.update(LAYOUT["founder"])
    lengths["end"] = max(4, LAYOUT["runtime"] - sum(lengths.values()))
    out, t = [], 0.0
    for s in LAYOUT["order"]:
        # Timeline rounds each section to whole frames; match it.
        d = round(lengths[s] * 30) / 30
        out.append((s, t, t + d))
        t += d
    return out


if __name__ == "__main__":
    for n, a, b in sections():
        print(f"{n}:{a:.3f}:{b:.3f}")
