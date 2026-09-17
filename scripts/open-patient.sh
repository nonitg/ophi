#!/bin/bash
# Open a patient by PID through the Patient Selection panel. Opens the panel if needed.
#   scripts/open-patient.sh 60
cd "$(dirname "$0")/.." || exit 1
pid="${1:?pid}"
scripts/ui tree -Name 'Patient Selection' -Depth 0 >/dev/null 2>&1 || { scripts/ui click -Id PatientManagerGNB >/dev/null; sleep 3; }
scripts/ui setfield -Name 'Last Name' -Text ''
scripts/ui setfield -Name 'First Name' -Text ''
scripts/ui setfield -Name 'PID' -Text "$pid"
scripts/ui click -Name 'Search Now' >/dev/null; sleep 3
./lab/vm/vm shot
scripts/ui click -Name 'OK' >/dev/null; sleep 5
scripts/ui tree -Depth 3 2>&1 | grep -o "name='PID [0-9]*'" | head -1
