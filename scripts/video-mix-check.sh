#!/usr/bin/env bash
# Per-section loudness and true peak of a rendered pitch mix. Usage: scripts/video-mix-check.sh mix.wav
set -euo pipefail
f="$1"
sections="$(python3 "$(dirname "$0")/video_layout.py" | tr '
' ' ')"
for s in $sections; do
  IFS=: read -r n a b <<<"$s"
  r=$(ffmpeg -v info -ss "$a" -to "$b" -i "$f" -af ebur128=peak=true -f null - 2>&1 | awk '/Summary/{s=1} s&&/I:/{i=$2} s&&/Peak:/{p=$2} END{print i" LUFS, true peak "p" dBFS"}')
  printf '%-8s %s\n' "$n" "$r"
done
