"""Roles lane: permission matrix over every mutating endpoint, as coordinator and as dentist.

Every request is deliberately shaped to be REJECTED (bogus ids, missing fields, wrong stage) so the
matrix does not mutate state other E2E lanes depend on. /reset is never called.
"""
import json
import re
import sys

import httpx

BASE = "http://127.0.0.1:8765"
C164 = "abeldent_164"  # waiting on Sun Life
C166 = "abeldent_166"

def title_of(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""

def err_of(html: str) -> str:
    """The error page's heading + detail, flattened."""
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:220]

# name -> (method path, data, files)
CASES = [
    ("assert",        f"/cases/{C166}/assert",        {"criterion_id": "no_such_criterion", "value": "yes", "note": ""}, None),
    ("assert/bulk",   f"/cases/{C166}/assert/bulk",   {}, None),
    ("proposals",     f"/cases/{C166}/proposals/art_bogus", {"decision": "confirmed"}, None),
    ("fixes",         f"/cases/{C166}/fixes",         {}, None),
    ("submitted",     f"/cases/{C164}/submitted",     {"on": ""}, None),
    ("letter",        f"/cases/{C164}/letter",        {}, {"letter": ("junk.txt", b"not a letter", "text/plain")}),
    ("decision",      f"/cases/{C164}/decision",      {"outcome": "", "decided_on": "", "reason": ""}, None),
    ("resubmit",      f"/cases/{C166}/resubmit",      {"reason_key": ""}, None),
    ("ask/done",      f"/cases/{C166}/ask/done",      {}, None),
    ("booked",        f"/cases/{C166}/booked",        {"on": ""}, None),
    ("capture",       f"/cases/{C166}/capture",       {"requirement_id": "bogus_req", "back": ""}, None),
    ("undo",          f"/cases/{C166}/undo",          {"step": "no_such_step"}, None),
    ("narrative",     f"/cases/{C164}/narrative",     {"narrative": "roles-lane probe, should be refused"}, None),
    ("sign-off",      f"/cases/{C166}/sign-off",      {"narrative": "roles-lane probe"}, None),
    ("recover/{id}",  "/recover/row_bogus",           {"status": "called", "note": ""}, None),
    ("rules/check",   "/rules/check",                 {}, None),
    ("rules/use",     "/rules/use",                   {"draft": "bogus", "draft_sha": "bogus"}, None),
    ("test-skip",     f"/cases/{C166}/test-skip",     {}, None),
    ("test-restore",  f"/cases/{C166}/test-restore",  {}, None),
    ("actor",         "/actor",                       {"actor": "dentist"}, None),
]

rows = []
for role in ("coordinator", "dentist"):
    for name, path, data, files in CASES:
        with httpx.Client(base_url=BASE, timeout=90, follow_redirects=False,
                          cookies={"actor": role}) as c:
            try:
                r = c.post(path, data=data, files=files)
            except Exception as e:
                rows.append({"role": role, "endpoint": name, "status": "EXC", "detail": repr(e)})
                continue
        loc = r.headers.get("location", "")
        detail = loc if r.status_code in (302, 303) else err_of(r.text)
        rows.append({"role": role, "endpoint": name, "status": r.status_code,
                     "title": title_of(r.text) if r.status_code >= 400 else "",
                     "detail": detail})
        print(f"{role:12} {name:16} {r.status_code}  {detail[:130]}")

json.dump(rows, open("var/e2e/roles/matrix.json", "w"), indent=1)
