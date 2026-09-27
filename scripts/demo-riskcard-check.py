#!/usr/bin/env python3
"""The deployed demo ships without torch, so every case page must get its fix plan from cases/demo/laya.
A case whose chart moved since it was scored silently loses its denial-risk card, so check the plan
matches the chart, and that the card reaches whoever owns the step."""
from __future__ import annotations

import os
import re

os.environ["USE_MOCK_PMS_API"] = "true"
os.environ["OPHI_VAR_DIR"] = "/tmp/ophi-riskcard-check"
os.environ.pop("USE_ABELDENT_PMS", None)
os.environ.pop("SUPABASE_DB_URL", None)

from fastapi.testclient import TestClient  # noqa: E402

from ophi.outcomes import readout  # noqa: E402
from ophi.service import CaseService  # noqa: E402
from ophi.web.app import create_app  # noqa: E402

CARD_STAGES = {"patient", "prepare", "dentist"}  # the steps whose card carries the plan

svc = CaseService()
svc.repository.vm_path = "/nonexistent/vm"  # no VM in reach, as on Vercel
app = create_app(svc=svc, live_ml=False, auto_rules_check=False)  # as the deploy runs it

stale, blank = [], []
with TestClient(app) as client:
    for cid in svc.case_ids():
        view = svc.view(cid)
        stage = str(view.stage)
        rd = readout.load(cid)
        matches = bool(rd and rd.matching(view.case))
        # the dentist owns their own step; the MOA owns the chart steps before it
        client.cookies.set("actor", "dentist" if stage == "dentist" else "moa")
        shown = "Denial risk" in client.get(f"/cases/{cid}").text
        want = stage in CARD_STAGES
        print(f"{cid:12} {stage:10} plan={'ok ' if matches else 'STALE'}  card={'yes' if shown else 'no '}{'' if shown == want else '  <- expected ' + ('yes' if want else 'no')}")
        if not matches:
            stale.append(cid)
        if want and not shown:
            blank.append(cid)

print(f"\n{len(svc.case_ids()) - len(stale)}/{len(svc.case_ids())} cases have a plan for the chart as it stands")
if stale or blank:
    raise SystemExit(f"stale plans: {stale or 'none'}; no card where one belongs: {blank or 'none'}")
