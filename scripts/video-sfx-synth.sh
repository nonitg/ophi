#!/usr/bin/env bash
# Fallback UI sound effects synthesized with ffmpeg, for when the ElevenLabs SFX endpoint is unavailable.
# Writes video/public/sfx/<name>.wav only where no generated effect exists yet.
set -euo pipefail
out="$(cd "$(dirname "$0")/../video/public/sfx" && pwd)"
mk() { # name duration expression [filters]
  [ -s "$out/$1.mp3" ] || [ -s "$out/$1.wav" ] && return
  ffmpeg -v error -y -f lavfi -i "aevalsrc='$3':s=48000:d=$2" -af "${4:-anull},afade=t=out:st=$(printf "%.3f" "$(echo "$2*0.8" | bc -l)"):d=$(printf "%.3f" "$(echo "$2*0.2" | bc -l)")" -ac 2 "$out/$1.wav"
  echo "$1"
}
noise() { # name duration filters
  [ -s "$out/$1.mp3" ] || [ -s "$out/$1.wav" ] && return
  ffmpeg -v error -y -f lavfi -i "anoisesrc=d=$2:c=pink:r=48000:a=0.6" -af "$3" -ac 2 "$out/$1.wav"
  echo "$1"
}
mk pop 0.18 "0.8*sin(2*PI*(520-1800*t)*t)*exp(-28*t)"
mk click 0.06 "0.9*(random(0)-0.5)*exp(-160*t)+0.4*sin(2*PI*3200*t)*exp(-120*t)" "highpass=f=900"
mk chime 1.2 "0.35*sin(2*PI*1318.5*t)*exp(-4*t)+0.3*sin(2*PI*1760*max(t-0.14,0))*exp(-4*max(t-0.14,0))*gte(t,0.14)"
mk approved 1.2 "0.35*sin(2*PI*1046.5*t)*exp(-3*t)+0.25*sin(2*PI*2093*t)*exp(-5*t)+0.15*sin(2*PI*3136*t)*exp(-7*t)"
mk denied 0.5 "0.7*sin(2*PI*(160-80*t)*t)*exp(-9*t)" "lowpass=f=900"
mk coin 0.9 "0.3*sin(2*PI*2637*t)*exp(-6*t)+0.25*sin(2*PI*3520*max(t-0.08,0))*exp(-6*max(t-0.08,0))*gte(t,0.08)"
mk impact 2.0 "0.9*sin(2*PI*(55+30*exp(-6*t))*t)*exp(-2.2*t)" "lowpass=f=400"
mk shimmer 2.5 "0.12*sin(2*PI*2200*t+3*sin(2*PI*7*t))*exp(-1.2*t)+0.1*sin(2*PI*3300*t+2*sin(2*PI*5*t))*exp(-1.5*t)" "aecho=0.6:0.5:120|240:0.4|0.25"
mk counter 1.2 "0.5*(random(0)-0.5)*exp(-200*mod(t,0.045))*lt(t,1.0)" "highpass=f=1500"
mk typewriter 2.2 "0.6*(random(0)-0.5)*exp(-120*mod(t,0.13+0.02*sin(9*t)))" "bandpass=f=2400:w=1800"
noise whoosh 1.2 "bandpass=f=900:w=800,volume='sin(PI*t/1.2)':eval=frame,afade=t=out:st=1.0:d=0.2"
noise riser 3.0 "highpass=f=300,lowpass=f=6000,volume='(t/3)^2':eval=frame"
noise pounce 0.45 "bandpass=f=2500:w=2000,volume='sin(PI*t/0.45)^3':eval=frame"
noise paper-slide 0.9 "bandpass=f=3500:w=3000,volume='0.6*sin(PI*t/0.9)':eval=frame"
noise stamp 0.6 "lowpass=f=500,volume='exp(-9*t)':eval=frame,afade=t=out:st=0.4:d=0.2"
noise xray-sweep 2.4 "bandpass=f=1400:w=300,volume='0.5*t/2.4':eval=frame"
# Bring each synthesized effect to a -4 dBFS peak so scene volumes mean the same thing for every file.
for f in "$out"/*.wav; do
  peak=$(ffmpeg -i "$f" -af volumedetect -f null - 2>&1 | awk '/max_volume/ {print $5}')
  gain=$(echo "-4 - ($peak)" | bc -l)
  ffmpeg -v error -y -i "$f" -af "volume=${gain}dB" "$f.tmp.wav" && mv "$f.tmp.wav" "$f"
done
