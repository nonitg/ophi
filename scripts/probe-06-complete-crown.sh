#!/bin/bash
# Probe 06 step 1: select the planned 27211 #16 row (y=479) and press the first Planned Treatment
# toolbar button (755,404), expected "post to today". Screenshot and list dialogs; no DB snapshot yet.
cd "$(dirname "$0")/.." || exit 1
scripts/ui clickxy -X 320 -Y 479 >/dev/null; sleep 1
scripts/ui clickxy -X 755 -Y 404 >/dev/null; sleep 3
./lab/vm/vm shot
scripts/ui windows | grep -v "Program Manager\|File Explorer\|ABELDent - Terry"
