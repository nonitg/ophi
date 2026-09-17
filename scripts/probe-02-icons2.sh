#!/bin/bash
# Close the Radiographic Templates window, then click each given Imaging toolbar icon x:
# screenshot + non-main window list after each, ESC before the next.
cd "$(dirname "$0")/.." || exit 1
scripts/ui clickxy -X 1162 -Y 20 >/dev/null; sleep 2
scripts/ui windows | grep -v "ABELDent - \|Program Manager"
for x in "$@"; do
  echo "=== icon x=$x"
  scripts/ui clickxy -X $x -Y 161 >/dev/null; sleep 3
  ./lab/vm/vm shot
  scripts/ui windows | grep -v "ABELDent - \|Program Manager"
  scripts/ui keys -Text '{ESC}' >/dev/null; sleep 1
done
