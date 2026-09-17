#!/bin/bash
# In Clinical Note Builder (opened via chart-grid icon x=1030 with the 27211 row selected):
# type the probe note into the editor, screenshot, Save, then snapshot+diff.
cd "$(dirname "$0")/.." || exit 1
scripts/ui clickxy -X 566 -Y 410 >/dev/null; sleep 1
scripts/ui keys -Text 'Colombus probe: fractured MB cusp #16, crown recommended' >/dev/null; sleep 1
./lab/vm/vm shot
scripts/ui clickxy -X 647 -Y 777 >/dev/null; sleep 4
./lab/vm/vm shot
scripts/probe-step p03-note "Chart view: select 27211 #16 chart row (700,573), note icon (1030,516) -> Clinical Note Builder, typed text, Save (647,777)" 2>/dev/null | head -120
