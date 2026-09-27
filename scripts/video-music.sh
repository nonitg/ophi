#!/usr/bin/env bash
# Compose the pitch video's music cues with ElevenLabs Music. Usage: scripts/video-music.sh <cue> ; cues: a b c end
set -euo pipefail
out="$(cd "$(dirname "$0")/../video/public/music" && pwd)"
compose() { # name length_ms prompt
  python3 -c 'import json,sys; print(json.dumps({"prompt": sys.argv[1], "music_length_ms": int(sys.argv[2]), "force_instrumental": True}))' "$3" "$2" \
    | elevenlabs music compose --json - -o "$out/$1.mp3" -q
  printf '%-14s %5.1fs\n' "$1" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out/$1.mp3")"
}
case "$1" in
  a) compose cue-a-field 53000 "Instrumental nature documentary score that evokes the atmosphere of a classic wildlife film. 0 to 10 seconds: hushed and curious, soft sustained strings, a solo flute and a playful pizzicato tiptoe motif with light clarinet, gently comedic, like observing a rare animal. 10 to 26 seconds: the strings warm with a soft felt piano, human and tender. 26 to 48 seconds: tension builds with a low cello ostinato and ticking percussion, growing unease. At exactly 48 seconds it resolves into a bright, hopeful major chord with a soft chime, then fades out by 53 seconds. Leaves room for a narrator; no vocals." ;;
  b) compose cue-b-product 126000 "Instrumental, modern optimistic product-film underscore at 100 BPM. Warm plucked marimba and kalimba arpeggios, soft felt piano, light brushed percussion and a gentle clean kick, subtle warm synth pad. Understated and clear so a narrator sits on top; steady momentum, small lifts every 16 bars, no big drops, no vocals. Confident, friendly, Canadian indie warmth. Ends on a soft resolve." ;;
  c) compose cue-c-vision 66000 "Instrumental cinematic score for a startup vision. 0 to 2 seconds: a soft shimmering swell like light passing through film. 2 to 19 seconds: intimate felt piano and sustained strings, curious and thoughtful. 19 to 37 seconds: rising string ostinato and soft timpani, something growing and branching out, momentum building. 37 to 53 seconds: fuller strings and warm brass, anticipation climbing. At exactly 54 seconds a triumphant, emotional swell peaks. 56 to 66 seconds: a warm sustained final chord that gently fades. Narrator on top; no vocals." ;;
  end) compose cue-end 9000 "Short instrumental logo sting: a warm felt piano chord with a soft string swell and a gentle bright chime on the last beat, hopeful and clean. No vocals." ;;
esac
