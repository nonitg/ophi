"""Read Sun Life's decision out of its letter, or out of the note text on an electronic answer.

Gemini reads the letter (PDF or phone photo) and names the outcome, the date, Sun Life's reason word for word, and
which of the rule pack's denial reasons it is. Staff confirm before anything is recorded. Laya is not used here: it
was trained to predict a reason from the chart, not to read letters.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import date
from typing import Literal

from pydantic import BaseModel

from ophi.workflow import REASONS

# An alias, not a pinned name: Google retires pinned models (gemini-2.5-pro went 404 mid-2026) and a retired
# model means no letter can be read until someone edits this file. Flash, not pro: the pro alias resolves to a model
# the free tier can't call at all (every read came back 429). Free tier allows 20 flash reads a day -- scripts/
# gemini-quota-check.py names the exhausted quota when reads start failing.
MODEL = "gemini-flash-latest"
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
# The free tier's 20 reads a day, spent. Waiting inside the request won't clear it, so say so and let staff move on.
DAILY_CAP = "Gemini's reads for today are used up. Pick the reason yourself, or try again tomorrow."


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


_client = None


def _gemini_client():
    """One client for the process. A throwaway `genai.Client()` is collected mid-call and its __del__ closes the
    httpx client underneath the request, which surfaces as "Cannot send a request, as the client has been closed"."""
    global _client
    from google import genai
    if _client is None:
        _client = genai.Client()
    return _client


# A burst throttle clears in a second or two and is worth waiting out; the free tier's daily cap is not, and
# retrying it only spends what quota is left. Gemini says which through RetryInfo and QuotaFailure, so honour that.
RETRY_UNDER_SECONDS = 5.0
RETRIES = 2


def _error_details(err) -> list[dict]:
    return (err.details or {}).get("error", {}).get("details", []) if isinstance(err.details, dict) else []


def _daily_cap(err) -> bool:
    """Whether the 429 is the per-day request cap, which no amount of waiting inside one request will clear."""
    return any(v.get("quotaId", "").startswith("GenerateRequestsPerDay")
               for d in _error_details(err) if d.get("@type", "").endswith("QuotaFailure")
               for v in d.get("violations", []))


def _retry_after(err) -> float | None:
    """How long to wait before trying again, when waiting is worth it. None when it isn't."""
    if _daily_cap(err):
        return None
    for d in _error_details(err):
        if d.get("@type", "").endswith("RetryInfo") and (delay := str(d.get("retryDelay", ""))).endswith("s"):
            try:
                return float(delay[:-1])
            except ValueError:
                return None
    return 1.0  # throttled without a delay named: one short wait is still worth a try


def _call(contents, config):
    """One read, waiting out a short throttle. A daily cap or a long delay comes straight back to the desk."""
    from google.genai import errors

    for attempt in range(RETRIES + 1):
        try:
            return _gemini_client().models.generate_content(model=MODEL, contents=contents, config=config)
        except (errors.ClientError, errors.ServerError) as e:
            wait = _retry_after(e) if e.code in (429, 500, 502, 503, 504) else None
            if wait is None or wait > RETRY_UNDER_SECONDS or attempt == RETRIES:
                raise
            time.sleep(wait)


def gemini_reader(parts: list[Part]) -> LetterReading:
    import httpx
    from google.genai import errors, types

    contents = [p if isinstance(p, str) else types.Part.from_bytes(data=p[0], mime_type=p[1]) for p in parts]
    config = types.GenerateContentConfig(system_instruction=SYSTEM, response_mime_type="application/json",
                                         response_schema=LetterReading)
    try:
        res = _call(contents, config)
    except ValueError as e:  # the SDK found no key at all
        raise LetterError(NO_KEY) from e
    except errors.ClientError as e:
        if e.code in (401, 403):
            raise LetterError(NO_KEY) from e
        if e.code == 429 and _daily_cap(e):
            raise LetterError(DAILY_CAP) from e
        raise LetterError(f"Gemini couldn't read the letter ({e.code}). Try again, or record the decision by hand.") from e
    except errors.ServerError as e:
        raise LetterError(f"Gemini couldn't read the letter ({e.code}). Try again, or record the decision by hand.") from e
    except httpx.HTTPError as e:
        raise LetterError("Ophi couldn't reach Gemini. Check the connection and try again.") from e
    except Exception as e:  # never a 500 on the desk: staff can still record the decision by hand
        raise LetterError(f"Gemini couldn't read the letter ({type(e).__name__}). Record the decision by hand.") from e
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
