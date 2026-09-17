#!/bin/bash
# Last perio-entry attempt: select the Pocket row via its header, click a cell, type, screenshot.
cd "$(dirname "$0")/.." || exit 1
scripts/ui keys -Text '{ESC}' >/dev/null; sleep 1
scripts/ui clickxy -X 85 -Y 243 >/dev/null; sleep 1
scripts/ui clickxy -X 250 -Y 243 >/dev/null; sleep 1
scripts/ui keys -Text '3' >/dev/null; sleep 1
scripts/ui keys -Text '{RIGHT}2' >/dev/null; sleep 1
scripts/ui focus
./lab/vm/vm shot
