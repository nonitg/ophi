#!/bin/bash
# Close Radiographic Templates (Back via UIA, then Alt+F4), confirm it is gone, open Patient Notes view.
cd "$(dirname "$0")/.." || exit 1
scripts/ui click -Window 'Radiographic Templates' -Name '‹ Back' >/dev/null; sleep 2
scripts/ui keys -Text '%{F4}' >/dev/null; sleep 2
scripts/ui windows | grep -v "Program Manager"
scripts/ui click -Name 'Patient Notes SideBarButton' >/dev/null; sleep 4
./lab/vm/vm shot
