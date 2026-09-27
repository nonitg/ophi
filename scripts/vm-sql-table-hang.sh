#!/usr/bin/env bash
# Regression check for the long-query hang: queries past the command-line limit, in every format and mode,
# repeated because the old stdin transport hung only some of the time. Dry-run only.
cd "$(dirname "$0")/.."
VM=./lab/vm/vm
LONGQ="SELECT COUNT(*) AS n FROM pat WHERE pid IN ($(seq -s, 1 3000))"
FIX="$(cat lab/fixtures/fake-sunlife-responses.sql)"
t() { local label="$1"; shift; local r="" i; for i in 1 2 3; do timeout 40 $VM sql "$@" >/dev/null 2>&1; r+="$? "; done; printf '%-32s exits: %s\n' "$label" "$r"; }
t "long read table"     "$LONGQ" "" table
t "long read json"      "$LONGQ" "" json
t "fixture dry-run table" "$FIX" "" table "{}" dry-run
t "fixture dry-run json"  "$FIX" "" json "{}" dry-run
t "short read table"    "SELECT TOP 2 pid FROM pat" "" table
