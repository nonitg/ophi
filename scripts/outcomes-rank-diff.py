"""Show which corpus cases get a different action order once outcome weights are loaded."""
from tests._cases import corpus_files
from ophi.casegen.dsl import load_case
from ophi.engine.assess import assess
from ophi.extract.proposer import propose_for_case
from ophi.outcomes.weights import load
from ophi.rules.loader import default_pack

w = load()
pack = default_pack()
changed = 0
for f in corpus_files():
    case = load_case(f)
    case = case.with_artifacts(propose_for_case(case))
    before = [a.unblocks[0] for a in assess(case, pack).actions]
    after = [a.unblocks[0] for a in assess(case, pack, w).actions]
    if before != after:
        changed += 1
        print(f"{f.relative_to(f.parents[2])}:\n  before {before}\n  after  {after}")
print(f"{changed} of {len(corpus_files())} cases reordered; verdicts unchanged by construction")
