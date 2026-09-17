#!/bin/bash
# Hover each imaging toolbar icon and screenshot to read its tooltip.
cd "$(dirname "$0")/.." || exit 1
for x in "$@"; do
  ./lab/vm/vm uexec "[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($x, 161); Start-Sleep -Milliseconds 1500; 'hovered $x'" >/dev/null
  ./lab/vm/vm shot
done
