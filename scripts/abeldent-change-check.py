"""Live: AbelDentPmsRepository pulls once, then only re-checks ABELDent's chart-change stamp (ad-hoc probe)."""
import sys, time
sys.path.insert(0, ".")
from ophi.sources.pms_repository import AbelDentPmsRepository

repo = AbelDentPmsRepository()
repo.CHECK_SECONDS = 2
for label in ("first pull", "cached", "after check window"):
    t = time.monotonic()
    n = len(repo.list_case_ids())
    print(f"{label}: {time.monotonic() - t:.2f}s, {n} cases, stamp {repo._stamp}")
    time.sleep(2.5 if label == "cached" else 0)
