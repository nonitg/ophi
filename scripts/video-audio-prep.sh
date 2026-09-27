#!/usr/bin/env bash
# Loudness-normalize music cues (and stretch cue B to cover demo+value+market) into video/public/music/*.wav,
# and refresh video/src/sfx.json with the sound effects that exist. Re-run after regenerating any audio.
set -euo pipefail
v="$(cd "$(dirname "$0")/../video" && pwd)"
norm() { ffmpeg -v error -y -i "$1" -af "${3:+$3,}loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 -ac 2 "$2"; }
norm "$v/public/music/cue-a-field.mp3"   "$v/public/music/cue-a.wav"
norm "$v/public/music/cue-b-product.mp3" "$v/public/music/cue-b.wav" "atempo=${CUE_B_TEMPO:-0.937}"
norm "$v/public/music/cue-c-vision.mp3"  "$v/public/music/cue-c.wav"
norm "$v/public/music/cue-end.mp3"       "$v/public/music/cue-end.wav"
for f in "$v"/public/music/cue-{a,b,c,end}.wav; do printf '%-10s %6.1fs\n' "$(basename "$f")" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")"; done
python3 - "$v" <<'PY'
import json, sys, pathlib
v = pathlib.Path(sys.argv[1]); names = sorted(p.stem for p in (v / "public/sfx").glob("*") if p.suffix in (".mp3", ".wav") and p.stat().st_size > 0)
exts = {p.stem: p.suffix for p in (v / "public/sfx").glob("*") if p.suffix in (".mp3", ".wav")}
(v / "src/sfx.json").write_text(json.dumps({n: f"sfx/{n}{exts[n]}" for n in names}, indent=1))
print("sfx:", len(names), names)
PY
