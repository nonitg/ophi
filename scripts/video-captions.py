#!/usr/bin/env python3
"""Write narrator captions (SRT) for the pitch from the measured narration, plus the founder-cam cue sheet.

Timing mirrors video/src/vo.ts (LAYOUT) and video/src/timeline.ts (section order, founder lengths).
Usage: scripts/video-captions.py  → video/out/ophi-pitch.srt, docs/pitch/founder-cam-cues.md
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VO = json.loads((ROOT / "video/src/vo.json").read_text())["sections"]
SCRIPT = (ROOT / "docs/pitch/af-hacks-script.md").read_text()

LAYOUT = {k: (v["lead"], v["gaps"], v["tail"]) for k, v in json.loads((ROOT / "video/src/layout.json").read_text())["narration"].items()}
ORDER = json.loads((ROOT / "video/src/layout.json").read_text())["order"]
FOUNDER = {k: float(v) for k, v in json.loads((ROOT / "video/src/layout.json").read_text())["founder"].items()}
MAX_CHARS = 84  # two lines of ~42


def ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def mmss(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def chunks(words):
    """Split a line's words into caption-sized groups, preferring breaks after punctuation."""
    out, cur = [], []
    for w in words:
        cur.append(w)
        text = " ".join(x["w"] for x in cur)
        if len(text) > MAX_CHARS * 0.6 and re.search(r"[.,:;?!]$", w["w"]) or len(text) > MAX_CHARS:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def main():
    starts, t, srt, n = {}, 0.0, [], 1
    for sec in ORDER:
        starts[sec] = t
        if sec in LAYOUT:
            lead, gaps, tail = LAYOUT[sec]
            lt = t + lead
            for i, line in enumerate(VO[sec]["lines"]):
                for group in chunks(line["words"]):
                    a, b = lt + group[0]["s"], lt + group[-1]["e"] + 0.15
                    srt.append([a, b, " ".join(w["w"] for w in group)])
                lt += line["dur"] + (gaps[i] if i < len(gaps) else 0)
            t = lt + tail
        elif sec in FOUNDER:
            t += FOUNDER[sec]
    starts["_end"] = 300.0
    (ROOT / "video/out").mkdir(exist_ok=True)
    for cur, nxt_cap in zip(srt, srt[1:]):  # never overlap the next caption
        cur[1] = min(cur[1], nxt_cap[0] - 0.02)
    n = len(srt) + 1
    body = [f"{i}\n{ts(a)} --> {ts(b)}\n{text}\n" for i, (a, b, text) in enumerate(srt, 1)]
    (ROOT / "video/out/ophi-pitch.srt").write_text("\n".join(body), encoding="utf-8")

    team = SCRIPT[SCRIPT.index("· Team, traction, plan"):]
    team = [l[2:] for l in team[:team.index("## ", 5)].splitlines() if l.startswith("> ")]
    close = SCRIPT[SCRIPT.index("· Close (FOUNDER"):]
    close = [l[2:] for l in close[:close.index("## ", 5)].splitlines() if l.startswith("> ")]
    nxt = {s: ORDER[i + 1] if i + 1 < len(ORDER) else "_end" for i, s in enumerate(ORDER)}
    md = [
        "# Founder cam — where your footage goes",
        "",
        "The pitch video (`video/out/ophi-pitch.mp4`) is pure black during these two windows. Lay your talking-head",
        "clip over each one in any editor (iMovie, CapCut, Premiere, DaVinci). Record 1920×1080 (or 4K), eye level,",
        "window light on your face, quiet room, phone or lav mic close. A very low music bed plays under both",
        "windows; keep it or turn the video's own audio down there.",
        "",
    ]
    for sec, title, lines in (("team", "Team, traction, plan", team), ("close", "Close", close)):
        a, b = starts[sec], starts[nxt[sec]]
        md += [f"## {title}: {mmss(a)} → {mmss(b)} ({b - a:.0f} s)", ""] + [f"> {l}" for l in lines] + [""]
    md += [
        "Timing tips: the team window fits about 95 words at a relaxed pace, so the four lines above land at about",
        "34 s. Leave half a second of silence at each end, so the cut from the vision scene and into the end card",
        "breathes.",
        "",
        f"Section map: " + " · ".join(f"{s} {mmss(starts[s])}" for s in ORDER),
        "",
    ]
    (ROOT / "docs/pitch/founder-cam-cues.md").write_text("\n".join(md), encoding="utf-8")
    print(f"{n - 1} captions; team {mmss(starts['team'])}–{mmss(starts['close'])}, close {mmss(starts['close'])}–{mmss(starts['end'])}")


if __name__ == "__main__":
    main()
