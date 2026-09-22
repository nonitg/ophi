#!/usr/bin/env bash
# Audit what git tracks: size by dir, biggest files, ignored-but-tracked, history bloat, secret-ish names.
set -eu
cd "$(dirname "$0")/.."

echo "== tracked size by top-level dir (working tree bytes) =="
git ls-files -z | xargs -0 stat -f '%z %N' 2>/dev/null \
  | awk '{split($2,p,"/"); d=(p[2]==""?p[1]:p[1]"/"); s[d]+=$1; n[d]++} END{for(k in s) printf "%10.1f KB  %5d files  %s\n", s[k]/1024, n[k], k}' \
  | sort -rn | head -30

echo; echo "== 25 biggest tracked files =="
git ls-files -z | xargs -0 stat -f '%z %N' 2>/dev/null | sort -rn | head -25 \
  | awk '{printf "%10.1f KB  %s\n", $1/1024, $2}'

echo; echo "== tracked but matched by .gitignore =="
git ls-files -ci --exclude-standard

echo; echo "== tracked binary/media by extension =="
git ls-files | grep -Ei '\.(png|jpe?g|gif|webp|mp4|mov|webm|pdf|zip|gz|tar|sqlite|db|ico|woff2?|ttf|otf|psd|fig)$' \
  | sed -E 's/.*\.//' | tr 'A-Z' 'a-z' | sort | uniq -c | sort -rn

echo; echo "== untracked, not ignored (size) =="
git ls-files -o --exclude-standard -z | xargs -0 du -sk 2>/dev/null | sort -rn | head -30

echo; echo "== secret-ish tracked filenames =="
git ls-files | grep -Ei '(\.env|secret|credential|\.pem$|\.key$|id_rsa|token|\.p12$|password)' || echo "(none)"

echo; echo "== biggest blobs in all history (incl. deleted) =="
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectsize) %(rest)' \
  | awk '$1=="blob"' | sort -k2 -rn | head -25 \
  | awk '{printf "%10.1f KB  %s\n", $2/1024, $3}'

echo; echo "== history blobs no longer in HEAD (top 15) =="
git ls-files > /tmp/.repo-audit-head.$$
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectsize) %(rest)' \
  | awk '$1=="blob" && $3!=""' | sort -k2 -rn \
  | while read -r _ sz path; do grep -qxF "$path" /tmp/.repo-audit-head.$$ || printf "%10.1f KB  %s\n" "$((sz/1024))" "$path"; done | head -15
rm -f /tmp/.repo-audit-head.$$

echo; echo "== totals =="
echo "tracked files: $(git ls-files | wc -l)"
git count-objects -vH | grep -E 'size|count'
