#!/usr/bin/env bash
# Print ABELDent's vendor data dictionary for a legacy table: position, label, help text. Usage: fda-dump.sh <table>
set -euo pipefail
t="$1"
"$(dirname "$0")/../lab/vm/vm" exec "\$n=@(Get-Content C:\\ABELDent\\Fdats\\${t}names.fda); \$h=@(Get-Content C:\\ABELDent\\Fdats\\${t}helps.fda); for(\$i=0;\$i -lt \$n.Count;\$i++){ '{0,2} {1} | {2}' -f (\$i+1),\$n[\$i],\$h[\$i] }"
