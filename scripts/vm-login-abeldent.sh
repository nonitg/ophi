#!/bin/bash
# Close stray console windows, bring ABELDent's (nameless) login window forward, click Login
# (password is remembered on the lab box), wait for the main window.
cd "$(dirname "$0")/.." || exit 1
V=./lab/vm/vm
$V uexec 'Get-Process WindowsTerminal,OpenConsole -ErrorAction SilentlyContinue | Stop-Process -Force
$p = Get-Process ABELAdo -ErrorAction SilentlyContinue | Select-Object -First 1
if ($p) { (New-Object -ComObject WScript.Shell).AppActivate($p.Id) | Out-Null; "activated ABELAdo " + $p.Id } else { "no ABELAdo process" }'
sleep 2; $V shot
scripts/ui clickxy -X 591 -Y 339 >/dev/null
for i in $(seq 1 12); do
  sleep 10
  w="$(scripts/ui windows 2>/dev/null | grep "ABELDent - [A-Z]")"
  [ -n "$w" ] && { echo "$w"; break; }
done
$V shot
