"""Is the letter 500 caused by ophi.letters dropping the genai.Client reference mid-call?"""
from __future__ import annotations

import os
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from google import genai
from google.genai import types

from ophi.letters import SYSTEM, LetterReading

pdf = (ROOT / "var/e2e/sunlife/sunlife-denial.pdf").read_bytes()
contents = [types.Part.from_bytes(data=pdf, mime_type="application/pdf"), "Read this letter."]
cfg = types.GenerateContentConfig(system_instruction=SYSTEM, response_mime_type="application/json",
                                  response_schema=LetterReading)

for tag, model in [("temporary-client", None), ("held-client", None)]:
    for m in ("gemini-2.5-pro", "gemini-3.1-pro-preview"):
        t0 = time.time()
        try:
            if tag == "temporary-client":
                res = genai.Client().models.generate_content(model=m, contents=contents, config=cfg)
            else:
                c = genai.Client()
                res = c.models.generate_content(model=m, contents=contents, config=cfg)
            print(f"{tag} {m}: {round(time.time()-t0,1)}s -> {res.parsed}")
        except Exception as e:
            print(f"{tag} {m}: {round(time.time()-t0,1)}s -> {type(e).__name__}: {str(e)[:200]}")
