#!/usr/bin/env bash
# Smoke-test the read-only ABELDent API over HTTP against a running `make demo` (default :8765).
B="${1:-http://127.0.0.1:8765}/api/abeldent"
OUT="$(mktemp)"
req() { printf '%-40s ' "GET $1"; curl -s -o "$OUT" -w '%{http_code} ' "$B$1"; head -c 160 "$OUT"; echo; }
req /providers
req "/patients?q=wat"
req /patients/5
req /patients/99999
req "/appointments?date=2026-09-28"
req "/appointments?date=not-a-date"
rm -f "$OUT"
