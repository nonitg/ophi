#!/usr/bin/env bash
# Prove the on-visit source check live: with a server on <base_url> whose OPHI_VAR_DIR is <var_dir> and whose
# rules-watch.json is backdated, one page visit starts the check and the board then shows today's date.
# Usage: scripts/rules-auto-live.sh <base_url> <var_dir>
set -euo pipefail
url=$1; var=$2
for _ in $(seq 1 60); do curl -s -o /dev/null "$url/" && break; sleep 1; done
echo "before: $(grep -o '"checked_on": "[^"]*"' "$var/rules-watch.json" | head -1)"
curl -s -o /dev/null -w "visit: %{http_code} in %{time_total}s\n" "$url/settings"
for _ in $(seq 1 60); do grep -q '"checking_since": null' "$var/rules-watch.json" && grep -q "\"checked_on\": \"$(date +%F)\"" "$var/rules-watch.json" && break; sleep 1; done
echo "after:  $(grep -o '"checked_on": "[^"]*"' "$var/rules-watch.json" | head -1)"
curl -s "$url/" | grep -o 'class="board-rules">[^<]*<a[^>]*>[^<]*' | sed 's/<[^>]*>//g'
