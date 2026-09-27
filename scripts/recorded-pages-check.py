#!/usr/bin/env python3
"""Every demo page must answer from the recording alone, with no VM in reach."""

from __future__ import annotations

import os
import re

from fastapi.testclient import TestClient

os.environ["USE_MOCK_PMS_API"] = "true"
os.environ.pop("USE_ABELDENT_PMS", None)

from ophi.service import CaseService
from ophi.sources.pms_repository import RecordedPmsRepository
from ophi.web.app import create_app

svc = CaseService()
assert isinstance(svc.repository, RecordedPmsRepository), type(svc.repository)
svc.repository.vm_path = "/nonexistent/vm"  # any live query would fail loudly

app = create_app(svc=svc, live_ml=False, auto_rules_check=False)
with TestClient(app) as client:
    for path in ["/", "/recover", "/results", "/settings"]:
        r = client.get(path)
        title = re.search(r"<h1[^>]*>(.*?)</h1>", r.text, re.S)
        print(f"{path:10} {r.status_code}  {(title.group(1).strip() if title else '')[:60]}")
        r.raise_for_status()
    case_id = svc.case_ids()[0]
    r = client.get(f"/cases/{case_id}")
    print(f"/cases/{case_id} {r.status_code}")
    r.raise_for_status()
