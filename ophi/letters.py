"""Read Sun Life's decision out of its letter, or out of the note text on an electronic answer.

Claude reads the letter (PDF or phone photo) and names the outcome, the date, Sun Life's reason word for word, and
which of the rule pack's denial reasons it is. Staff confirm before anything is recorded. Laya is not used here: it
was trained to predict a reason from the chart, not to read letters.
"""

from __future__ import annotations

import base64
from collections.abc import Callable
from datetime import date
from typing import Literal

from pydantic import BaseModel

from ophi.workflow import REASONS

MODEL = "claude-opus-5"
IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MEDIA_TYPES = {"application/pdf", *IMAGE_TYPES}

ReasonKey = Literal[tuple(REASONS)]  # type: ignore[valid-type]

SYSTEM = f"""You read decision letters and explanations of benefits that Sun Life sends a dental clinic about a
Canadian Dental Care Plan crown preauthorization (predetermination). Report only what the document says.
- outcome: approved, denied, or unclear when the document doesn't say.
- decided_on: the date on the decision, as YYYY-MM-DD, or null.
- reason: Sun Life's own words explaining a denial, copied exactly, or null.
- reason_key: the one reason below that Sun Life's words name, or null when the letter gives no specific reason
  (for example "as per the plan criteria"). Never guess a reason the letter doesn't state.
- carrier_ref: Sun Life's reference or claim number for the request, or null.
Reasons: {"; ".join(f"{k} = {v[0]}" for k, v in REASONS.items())}."""


class LetterReading(BaseModel):
    outcome: Literal["approved", "denied", "unclear"]
    decided_on: date | None = None
    reason: str | None = None
    reason_key: ReasonKey | None = None
    carrier_ref: str | None = None


class LetterError(Exception):
    """The letter couldn't be read; the message is fit to show staff."""


Reader = Callable[[list[dict]], LetterReading]  # user content blocks -> reading


def claude_reader(content: list[dict]) -> LetterReading:
    import anthropic

    try:
        res = anthropic.Anthropic().messages.parse(model=MODEL, max_tokens=16000, system=SYSTEM,
                                                   messages=[{"role": "user", "content": content}],
                                                   output_format=LetterReading)
    except anthropic.AuthenticationError as e:
        raise LetterError("Ophi can't reach Claude: set ANTHROPIC_API_KEY for the server.") from e
    except anthropic.APIConnectionError as e:
        raise LetterError("Ophi couldn't reach Claude. Check the connection and try again.") from e
    except anthropic.APIStatusError as e:
        raise LetterError(f"Claude couldn't read the letter ({e.status_code}). Try again, or record the decision by hand.") from e
    except TypeError as e:  # the SDK found no credentials at all
        raise LetterError("Ophi can't reach Claude: set ANTHROPIC_API_KEY for the server.") from e
    if res.stop_reason == "refusal" or res.parsed_output is None:
        raise LetterError("Claude couldn't read the letter. Record the decision by hand.")
    return res.parsed_output


def read_letter(data: bytes, media_type: str, reader: Reader = claude_reader) -> LetterReading:
    """A letter file as staff uploaded it: a PDF, or a photo of the page."""
    if media_type not in MEDIA_TYPES:
        raise LetterError("Upload the letter as a PDF or a photo (PNG or JPEG).")
    source = {"type": "base64", "media_type": media_type, "data": base64.standard_b64encode(data).decode()}
    block = {"type": "image" if media_type in IMAGE_TYPES else "document", "source": source}
    return reader([block, {"type": "text", "text": "Read this letter."}])


def read_note(text: str, reader: Reader = claude_reader) -> LetterReading:
    """Sun Life's note text from an electronic answer, already in the PMS."""
    return reader([{"type": "text", "text": f"Read this explanation-of-benefits note:\n\n{text}"}])
