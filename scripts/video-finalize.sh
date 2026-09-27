#!/usr/bin/env bash
# Two-pass loudness normalize a rendered pitch to -14 LUFS / -1 dBTP (web standard), video stream copied.
# Usage: scripts/video-finalize.sh in.mp4 out.mp4
set -euo pipefail
in="$1"; out="$2"
m=$(ffmpeg -hide_banner -i "$in" -vn -af loudnorm=I=-14:TP=-1:LRA=20:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$m" | python3 -c "import json,sys; print(json.load(sys.stdin)['$1'])"; }
ffmpeg -v error -y -i "$in" -c:v copy -af "loudnorm=I=-14:TP=-1:LRA=20:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true" \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart "$out"
ffmpeg -i "$out" -vn -af ebur128=peak=true -f null - 2>&1 | awk '/Summary/{s=1} s&&/I:/{i=$2} s&&/Peak:/{p=$2} END{print "final: "i" LUFS, true peak "p" dBFS"}'
