"""Check that a patient marked inactive in ABELDent drops off the board."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ophi.sources.pms_repository import AbelDentPmsRepository

repo = AbelDentPmsRepository()
rows = repo.sql("SELECT pid, RTRIM(pfname) AS f, RTRIM(plname) AS l, pinactive, pnonpatient FROM pat WHERE pid IN (168,169,170)")
for r in rows:
    print(r)
print("case ids:", sorted(repo.list_case_ids()))
