"""Run one read-only SQL query against the ABELDent lab VM and print rows. Usage: vm-sql.py "SELECT ..." """
import json
import sys

from ophi.sources.pms_repository import AbelDentPmsRepository

for row in AbelDentPmsRepository().sql(sys.argv[1], None):
    print(json.dumps(row, default=str))
