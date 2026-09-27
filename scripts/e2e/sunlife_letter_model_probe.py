"""Confirm the letter-reading failure is the retired model id, not the letter or the key.
Read-only: patches ophi.letters.MODEL in this process only, never on disk."""
from __future__ import annotations

import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from ophi import letters  # noqa: E402

letters.MODEL = sys.argv[1] if len(sys.argv) > 1 else "gemini-3.1-pro-preview"
print("model:", letters.MODEL)
pdf = (ROOT / "var/e2e/sunlife/sunlife-denial.pdf").read_bytes()
for tag, data, mt in [("valid_pdf", pdf, "application/pdf"),
                      ("empty_pdf", b"", "application/pdf"),
                      ("png_not_letter", (ROOT / "var/e2e/sunlife/not-a-letter.png").read_bytes(), "image/png")]:
    t0 = time.time()
    try:
        print(f"{tag}: {round(time.time()-t0,1)}s ->", letters.read_letter(data, mt))
    except Exception as e:
        print(f"{tag}: {round(time.time()-t0,1)}s -> {type(e).__name__}: {e}")
