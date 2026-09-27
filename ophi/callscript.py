"""Draft what to say when calling a patient whose crown was denied and never resent.

The slow part of working the Past denials list is not dialling -- it is reconstructing, from "Denied as per
the plan criteria" and a chart nobody has opened in eight months, why a crown the patient was promised never
happened. Gemini drafts those few sentences; a person reads them and makes the call. Ophi never dials.

The model is given initials, never a name: it drafts for "L.F." and staff say "Leila" out loud. Every draft
goes through `ophi.verify.callscript`, which shares no code with this module; a draft that fails verification
is never shown, because a staffer reading an ungrounded sentence to a patient is the whole risk here.
"""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel

from ophi.letters import MODEL, LetterError
from ophi.lookback import LookBackRow
from ophi.verify.callscript import MAX_WORDS, ScriptReport, verify_script

SYSTEM = f"""You draft a short telephone script for a Canadian dental clinic's office manager, who will read it
aloud when calling a patient. The patient was told they needed a crown; the clinic asked the Canadian Dental Care
Plan (via Sun Life) to authorise it in advance; the request came back denied; nobody ever sent it again. The
clinic is calling to pick that back up.

Rules, all of them hard:
- Under {MAX_WORDS} words. Plain spoken English, warm and direct, no jargon, no bullet points.
- Refer to the patient by the initials you are given. Never invent a name for anyone: not the patient, not a
  dentist, not a staff member.
- Say only what the facts below state. Never mention a tooth, a date, or a missing document that is not listed.
- Never say a request was or will be approved, eligible, covered, or likely. Never mention a price, a fee, an
  amount, or what anyone will or will not pay.
- Do not offer a specific appointment time. Ask the patient to call the clinic back.
- Open by naming the clinic so the patient knows who is calling.
- Say plainly what is unfinished and what the clinic needs from them, then ask them to call back.

Write only the script itself, with no heading, preamble, or stage directions."""

NO_KEY = "Ophi can't reach Gemini: set GEMINI_API_KEY for the server."
UNSAFE = "Gemini's draft didn't hold up against the chart. Write the call notes by hand."

Drafter = Callable[[str], str]


class CallScript(BaseModel):
    """A draft and the verdict of the independent check, shown together: staff see what was checked."""

    text: str
    report: ScriptReport


def facts(row: LookBackRow, clinic: str) -> str:
    """The only facts the model may use. Initials, never the patient's name."""
    lines = [
        f"Clinic name: {clinic}",
        f"Patient initials: {row.patient_label}",
        f"Tooth: #{row.tooth_fdi}",
        f"The request was sent to Sun Life on: {row.submitted_on.isoformat()}",
        f"Sun Life's answer: denied. Their words, which may be uninformative: \"{row.denial_text or 'no reason given'}\"",
    ]
    if row.gaps:
        lines.append("What the chart was missing on the day it was sent, and what the clinic now needs from the "
                     f"patient: {'; '.join(row.gaps)}")
    else:
        lines.append("No missing document was found in the chart. The clinic needs to review the file with the "
                     "patient before sending it again; do not name any specific missing document.")
    return "\n".join(lines)


def gemini_drafter(prompt: str) -> str:
    from google.genai import types

    from ophi.letters import _gemini_client

    config = types.GenerateContentConfig(system_instruction=SYSTEM, temperature=0.4)
    try:
        res = _gemini_client().models.generate_content(model=MODEL, contents=[prompt], config=config)
    except ValueError as e:  # the SDK found no key at all
        raise LetterError(NO_KEY) from e
    except Exception as e:  # never a 500 on the desk: staff can always write the call notes themselves
        raise LetterError(f"Gemini couldn't draft the call ({type(e).__name__}). Write the call notes by hand.") from e
    return (res.text or "").strip()


def draft_call_script(row: LookBackRow, clinic: str, drafter: Drafter = gemini_drafter,
                      attempts: int = 2) -> CallScript:
    """Draft, verify, and re-ask once with the findings when the draft doesn't hold up.

    Raises `LetterError` when no attempt verifies: no draft is better than one a staffer reads out and has to
    walk back. Staff can still write their own notes.
    """
    prompt, last = facts(row, clinic), None
    for _ in range(attempts):
        text = drafter(prompt)
        report = verify_script(text, row, clinic)
        if report.ok:
            return CallScript(text=text, report=report)
        last = report
        prompt = (f"{facts(row, clinic)}\n\nYour previous draft was rejected for these reasons. Fix every one of "
                  f"them and write the script again:\n- " + "\n- ".join(report.findings))
    raise LetterError(f"{UNSAFE} ({'; '.join(last.findings) if last else 'no draft'})")
