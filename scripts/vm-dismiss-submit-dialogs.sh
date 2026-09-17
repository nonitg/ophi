#!/bin/bash
# Back out of the accidental Print/Submit chain without ever confirming anything:
# dump the hidden "Select Transactions to Submit" window, cancel it, then cancel the Print dialog.
cd "$(dirname "$0")/.." || exit 1
echo "## Select Transactions to Submit tree"
scripts/ui tree -Window 'Select Transactions to Submit' -Depth 3 2>&1 | grep -v "no-rect" | grep -i "button\|cancel\|close\|Window |" | head -12
for name in Cancel Close Exit; do
  scripts/ui click -Window 'Select Transactions to Submit' -Name "$name" >/dev/null 2>&1 && { echo "clicked $name"; break; }
done
sleep 2
scripts/ui windows | grep -c "Select Transactions" | sed 's/^/select-window remaining: /'
# Named Cancel only. Never a coordinate click here: the dialog's OK/Submit sit next to Cancel.
scripts/ui click -Window 'Print Forms' -Name Cancel >/dev/null 2>&1 \
  || scripts/ui click -Name Cancel >/dev/null 2>&1 \
  || echo "Print dialog Cancel not found by name; dismiss it by hand in the VM console"
sleep 2
scripts/ui tree -Name 'Print Forms / Submit Claims' -Depth 0 >/dev/null 2>&1 && echo "print dialog STILL OPEN" || echo "print dialog closed"
scripts/ui windows | grep -v "Program Manager\|File Explorer"
