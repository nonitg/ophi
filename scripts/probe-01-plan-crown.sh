#!/bin/bash
# Probe 01: fill the inline "Add Planned Treatment" form on the Treatment view (already open)
# with a 27211 crown on tooth 16, but do NOT save. Screenshot so the form can be checked first.
cd "$(dirname "$0")/.." || exit 1
scripts/ui clickxy -X 250 -Y 522            # Code combobox
scripts/ui keys -Text '27211'
sleep 1
scripts/ui keys -Text '{TAB}'
scripts/ui keys -Text '16'
scripts/ui keys -Text '{TAB}'
sleep 1
./lab/vm/vm shot
scripts/ui focus
