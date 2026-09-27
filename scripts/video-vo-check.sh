#!/usr/bin/env bash
# Concatenate each section's narration clips and transcribe them, to catch misreads before the mix.
set -euo pipefail
vo="$(cd "$(dirname "$0")/../video/public/vo" && pwd)"; tmp="$(mktemp -d)"
for sec in cold patient problem demo value market vision; do
  ls "$vo"/$sec-*.wav | sort -t- -k2 -n | sed "s/^/file '/;s/$/'/" > "$tmp/$sec.txt"
  ffmpeg -v error -y -f concat -safe 0 -i "$tmp/$sec.txt" -c:a libmp3lame -q:a 4 "$tmp/$sec.mp3"
  printf '\n[%s] ' "$sec"
  elevenlabs speech-to-text convert --model-id scribe_v1 --file "$tmp/$sec.mp3" --format json --query text
done
rm -rf "$tmp"
