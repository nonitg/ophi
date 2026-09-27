#!/usr/bin/env bash
# Turn generated effects (public/sfx/*.mp3) into frame-accurate wavs: trim leading silence, -4 dBFS peak.
# Originals move to video/sfx-src/, synthesized fallbacks to video/sfx-synth/ (both outside public/).
set -euo pipefail
v="$(cd "$(dirname "$0")/../video" && pwd)"; mkdir -p "$v/sfx-src" "$v/sfx-synth"
for f in "$v"/public/sfx/*.wav; do [ -e "$f" ] && [ -s "${f%.wav}.mp3" ] && mv "$f" "$v/sfx-synth/"; done
for m in "$v"/public/sfx/*.mp3; do
  [ -e "$m" ] || continue
  n="$(basename "$m" .mp3)"; w="$v/public/sfx/$n.wav"
  trim="silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.01"
  [ "$n" = amb-clinic ] && trim="anull"   # room tone: keep as is
  ffmpeg -v error -y -i "$m" -af "$trim" -ar 48000 -ac 2 "$w.tmp.wav"
  peak=$(ffmpeg -i "$w.tmp.wav" -af volumedetect -f null - 2>&1 | awk '/max_volume/ {print $5}')
  ffmpeg -v error -y -i "$w.tmp.wav" -af "volume=$(echo "-4 - ($peak)" | bc -l)dB" "$w" && rm "$w.tmp.wav"
  mv "$m" "$v/sfx-src/"
  printf '%-12s %5.2fs\n' "$n" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$w")"
done
