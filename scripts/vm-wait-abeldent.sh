#!/bin/bash
# Poll until the ABELDent main window (title "ABELDent - <user>") exists, then screenshot.
cd "$(dirname "$0")/.." || exit 1
for i in $(seq 1 "${1:-18}"); do
  w="$(scripts/ui windows 2>/dev/null | grep "name='ABELDent - " | grep -v "File Explorer")"
  [ -n "$w" ] && { echo "$w"; break; }
  sleep 10
done
./lab/vm/vm uexec 'Get-Process ABELAdo -ErrorAction SilentlyContinue | Select-Object Id, Responding, MainWindowTitle | Format-Table -AutoSize | Out-String'
./lab/vm/vm shot
