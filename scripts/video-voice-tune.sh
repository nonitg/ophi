#!/usr/bin/env bash
# Render the hook line in voice "a" with several model/settings combos; print duration, wpm and pause stats.
set -euo pipefail
out="$(dirname "$0")/../video/audition/tune"; mkdir -p "$out"
voice=jvcMcno3QtjOzGtfpjoI
line='Here, at the front desk of a Canadian dental clinic, we observe one of the rarest creatures in the country: the approved preauthorization. Fewer than half make it.'
words=$(echo "$line" | wc -w | tr -d ' ')
render() { # slug model settings-json
  elevenlabs text-to-speech convert --voice-id $voice --model-id "$2" --voice-settings "$3" --text "$line" -o "$out/$1.mp3" -q
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out/$1.mp3")
  pauses=$(ffmpeg -i "$out/$1.mp3" -af silencedetect=n=-35dB:d=0.25 -f null - 2>&1 | grep -c silence_end || true)
  printf '%-22s %5.1fs  %3.0f wpm  pauses>0.25s: %s\n' "$1" "$d" "$(echo "$words*60/$d" | bc -l)" "$pauses"
}
render v3-robust      eleven_v3              '{"stability":1.0,"similarity_boost":0.8,"speed":1.15}'
render v3-natural     eleven_v3              '{"stability":0.5,"similarity_boost":0.8,"speed":1.15}'
render v2-steady      eleven_multilingual_v2 '{"stability":0.65,"similarity_boost":0.8,"style":0.15,"speed":1.15,"use_speaker_boost":true}'
render v2-steady-fast eleven_multilingual_v2 '{"stability":0.7,"similarity_boost":0.8,"style":0.1,"speed":1.2,"use_speaker_boost":true}'
