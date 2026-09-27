#!/usr/bin/env python
"""The free-offer walkthrough end to end: a denial letter in, what went wrong out, the row kept for training.

Runs the whole chain on a throwaway Postgres so it can be checked without touching Supabase:
  letter text -> letters.read_note -> reason_key -> denial_map -> the criteria the packet fell short of
  -> outcomes.submission/decision/requirement_result -> the resubmission that turned it around.

Gemini reads the letter only with --gemini (it costs quota); by default a stub stands in for the reader so the
rest of the chain can be checked on every run.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from ophi import letters
from ophi.casegen.dsl import build_case
from ophi.engine.assess import assess
from ophi.outcomes import store
from ophi.outcomes.from_live import attempt_id, save_attempt
from ophi.outcomes.why_denied import changes_between, explain_denial
from ophi.rules.loader import pack_for
from tests import _pg
from tests._cases import ready_dict

LETTER = ("Sun Life Assurance Company of Canada. Predetermination 27211, tooth 46. We are unable to process this "
          "request as submitted. A current periapical radiograph of the tooth was not received with the request.")
SENT_ON, DECIDED_ON = date(2026, 9, 17), date(2026, 9, 22)


def stub_reader(parts):
    return letters.LetterReading(outcome="denied", decided_on=DECIDED_ON, reason=LETTER.split(". ", 2)[-1],
                                 reason_key="missing_radiograph", carrier_ref="SL-88213")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gemini", action="store_true", help="let Gemini read the letter (uses daily quota)")
    args = ap.parse_args()
    load_dotenv()  # GEMINI_API_KEY, as the app reads it; the value never reaches this script's output

    print("1. The letter staff dropped in\n   " + LETTER + "\n")

    reading = letters.read_note(LETTER) if args.gemini else letters.read_note(LETTER, reader=stub_reader)
    print(f"2. Read by {'Gemini' if args.gemini else 'a stub'}: {reading.outcome} on {reading.decided_on}, "
          f"reason_key={reading.reason_key!r}\n   Sun Life's words: “{reading.reason}”\n")

    denied = ready_dict() | {"radiographs": []}  # the request as it went out: no film attached
    case = build_case(denied, "walkthrough")
    pack = pack_for(case)
    a = assess(case, pack)

    r = explain_denial(a, reading.reason_key, pack)
    print(f"3. What went wrong (pack {pack.version})")
    if r.unexplained:
        print("   The letter named no reason Ophi can attribute to a criterion.")
    for c in r.criteria:
        print(f"   {'SHORT   ' if c.short else 'was met '} {c.requirement_id:22} {c.label} — {c.status.value}")
    print("   " + ("PACK BLIND SPOT: Sun Life denied on criteria Ophi had read as met.\n"
                   if r.blind_spot else "Ophi had flagged this before it went out.\n"))

    name, url = _pg.start()
    try:
        with store.connect(url) as conn:
            store.migrate(conn)
            save_attempt(conn, case, a, attempt_id("walkthrough", 1), SENT_ON, "denied", reading.reason_key)

            fixed = ready_dict()  # staff took the film; the same case goes again
            case2 = build_case(fixed, "walkthrough")
            a2 = assess(case2, pack)
            save_attempt(conn, case2, a2, attempt_id("walkthrough", 2), date(2026, 9, 24), "approved", None)

            print("4. Kept for training")
            for row in conn.execute(
                    "select s.preauth_id, s.channel, s.verdict, d.status, d.reason_code from outcomes.submission s "
                    "join outcomes.decision d using (preauth_id) where s.preauth_id like 'walkthrough#%' order by 1"):
                print(f"   {row[0]:15} channel={row[1]:5} verdict={row[2]:16} {row[3]}  {row[4] or '-'}")

            print("\n5. Why the second one went differently")
            for c in changes_between(a, a2):
                print(f"   {'FIXED' if c.fixed else '     '} {c.requirement_id:22} {c.before.value} -> {c.after.value}")
    finally:
        _pg.stop(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
