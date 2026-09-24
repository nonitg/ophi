#!/bin/bash
# In the open Clinical Note Builder: type a second note and click Sign Off instead of Save.
# Screenshot + window list (a credential prompt may appear), then snapshot+diff.
cd "$(dirname "$0")/.." || exit 1
scripts/ui clickxy -X 566 -Y 410 >/dev/null; sleep 1
scripts/ui keys -Text 'Ophi probe SIGNED: #16 crown rationale' >/dev/null; sleep 1
scripts/ui clickxy -X 430 -Y 777 >/dev/null; sleep 4
./lab/vm/vm shot
scripts/ui windows | grep -v "Program Manager\|ABELDent - "
