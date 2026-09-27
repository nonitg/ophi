#!/usr/bin/env bash
# Roles lane: pair every traceback in the serve log with the request line that follows it.
set -euo pipefail
LOG=var/e2e-serve.log
echo "== tracebacks: final exception line + the request logged right after =="
awk '
  /^Traceback \(most recent call last\):/ { intb=1; last=""; next }
  intb && /^[A-Za-z_][A-Za-z0-9_.]*(Error|Exception|Warning)(:|$)/ { last=$0 }
  intb && /^INFO: *[0-9]/ { print last " <<< " $0; intb=0 }
' "$LOG"
echo
echo "== every 4xx/5xx status in the access log =="
grep -oE '"(GET|POST) [^"]+" [45][0-9][0-9]' "$LOG" | sort | uniq -c | sort -rn
echo
echo "== warnings =="
grep -E "^WARNING|WARNING:" "$LOG" | sort | uniq -c
