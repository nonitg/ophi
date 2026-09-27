#!/usr/bin/env bash
# Tile story stills into one sheet, 4 per row. Usage: tools/story/tile.sh <scene> <out.png> <frame...>
set -euo pipefail
d="$(cd "$(dirname "$0")/../../out/checks/story" && pwd)"; scene=$1; out=$2; shift 2
inputs=(); for f in "$@"; do inputs+=(-i "$d/$scene-$(printf %05d "$f").png"); done
n=$#; cols=4; rows=$(( (n + cols - 1) / cols )); layout=""
for ((i=0;i<n;i++)); do x=$(( (i % cols) * 960 )); y=$(( (i / cols) * 540 )); layout+="${x}_${y}|"; done
ffmpeg -v error -y "${inputs[@]}" -filter_complex "xstack=inputs=$n:layout=${layout%|}:fill=black" "$d/$out"
