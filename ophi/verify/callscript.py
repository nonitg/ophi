"""Independent verifier for a drafted call script.

A staffer reads this script aloud to a patient whose crown was denied and never resent. The risk is not
telephony -- a person dials -- it is that a model puts a sentence in a staffer's mouth that the chart does
not support, or that promises what Sun Life will do. So every clinical token in the script must trace back
to the Look-Back row it was drafted from, and Ophi's copy law applies to speech exactly as it does to a screen.

Deliberately shares no code with the drafter (`ophi.callscript`): a model checking its own output is not
evidence. Verify first, draft second -- if this cannot reject a deliberately bad script, nothing else matters.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

from ophi import copy_law
from ophi.lookback import LookBackRow

# The same copy law the screens are held to, plus the words a model reaches for only out loud. A script
# that passes it is, near enough, not solicitation by construction -- which is the whole compliance argument
# in `docs/voice-followup.md`, so it must be the *shared* rule and never a second copy of it.
COPY_LAW = (copy_law.FORBIDDEN, copy_law.SPOKEN_EXTRA)
# Promising money or a payer outcome. Separate from the copy law because these are how a script sells.
PROMISE = re.compile(r"\b(free of charge|no cost|at no charge|won'?t (?:cost|pay)|reimburse\w*|pays? for|we can get (?:this|it))\b", re.I)
TOOTH = re.compile(r"#\s*(\d{1,2})|\btooth\s+(?:number\s+)?(\d{1,2})\b", re.I)
MONEY = re.compile(r"\$\s?([\d,]+(?:\.\d{2})?)")
DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
# A drafter is handed initials, never a name. A full name in the output means the model invented one.
FULL_NAME = re.compile(r"\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b")

MAX_WORDS = 220  # a phone script, not a letter; nobody reads past this and a long draft hides its claims

# Clinical nouns a script may only use when the row actually names that gap.
GAP_WORDS = {
    "radiograph": ("radiograph", "x-ray", "xray", "film", "periapical", "bitewing"),
    "perio": ("periodontal", "perio", "gum measurement", "pocket depth", "charting"),
}


class ScriptReport(BaseModel):
    ok: bool
    findings: list[str]
    checks: dict[str, bool]


def _words(text: str) -> int:
    return len(text.split())


def _teeth(text: str) -> set[int]:
    return {int(a or b) for a, b in TOOTH.findall(text)}


def _money(text: str) -> set[float]:
    return {float(m.replace(",", "")) for m in MONEY.findall(text)}


def _gap_kinds(labels: list[str]) -> set[str]:
    """Which families of clinical evidence the row actually names as missing."""
    joined = " ".join(labels).lower()
    kinds = set()
    for kind, words in GAP_WORDS.items():
        if any(w in joined for w in words):
            kinds.add(kind)
    return kinds


def verify_script(text: str, row: LookBackRow, clinic: str, allow_name: str | None = None) -> ScriptReport:
    """Check one drafted script against the row it was drafted from.

    `allow_name` is the patient's real name when staff have templated it in locally; the drafter never sees it.
    """
    findings: list[str] = []
    checks: dict[str, bool] = {}

    def check(name: str, ok: bool, finding: str) -> None:
        checks[name] = ok
        if not ok:
            findings.append(finding)

    body = text.strip()
    check("not_empty", bool(body), "The script is empty.")
    check("length", _words(body) <= MAX_WORDS, f"The script is {_words(body)} words; the limit is {MAX_WORDS}.")

    hits = sorted({m.group(0) for law in COPY_LAW for m in law.finditer(body)})
    check("copy_law", not hits, f"Says what Sun Life will do: {', '.join(hits)}.")

    promises = sorted({m.group(0) for m in PROMISE.finditer(body)})
    check("no_promise", not promises, f"Promises an outcome or a cost: {', '.join(promises)}.")

    teeth = _teeth(body)
    check("tooth_grounded", teeth <= {row.tooth_fdi},
          f"Names tooth {', '.join(f'#{t}' for t in sorted(teeth - {row.tooth_fdi}))}; the row is #{row.tooth_fdi}.")

    amounts = _money(body)
    check("no_fee_quoted", not amounts,
          f"Quotes a price ({', '.join(f'${a:,.2f}' for a in sorted(amounts))}); a call-back script never does.")

    dates = set(DATE.findall(body))
    allowed_dates = {row.submitted_on.isoformat()}
    check("dates_grounded", dates <= allowed_dates,
          f"Names a date not on the row: {', '.join(sorted(dates - allowed_dates))}.")

    named = _gap_kinds([body]) - _gap_kinds(row.gaps)
    check("gaps_grounded", not named,
          f"Names evidence the row does not record as missing: {', '.join(sorted(named))}.")

    allowed_names = {clinic, "Sun Life", allow_name or ""}
    invented = {n for n in FULL_NAME.findall(body) if n not in allowed_names and n != row.patient_name}
    check("no_invented_name", not invented, f"Uses a name the drafter was never given: {', '.join(sorted(invented))}.")

    check("names_clinic", clinic.lower() in body.lower(), f"Never identifies the caller as {clinic}.")

    return ScriptReport(ok=not findings, findings=findings, checks=checks)
