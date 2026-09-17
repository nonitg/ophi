#!/bin/bash
# Dismiss scanner error, cancel capture, close template window, then click each remaining
# Imaging toolbar icon in turn: screenshot + window list after each, ESC before the next.
cd "$(dirname "$0")/.." || exit 1
scripts/ui click -Window Error -Name OK >/dev/null; sleep 1
scripts/ui clickxy -X 849 -Y 631 >/dev/null; sleep 2      # Cancel capture
scripts/ui clickxy -X 100 -Y 631 >/dev/null; sleep 2      # Back
scripts/ui clickxy -X 1162 -Y 20 >/dev/null; sleep 2      # close Radiographic Templates
scripts/ui windows
for x in "$@"; do
  echo "=== icon x=$x"
  scripts/ui clickxy -X $x -Y 161 >/dev/null; sleep 3
  ./lab/vm/vm shot
  scripts/ui windows | grep -v "ABELDent - \|Program Manager"
  scripts/ui keys -Text '{ESC}' >/dev/null; sleep 1
done
