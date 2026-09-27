#!/usr/bin/env bash
# Generate the pitch video's sound effects (2 at a time: plan concurrency limit). Skips files that exist.
set -uo pipefail
out="$(cd "$(dirname "$0")/../video/public/sfx" && pwd)"
# The sound-effects endpoint rejects the CLI's OAuth login; use an API key kept in the macOS Keychain
# (service "elevenlabs-api-key"). It is only exported to this process, never printed.
if key="$(security find-generic-password -s elevenlabs-api-key -w 2>/dev/null)"; then export ELEVENLABS_API_KEY="$key"; fi
unset key
gen() { # name seconds prompt
  [ -s "$out/$1.mp3" ] && return
  elevenlabs text-to-sound-effects convert --text "$3" --duration-seconds "$2" --prompt-influence 0.6 -o "$out/$1.mp3" -q \
    && printf '%-16s ok\n' "$1" || printf '%-16s FAILED\n' "$1"
}
jobs_list=(
"amb-clinic|10|Quiet dental clinic front desk room tone: distant phone ringing once, soft keyboard typing, a faint dental drill far away, gentle air conditioning hum"
"typewriter|3|Soft vintage typewriter keys typing a short label, close and gentle"
"pop|0.5|Soft round UI pop, light and satisfying"
"whoosh|1.5|Soft airy whoosh, smooth transition swish"
"xray-sweep|2.5|Dental x-ray machine exposure: soft electronic hum rising with a gentle beep at the end"
"stamp|1|Rubber stamp pressed firmly onto paper on a wooden desk, single thud"
"paper-slide|1.2|A paper card sliding across a desk, short"
"counter|2|Fast mechanical flip counter digits rolling, then stopping with a click"
"click|0.5|Crisp single computer mouse click"
"chime|1.2|Gentle friendly UI notification chime, two soft notes"
"pounce|1|Quick cartoon whip swoosh, playful and fast"
"denied|1.2|Low soft negative thunk, muted wooden knock, not harsh"
"approved|1.2|Warm positive bell ding, bright and clean"
"coin|1|Soft cash register ka-ching with a coin clink, light"
"grow|4|Organic growth: plant vines stretching and branching, soft creaking wood and leaves rustling, magical"
"shimmer|3|Soft sparkling digital shimmer, particles of light, gentle"
"riser|3|Cinematic soft riser building tension, airy"
"impact|2|Deep soft cinematic boom impact with a warm tail"
"clock|4|Ticking wall clock, steady, slightly echoey"
"loop-back|1.5|Descending boing-like slide whistle, comedic and short"
)
run2() { local n=0; for j in "${jobs_list[@]}"; do IFS='|' read -r a b c <<<"$j"; gen "$a" "$b" "$c" & n=$((n+1)); if (( n % 2 == 0 )); then wait; fi; done; wait; }
run2
