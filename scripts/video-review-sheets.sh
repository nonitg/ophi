#!/usr/bin/env bash
# Contact sheets of a rendered pitch for review: one sheet per section, one frame every STEP seconds,
# each tile stamped with its timecode. Usage: scripts/video-review-sheets.sh video.mp4 outdir [step]
set -euo pipefail
in="$1"; out="$2"; step="${3:-2}"; mkdir -p "$out"
sections="$(python3 "$(dirname "$0")/video_layout.py" | tr '
' ' ')"
for s in $sections; do
  IFS=: read -r n a b <<<"$s"
  case "$n" in team|close) continue ;; esac
  ffmpeg -v error -y -ss "$a" -to "$b" -i "$in" \
    -vf "fps=1/$step,scale=640:-1,drawtext=text='%{pts\:hms\:$a}':x=8:y=8:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=4,tile=4x0:padding=6:color=white" \
    -frames:v 1 "$out/$n.png" 2>/dev/null || \
  ffmpeg -v error -y -ss "$a" -to "$b" -i "$in" \
    -vf "fps=1/$step,scale=640:-1,drawtext=text='%{pts\:hms\:$a}':x=8:y=8:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=4,tile=4x$(( ( ${b%.*} - ${a%.*} ) / step / 4 + 1 )):padding=6:color=white" \
    -frames:v 1 "$out/$n.png"
  echo "$out/$n.png"
done
