#!/bin/bash
# Verify the inline "wait for ColombusRun idle" command actually runs in the guest and returns fast.
cd "$(dirname "$0")/.." || exit 1
UTMCTL=/Applications/UTM.app/Contents/MacOS/utmctl; VM=44469FC2-B636-412D-8441-9A4A9B04E537
time "$UTMCTL" exec "$VM" --cmd 'C:\Windows\System32\cmd.exe' /c \
  "powershell -NoProfile -Command \"for (\$i=0; \$i -lt 100; \$i++) { if ((schtasks /query /tn ColombusRun /fo csv /nh) -notmatch 'Running') { break }; Start-Sleep -Milliseconds 200 }; 'idle after ' + \$i\" > C:\colombus\out\_wait.txt 2>&1"
sleep 1; "$UTMCTL" file pull "$VM" 'C:\colombus\out\_wait.txt'
echo "--- task state now:"; ./lab/vm/vm exec "schtasks /query /tn ColombusRun /fo csv /nh"
