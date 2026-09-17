#!/bin/bash
# Probe 02: answer "No" to pre-populate, then enter pocket depths on tooth 16 in the fresh exam:
# facial sites 3,2,3 (top Pocket row, y=243) and palatal sites 4,5,6 (bottom Pocket row, y=735).
# Distinct values per site so the diff reveals byte order. Screenshot before saving.
cd "$(dirname "$0")/.." || exit 1
scripts/ui click -Window ABELAdo -Name No >/dev/null
sleep 3
i=0
for x in 250 272 294; do
  vals=(3 2 3); scripts/ui clickxy -X $x -Y 243 >/dev/null; scripts/ui keys -Text "${vals[$i]}" >/dev/null; i=$((i+1))
done
i=0
for x in 250 272 294; do
  vals=(4 5 6); scripts/ui clickxy -X $x -Y 735 >/dev/null; scripts/ui keys -Text "${vals[$i]}" >/dev/null; i=$((i+1))
done
sleep 1
./lab/vm/vm shot
