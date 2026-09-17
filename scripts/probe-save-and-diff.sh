#!/bin/bash
# Click a save button at X,Y on the ABELDent view, screenshot, then snapshot+diff the DB.
#   scripts/probe-save-and-diff.sh <X> <Y> <probe-name> "<what was done>"
cd "$(dirname "$0")/.." || exit 1
scripts/ui clickxy -X "$1" -Y "$2" >/dev/null
sleep 4
./lab/vm/vm shot
scripts/probe-step "$3" "$4" 2>/dev/null
