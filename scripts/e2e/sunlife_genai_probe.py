"""Narrow the letter-reading 500: is it google-genai 2.25.0's client, or the environment?"""
from __future__ import annotations

import os
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import httpx
from google import genai

c = genai.Client()
api = c._api_client
hc = getattr(api, "_httpx_client", None)
print("httpx client:", type(hc).__name__, "is_closed =", getattr(hc, "is_closed", "?"))

t0 = time.time()
try:
    r = c.models.generate_content(model="gemini-2.5-pro", contents="Reply with the single word OK.")
    print("plain text call:", round(time.time() - t0, 1), "s ->", (r.text or "")[:40])
except Exception as e:
    print("plain text call:", round(time.time() - t0, 1), "s ->", type(e).__name__, e)

# does a hand-rolled httpx request to the same host work at all from here?
t0 = time.time()
try:
    resp = httpx.get("https://generativelanguage.googleapis.com/v1beta/models",
                     headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, timeout=30)
    print("raw httpx:", round(time.time() - t0, 1), "s ->", resp.status_code, len(resp.text))
except Exception as e:
    print("raw httpx:", round(time.time() - t0, 1), "s ->", type(e).__name__, e)
