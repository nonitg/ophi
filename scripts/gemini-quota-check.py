"""Why is Gemini answering 429? Names the exhausted quota and the retry delay.

Identifies the key by fingerprint only -- the key itself never leaves the server.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import httpx  # noqa: E402

from ophi.letters import MODEL  # noqa: E402
MODEL = os.environ.get("QUOTA_CHECK_MODEL", MODEL)

key = os.environ.get("GEMINI_API_KEY", "")
print("key fingerprint:", f"...{key[-4:]} sha256:{hashlib.sha256(key.encode()).hexdigest()[:12]}" if key else "NOT SET")

r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
               headers={"x-goog-api-key": key},
               json={"contents": [{"parts": [{"text": "Reply with the single word OK."}]}]}, timeout=60)
print("status:", r.status_code)
if r.status_code != 200:
    err = r.json().get("error", {})
    print("message:", err.get("message"))
    for d in err.get("details", []):
        t = d.get("@type", "")
        if t.endswith("QuotaFailure"):
            for v in d.get("violations", []):
                print("  quota:", v.get("quotaId"), "limit", v.get("quotaValue"),
                      json.dumps(v.get("quotaDimensions", {})))
        elif t.endswith("RetryInfo"):
            print("  retry after:", d.get("retryDelay"))
