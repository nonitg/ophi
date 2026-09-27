"""Read Sun Life's decision out of its letter, or out of the note text on an electronic answer.

Gemini reads the letter (PDF or phone photo) and names the outcome, the date, Sun Life's reason word for word, and
which of the rule pack's denial reasons it is. Staff confirm before anything is recorded. Laya is not used here: it
was trained to predict a reason from the chart, not to read letters.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Literal

from pydantic import BaseModel

from ophi.workflow import REASONS

MODEL = "gemini-2.5-pro"
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

NO_KEY = "Ophi can't reach Gemini: set GEMINI_API_KEY for the server."
UNREADABLE = "Gemini couldn't read the letter. Record the decision by hand."


class LetterReading(BaseModel):
    outcome: Literal["approved", "denied", "unclear"]
    decided_on: date | None = None
    reason: str | None = None
    reason_key: ReasonKey | None = None
    carrier_ref: str | None = None


class LetterError(Exception):
    """The letter couldn't be read; the message is fit to show staff."""


Part = tuple[bytes, str] | str  # an uploaded file as (bytes, media type), or prompt text
Reader = Callable[[list[Part]], LetterReading]


def gemini_reader(parts: list[Part]) -> LetterReading:
    import httpx
    from google import genai
    from google.genai import errors, types

    contents = [p if isinstance(p, str) else types.Part.from_bytes(data=p[0], mime_type=p[1]) for p in parts]
    config = types.GenerateContentConfig(system_instruction=SYSTEM, response_mime_type="application/json",
                                         response_schema=LetterReading)
    try:
        res = genai.Client().models.generate_content(model=MODEL, contents=contents, config=config)
    except ValueError as e:  # the SDK found no key at all
        raise LetterError(NO_KEY) from e
    except errors.ClientError as e:
        if e.code in (401, 403):
            raise LetterError(NO_KEY) from e
        raise LetterError(f"Gemini couldn't read the letter ({e.code}). Try again, or record the decision by hand.") from e
    except errors.ServerError as e:
        raise LetterError(f"Gemini couldn't read the letter ({e.code}). Try again, or record the decision by hand.") from e
    except httpx.HTTPError as e:
        raise LetterError("Ophi couldn't reach Gemini. Check the connection and try again.") from e
    if not isinstance(res.parsed, LetterReading):  # refused, blocked, or answered with something else
        raise LetterError(UNREADABLE)
    return res.parsed


def read_letter(data: bytes, media_type: str, reader: Reader = gemini_reader) -> LetterReading:
    """A letter file as staff uploaded it: a PDF, or a photo of the page."""
    if media_type not in MEDIA_TYPES:
        raise LetterError("Upload the letter as a PDF or a photo (PNG or JPEG).")
    return reader([(data, media_type), "Read this letter."])


def read_note(text: str, reader: Reader = gemini_reader) -> LetterReading:
    """Sun Life's note text from an electronic answer, already in the PMS."""
    return reader([f"Read this explanation-of-benefits note:\n\n{text}"])
