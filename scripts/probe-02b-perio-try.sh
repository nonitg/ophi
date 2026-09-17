#!/bin/bash
# Try one cell at a time with delays, report focus, screenshot. Diagnoses why keystrokes did not land.
cd "$(dirname "$0")/.." || exit 1
scripts/ui clickxy -X 250 -Y 243 >/dev/null; sleep 1
scripts/ui focus
scripts/ui keys -Text '3' >/dev/null; sleep 1
./lab/vm/vm shot
