#!/bin/bash
# Two attempts at data entry in the legacy perio grid: double-click a cell and type, then
# inspect the Perio menu for an entry mode. Screenshots after each.
cd "$(dirname "$0")/.." || exit 1
scripts/ui dblclick -X 250 -Y 243 >/dev/null; sleep 1
scripts/ui keys -Text '3{ENTER}' >/dev/null; sleep 1
scripts/ui focus
./lab/vm/vm shot
scripts/ui keys -Text '{ESC}' >/dev/null
scripts/ui clickxy -X 282 -Y 32 >/dev/null; sleep 2
./lab/vm/vm shot
scripts/ui windows
