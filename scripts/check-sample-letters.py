"""Read every sample letter in fixtures/letters/ with the real reader and check what it found.

Guards the letter-upload demo: if a regenerated letter stops saying what it used to, or the prompt drifts, this
fails before staff see it. Needs GEMINI_API_KEY (it calls Gemini, one request per letter).
Run: .venv/bin/python scripts/check-sample-letters.py
"""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ophi import letters

OUT = Path(__file__).resolve().parent.parent / "fixtures" / "letters"
MEDIA = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}

# name -> (outcome, decided_on, reason_key, carrier_ref); None means "don't care"
EXPECT = {
    "cherski-approved":           ("approved", "2026-09-17", None, "SL260915000160"),
    "cherski-denied-ferrule":     ("denied", "2026-09-17", "insufficient_ferrule", "SL260915000160"),
    "cherski-denied-vague":       ("denied", "2026-09-17", None, "SL260915000160"),
    "cherski-denied-perio":       ("denied", "2026-09-17", "missing_perio_chart", "SL260915000160"),
    "goertsen-approved":          ("approved", "2026-09-25", None, "SL260922000164"),
    "goertsen-denied-radiograph": ("denied", "2026-09-25", "missing_radiograph", "SL260922000164"),
    "goertsen-denied-notes":      ("denied", "2026-09-25", "insufficient_notes", "SL260922000164"),
    # Decides nothing, so the date it carries is the letter's, not a decision's: don't pin it.
    "goertsen-acknowledgement":   ("unclear", None, None, "SL260922000164"),
}

FIELDS = ("outcome", "decided_on", "reason_key", "carrier_ref")


def read(path: Path):
    return letters.read_letter(path.read_bytes(), MEDIA[path.suffix])


def main() -> int:
    paths = sorted(p for p in OUT.iterdir() if p.suffix in MEDIA)
    missing = sorted(set(EXPECT) - {p.stem for p in paths})
    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            readings = list(pool.map(read, paths))
    except letters.LetterError as e:
        print(f"can't read the letters: {e}")
        return 2

    bad = list(missing)
    for path, got in zip(paths, readings):
        want = EXPECT.get(path.stem)
        if want is None:
            print(f"?  {path.name}: no expectation ({got.outcome}, {got.decided_on}, {got.reason_key})")
            continue
        wrong = [f"{f}: want {w}, got {g}" for f, w, g in
                 ((f, w, getattr(got, f)) for f, w in zip(FIELDS, want))
                 if w is not None and str(g) != w]
        print(f"{'FAIL' if wrong else 'ok  '} {path.name}: {got.outcome} {got.decided_on} {got.reason_key}")
        for w in wrong:
            print(f"       {w}")
        if wrong:
            bad.append(path.stem)
    for m in missing:
        print(f"FAIL {m}: expected but not generated")
    print(f"\n{len(paths) - len(bad)}/{len(EXPECT)} letters read as expected")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
