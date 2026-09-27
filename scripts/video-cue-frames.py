#!/usr/bin/env python3
"""Print section-relative frames of spoken words (same maths as video/src/vo.ts), to pick check stills.
Usage: scripts/video-cue-frames.py demo 0:sorted 2:three 8:reason ..."""
import json, re, sys
from pathlib import Path
V = Path(__file__).resolve().parent.parent / "video/src"
sec, cues = sys.argv[1], sys.argv[2:]
lines = json.loads((V / "vo.json").read_text())["sections"][sec]["lines"]
lay = json.loads((V / "layout.json").read_text())["narration"][sec]
t, starts = lay["lead"], []
for i, l in enumerate(lines):
    starts.append(t); t += l["dur"] + (lay["gaps"][i] if i < len(lay["gaps"]) else 0)
print("section frames", round((t + lay["tail"]) * 30))
norm = lambda s: re.sub(r"[^a-z0-9$%]", "", s.lower())
for c in cues:
    li, w = c.split(":", 1)
    li = int(li)
    hit = next((x for x in lines[li]["words"] if norm(x["w"]) == norm(w)), None)
    print(f"{c:18} {round((starts[li] + hit['s']) * 30) if hit else 'MISSING'}")
