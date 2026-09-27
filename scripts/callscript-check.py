"""Draft a real call script with Gemini for one row of the Past denials list, and show what the independent
verifier made of it. One model call per run: the free tier allows 20 a day (see ophi/letters.py)."""

from __future__ import annotations

import sys

from dotenv import load_dotenv

from ophi.callscript import draft_call_script, facts
from ophi.letters import LetterError
from ophi.service import CaseService


def main() -> int:
    load_dotenv()
    svc = CaseService()
    rows = svc.recover_rows()
    if not rows:
        print("No past denials are waiting on a call.")
        return 1
    row = max(rows, key=lambda x: x["row"].fee_dollars)["row"]
    clinic = svc.clinic_name()
    print(f"{row.patient_label}  #{row.tooth_fdi}  ${row.fee_dollars:,.2f}  sent {row.submitted_on}")
    print(f"\n--- what the model is given ---\n{facts(row, clinic)}")
    try:
        script = draft_call_script(row, clinic)
    except LetterError as e:
        print(f"\nno draft: {e}")
        return 1
    print(f"\n--- the draft ---\n{script.text}")
    print(f"\n--- checks ---\n{', '.join(k for k, ok in script.report.checks.items() if ok)}: passed")
    assert row.patient_name.split()[0] not in script.text, "the draft used the patient's name"
    return 0


if __name__ == "__main__":
    sys.exit(main())
