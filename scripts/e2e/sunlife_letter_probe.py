"""Out-of-band probe: does ophi.letters read the test letter at all, and how long does Gemini take?"""
from __future__ import annotations

import os
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
for line in (ROOT / ".env").read_text().splitlines():  # same keys the server loads
    if "=" in line and not line.strip().startswith("#"):
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from ophi import letters  # noqa: E402

print("GEMINI_API_KEY set:", bool(os.environ.get("GEMINI_API_KEY")))
pdf = (ROOT / "var/e2e/sunlife/sunlife-denial.pdf").read_bytes()

for tag, data, mt in [("valid_pdf", pdf, "application/pdf"),
                      ("valid_pdf_again", pdf, "application/pdf"),
                      ("empty_pdf", b"", "application/pdf"),
                      ("png_not_letter", (ROOT / "var/e2e/sunlife/not-a-letter.png").read_bytes(), "image/png")]:
    t0 = time.time()
    try:
        r = letters.read_letter(data, mt)
        print(f"{tag}: {round(time.time()-t0,1)}s -> {r}")
    except Exception as e:
        print(f"{tag}: {round(time.time()-t0,1)}s -> {type(e).__name__}: {e}")

note = ("Predetermination not approved. A current periapical radiograph of tooth 24 was not received. "
        "Resubmit with the radiograph.")
t0 = time.time()
try:
    print("read_note:", round(time.time()-t0, 1), letters.read_note(note))
except Exception as e:
    print("read_note:", round(time.time()-t0, 1), type(e).__name__, e)
