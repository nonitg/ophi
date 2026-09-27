#!/bin/bash
# Read-only: open an ABELDent top menu (optionally a submenu path), dump its items, screenshot, then Escape out.
#   scripts/pred-status-menu.sh Insurance ["Sub Item" ...]
cd "$(dirname "$0")/.." || exit 1
for m in "$@"; do scripts/ui click -Name "$m" >/dev/null; sleep 1; done
./lab/vm/vm uexec "& C:\ophi\ui.ps1 tree -Window '' -Depth 0" >/dev/null 2>&1
./lab/vm/vm uexec "Add-Type -AssemblyName UIAutomationClient; \$r=[System.Windows.Automation.AutomationElement]::RootElement; \$c=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::MenuItem); foreach(\$e in \$r.FindAll('Descendants',\$c)){ if(-not \$e.Current.IsOffscreen){ \$e.Current.Name } }"
shot="$(./lab/vm/vm shot)"; echo "$shot"
