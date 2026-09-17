#!/bin/bash
# Relaunch ABELDent in the logged-on user's session without leaving it a child of the ColombusRun
# task (a child keeps the task "Running", which blocks every later vm sql/uexec call).
# explorer.exe re-parents the launched process to the shell, so the task can exit.
cd "$(dirname "$0")/.." || exit 1
V=./lab/vm/vm
echo "## task state / process tree (as SYSTEM)"
$V exec 'schtasks /query /tn ColombusRun /fo csv /nh
Get-CimInstance Win32_Process -Filter "Name=''ABELAdo.exe'' or Name=''powershell.exe'' or Name=''conhost.exe''" | Select-Object ProcessId, ParentProcessId, Name, CreationDate | Format-Table -AutoSize | Out-String
taskkill /IM ABELAdo.exe /F 2>&1
Start-Sleep 3
schtasks /query /tn ColombusRun /fo csv /nh'
echo "## relaunch detached"
$V uexec 'explorer.exe C:\ABELDent\ABELAdo.exe; "launched via explorer"'
for i in $(seq 1 18); do
  sleep 10
  w="$(scripts/ui windows 2>/dev/null | grep -iv "File Explorer\|Program Manager\|Widgets")"
  [ -n "$w" ] && { echo "$w"; break; }
done
./lab/vm/vm shot
