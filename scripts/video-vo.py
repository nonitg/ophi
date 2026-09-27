#!/usr/bin/env python3
"""Generate the pitch narration from docs/pitch/af-hacks-script.md with ElevenLabs.

One clip per spoken line (narrator sections only), stitched with previous/next text for continuity,
then sped up with a pitch-preserving stretch. Writes video/public/vo/<id>.wav and a manifest
video/src/vo.json with per-line durations and word timings (seconds, after the stretch).
Clips are cached by a hash of their inputs, so re-running only regenerates changed lines.

Usage: scripts/video-vo.py [--only cold-0,demo-3] [--force]
"""
import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "docs/pitch/af-hacks-script.md"
OUT = ROOT / "video/public/vo"
MANIFEST = ROOT / "video/src/vo.json"

VOICE = "jvcMcno3QtjOzGtfpjoI"  # "David - Deep Documentary Narrator", audition a
MODEL = "eleven_v3"
SETTINGS = {"stability": 1.0, "similarity_boost": 0.8, "speed": 1.15}
TEMPO = 1.48  # v4: ~18% faster than v1 (1.25), per the team; fits 5:00 without cutting words
# Section order in the script; founder sections and the end card have no narration.
SECTION_IDS = ["cold", "patient", "problem", "demo", "value", "market", "vision", "team", "close", "end"]
NARRATED = {"cold", "patient", "problem", "demo", "value", "market", "vision"}
# Spoken forms the model would otherwise misread.
SAY = {"123Dentist": "one-two-three Dentist"}


def lines_by_section():
    sections, current = {}, None
    for raw in SCRIPT.read_text(encoding="utf-8").splitlines():
        if re.match(r"^## \d+:\d{2}", raw):
            current = SECTION_IDS[len(sections)]
            sections[current] = []
        elif raw.startswith("## "):
            current = None
        elif current in NARRATED and raw.startswith("> "):
            sections[current].append(raw[2:].strip())
    return sections


def spoken(text):
    for k, v in SAY.items():
        text = re.sub(rf"\b{re.escape(k)}\b", v, text)
    return text


def tts(text):
    cmd = ["elevenlabs", "text-to-speech", "convert_with_timestamps", "--voice-id", VOICE, "--model-id", MODEL,
           "--voice-settings", json.dumps(SETTINGS), "--text", text, "--format", "json"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(res.stdout or "{}")
    if res.returncode or "audio_base64" not in data:
        sys.exit(f"TTS failed: {(res.stdout or res.stderr)[-600:]}")
    return data


def words_in(alignment, lo, hi, offset, scale):
    """Words whose characters fall in [lo, hi) of the section text, timed relative to `offset` seconds."""
    chars = alignment["characters"][lo:hi]
    starts = alignment["character_start_times_seconds"][lo:hi]
    ends = alignment["character_end_times_seconds"][lo:hi]
    words, buf, s, e, in_tag = [], "", None, None, False
    def flush():
        if buf:
            words.append({"w": buf, "s": round((s - offset) / scale, 3), "e": round((e - offset) / scale, 3)})
    for ch, cs, ce in zip(chars, starts, ends):
        if ch == "[":
            in_tag = True
        if in_tag:
            in_tag = ch != "]"
            continue
        if ch.isspace():
            flush()
            buf, s = "", None
            continue
        if s is None:
            s = cs
        buf, e = buf + ch, ce
    flush()
    return words


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout
    return float(out)


def render_section(sec, lines):
    """One take per section (v3 can't stitch separate requests), cut into per-line clips at the silences."""
    texts = [spoken(t) for t in lines]
    full = " ".join(texts)
    data = tts(full)
    al = data["alignment"]
    if len(al["characters"]) != len(full):
        sys.exit(f"{sec}: alignment has {len(al['characters'])} chars for {len(full)} input chars")
    raw = OUT / f"{sec}.raw.mp3"
    raw.write_bytes(base64.b64decode(data["audio_base64"]))
    total = duration(raw)
    bounds, pos = [], 0
    for t in texts:
        bounds.append((pos, pos + len(t)))
        pos += len(t) + 1
    st, en = al["character_start_times_seconds"], al["character_end_times_seconds"]
    def speech_start(lo, hi):
        return next(st[i] for i in range(lo, hi) if not full[i].isspace() and full[i] not in "[]")
    def speech_end(lo, hi):
        return next(en[i] for i in range(hi - 1, lo - 1, -1) if full[i].isalnum() or full[i] in ".,!?:;'’")
    cuts = [0.0]
    for (alo, ahi), (blo, bhi) in zip(bounds, bounds[1:]):
        cuts.append((speech_end(alo, ahi) + speech_start(blo, bhi)) / 2)
    cuts.append(total)
    out = []
    for i, ((lo, hi), a, b) in enumerate(zip(bounds, cuts, cuts[1:])):
        wav = OUT / f"{sec}-{i}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(raw),
                        "-af", f"atempo={TEMPO}", "-ar", "48000", "-ac", "1", str(wav)], check=True)
        out.append({"dur": round(duration(wav), 3), "words": words_in(al, lo, hi, a, TEMPO)})
    raw.unlink()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma-separated section ids to regenerate")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    only = set(filter(None, args.only.split(",")))
    OUT.mkdir(parents=True, exist_ok=True)
    old = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"sections": {}}
    manifest = {"voice": VOICE, "model": MODEL, "tempo": TEMPO, "sections": {}}
    for sec, lines in lines_by_section().items():
        if not lines:
            continue
        key = hashlib.sha256(json.dumps([[spoken(t) for t in lines], VOICE, MODEL, SETTINGS, TEMPO]).encode()).hexdigest()[:16]
        cached = old.get("sections", {}).get(sec)
        fresh = cached and cached["key"] == key and all((OUT / f"{sec}-{i}.wav").exists() for i in range(len(lines)))
        if fresh and not args.force and sec not in only:
            manifest["sections"][sec] = cached
            continue
        if only and sec not in only and cached:
            manifest["sections"][sec] = cached
            continue
        clips = render_section(sec, lines)
        manifest["sections"][sec] = {"key": key, "lines": [
            {"id": f"{sec}-{i}", "text": t, "file": f"vo/{sec}-{i}.wav", **c} for i, (t, c) in enumerate(zip(lines, clips))]}
        MANIFEST.write_text(json.dumps(manifest, indent=1))
        print(f"{sec:8} {sum(c['dur'] for c in clips):5.1f}s  " + " | ".join(f"{c['dur']:.1f}" for c in clips))
    MANIFEST.write_text(json.dumps(manifest, indent=1))
    tot = {k: round(sum(l["dur"] for l in v["lines"]), 1) for k, v in manifest["sections"].items()}
    print("section totals:", tot, "sum", round(sum(tot.values()), 1))


if __name__ == "__main__":
    main()
