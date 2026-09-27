#!/usr/bin/env python3
"""What the Look-Back finds in the actual ABELDent database on the lab VM."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from ophi.sources.pms_repository import AbelDentPmsRepository
from ophi.sources.pms_lookback import PmsLookBack

repo = AbelDentPmsRepository()
rep = PmsLookBack(repo).report()
print(f"submitted={rep.submitted} denied={rep.denied} undecided={rep.undecided} "
      f"never_resubmitted={rep.never_resubmitted} (${rep.never_resubmitted_dollars})")
for r in rep.rows:
    print(f"  {r.patient_name:22} {r.code} #{r.tooth_fdi} {r.submitted_on} {r.decision:8} "
          f"${r.fee_dollars:>8,.2f} gaps={r.gaps} unver={r.unverifiable}")
