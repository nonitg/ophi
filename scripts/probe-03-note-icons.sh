#!/bin/bash
# Dismiss the Delete confirm (No), then with the crown row selected try each candidate note icon,
# screenshotting after each so the right one can be identified.
cd "$(dirname "$0")/.." || exit 1
scripts/ui clickxy -X 700 -Y 483 >/dev/null; sleep 2
./lab/vm/vm shot
for x in "$@"; do
  echo "=== icon x=$x"
  scripts/ui clickxy -X 700 -Y 573 >/dev/null; sleep 1
  scripts/ui clickxy -X $x -Y 516 >/dev/null; sleep 3
  ./lab/vm/vm shot
done
