#!/bin/bash
# Close the perio panel (red X), dismiss any save prompt, open the Imaging view, screenshot.
cd "$(dirname "$0")/.." || exit 1
scripts/ui clickxy -X 1141 -Y 123 >/dev/null; sleep 2
scripts/ui windows | grep -q ABELAdo && scripts/ui click -Window ABELAdo -Name No >/dev/null; sleep 2
scripts/ui click -Name 'Imaging SideBarButton' >/dev/null; sleep 4
./lab/vm/vm shot
scripts/ui windows
