"""Probe case state for the roles lane: what stage the assigned cases are on."""
import json, re, sys
import httpx

BASE = "http://127.0.0.1:8765"
for cid in ("abeldent_164", "abeldent_166"):
    r = httpx.get(f"{BASE}/api/cases/{cid}/assessment.json", timeout=60)
    print(cid, r.status_code)
    if r.status_code == 200:
        a = r.json()
        print("  verdict:", a.get("verdict"), "assessment_id:", a.get("assessment_id"))
    p = httpx.get(f"{BASE}/cases/{cid}", timeout=60)
    print("  case page:", p.status_code, len(p.text))
    t = re.sub(r"<[^>]+>", " ", p.text)
    t = re.sub(r"\s+", " ", t)
    print("  title:", re.search(r"<title>(.*?)</title>", p.text, re.S).group(1).strip() if "<title>" in p.text else "?")
    # forms present on the page
    for m in re.finditer(r'<form[^>]*action="([^"]*)"[^>]*>', p.text):
        print("   form:", m.group(1))
