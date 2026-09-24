#!/usr/bin/env bash
# Size every client asset of a built site/ (raw, gzip, brotli) and name the notable libraries inside each JS chunk.
set -euo pipefail
SITE=${1:?usage: site-bundle-sizes.sh <site dir>}
cd "$SITE/.next/static"
printf "%9s %9s %9s  %s\n" raw gzip brotli file
find . -type f \( -name '*.js' -o -name '*.css' -o -name '*.woff2' \) | while read -r f; do
  raw=$(wc -c < "$f"); gz=$(gzip -9c "$f" | wc -c); br=$(brotli -c "$f" 2>/dev/null | wc -c || echo 0)
  libs=""
  case "$f" in *.js)
    grep -q "WebGLRenderer" "$f" && libs="$libs three"
    grep -q "ZodError\|\$ZodType" "$f" && libs="$libs zod"
    grep -q "react-dom" "$f" && libs="$libs react-dom"
    grep -q "RoomEnvironment\|PMREMGenerator" "$f" && libs="$libs pmrem" ;;
  esac
  printf "%9d %9d %9d  %s%s\n" "$raw" "$gz" "$br" "$f" "${libs:+  [$libs ]}"
done | sort -k1 -n -r
for f in $(ls "$SITE/public"); do printf "public/%s raw=%d gzip=%d\n" "$f" "$(wc -c < "$SITE/public/$f")" "$(gzip -9c "$SITE/public/$f" | wc -c)"; done
