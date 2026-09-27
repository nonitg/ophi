#!/usr/bin/env bash
# Transcribe rendered narration to catch misreads (audio tags spoken aloud, wrong numbers).
# Usage: scripts/video-stt-check.sh file.mp3 [...]
set -euo pipefail
for f in "$@"; do
  printf '%s: ' "$(basename "$f")"
  elevenlabs speech-to-text convert --model-id scribe_v1 --file "$f" --format json --query text
done
