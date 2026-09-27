"""Reproduce the 500 on letter upload: does a second Gemini read in one process hit a closed httpx client?

Usage: .venv/bin/python scripts/e2e/lead-letter-probe.py [n]   (n reads, default 3; uses a fictional one-page letter)
"""
import gc
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
for line in (Path(__file__).resolve().parents[2] / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

from ophi import letters  # noqa: E402

LETTER = b"""%PDF-1.4
Sun Life Assurance Company of Canada
Predetermination response - September 17, 2026
Patient: Sumi Yokoyama   Tooth: 24   Procedure: 27211
Decision: Predetermination not approved. A current periapical radiograph of tooth 24 was not provided.
Reference: SL260910000158
"""

n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
for i in range(1, n + 1):
    try:
        r = letters.read_letter(LETTER, "application/pdf")
        print(f"{i}: ok {r.outcome} {r.decided_on} key={r.reason_key}")
    except letters.LetterError as e:
        print(f"{i}: LetterError (handled, staff sees this): {e}")
    except Exception as e:  # what reaches the user as a 500
        print(f"{i}: UNHANDLED {type(e).__name__}: {e}")
    gc.collect()  # a dropped Client closing a shared transport would show up here
