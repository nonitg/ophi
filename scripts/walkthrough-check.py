"""Print what the deployed demo shows for a walk-through patient (mocks/pms/walkthrough), step by step, through the
same service calls the app makes: stage, gaps, Ophi's note proposals, dentist pre-fills, and whether a fix plan
matches. Throwaway state; nothing is written to var/.

Usage: .venv/bin/python scripts/walkthrough-check.py [case_id] [--walk]   (default: patel; --walk clicks through the chair
and the lab-code fix)
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ["USE_MOCK_PMS_API"] = "true"
os.environ.pop("USE_ABELDENT_PMS", None)
os.environ.pop("SUPABASE_DB_URL", None)

from ophi.outcomes import readout  # noqa: E402
from ophi.outcomes.readout import demo_states, fingerprint, text_for  # noqa: E402
from ophi.service import CaseService, Store  # noqa: E402
from ophi.web import present  # noqa: E402

cid = next((a for a in sys.argv[1:] if not a.startswith("--")), "patel")
svc = CaseService(store=Store(Path(tempfile.mkdtemp(prefix="ophi-walk-")) / "state"))
svc.repository.vm_path = "/nonexistent/vm"  # as on Vercel
base = svc.base_case(cid)
ahead = {fingerprint(text_for(c)): name for name, c in demo_states(base, svc.pack_for(base))}  # what the scorer scores


def show(label: str) -> None:
    v = svc.view(cid)
    rd = readout.load(cid)
    pre = present.pre_reads_for(v, v.pack, rd)
    print(f"\n== {label}: stage={v.stage}  verdict={v.assessment.verdict.value}  in_chair={present.in_chair(v)}"
          f"  plan={'matches' if rd and rd.matching(v.case) else 'none' if not rd else 'STALE'}"
          f"  scored ahead as={ahead.get(fingerprint(text_for(v.case)), 'NOT SCORED AHEAD')}")
    for g in present.gap_rows(v):
        print(f"   gap   {g['title']}{'  [chair]' if g['chair'] else ''}")
    for p in v.proposals:
        print(f"   note  {p.payload.claim!r}  quote={p.payload.quote!r}")
    for c, r in pre.items():
        print(f"   crit  {c:<26} suggest={r.suggest}  " + "; ".join(f"{e.stance}: {e.text}" for e in r.evidence))


show("as charted")
if "--walk" in sys.argv:
    for rid in ("radiograph_pa", "perio_chart"):
        svc.record_capture(cid, rid, "R. Chen RDH")
        show(f"after taking {rid}")
    svc.apply_fixes(cid, ["lab_codes_current"], "Kim Osei")
    show("after Apply it")
