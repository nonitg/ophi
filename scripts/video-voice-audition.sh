#!/usr/bin/env bash
# Render one hook line in several candidate narrator voices so the team can pick by ear.
# Usage: scripts/video-voice-audition.sh  (writes video/audition/*.mp3)
set -euo pipefail
out="$(dirname "$0")/../video/audition"; mkdir -p "$out"
doc='[hushed] Here, at the front desk of a Canadian dental clinic, we observe one of the rarest creatures in the country. [pause] The approved crown request. [sighs] Only thirty-seven in a hundred make it.'
trailer='In a world... where one crown needs two x-rays, a full gum chart, and the blessing of Sun Life... [pause] only thirty-seven percent make it.'
render() { # slug voice_id text
  elevenlabs text-to-speech convert --voice-id "$2" --model-id eleven_v3 --text "$3" -o "$out/$1.mp3" -q
  printf '%-34s %5.1fs\n' "$1" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out/$1.mp3")"
}
render a-doc-old-british      jvcMcno3QtjOzGtfpjoI "$doc"
render b-doc-wildlife-british sIsyDvq54C8vCgtvpJac "$doc"
render c-doc-canadian         Ovio1nb5Thj5cZeW3MPS "$doc"
render d-trailer-chuck        9GVWvaD23xXLseHJlxy8 "$trailer"
render e-trailer-don          JJCR1UICgHnHljtvu5uF "$trailer"
