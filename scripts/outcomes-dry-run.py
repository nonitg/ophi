"""Assess every fixture export through the outcomes adapter and print verdict + per-requirement status."""
from collections import Counter
from pathlib import Path

from ophi.engine.assess import assess
from ophi.outcomes.adapter import in_pack, load_export, to_case, to_submission
from ophi.rules.loader import default_pack

pack = default_pack()
verdicts = Counter()
for f in sorted(Path("fixtures").glob("cdcp_*/*.json")):
    d = load_export(f)
    sub = to_submission(d)
    if not in_pack(sub, pack):
        verdicts["out_of_pack"] += 1
        continue
    a = assess(to_case(d, sub), pack)
    verdicts[a.verdict] += 1
    st = {r.requirement_id: r.status.value[:5] for r in a.requirements if r.applicable}
    print(sub.preauth_id, sub.outcome.status[:4], sub.outcome.reason_code or "-", a.verdict, st)
print(verdicts)
