"""What the outcomes corpus says about the clinic sending a request: its past denial rate, for live scoring.

The nearest-neighbour matcher that put "past requests like this" under a fix step was removed with that panel
(the step stands on its own); git history has it if the corpus is ever read on screen again.
"""

from __future__ import annotations

import logging

from ophi.cdm.models import Case
from ophi.outcomes import past_store
from ophi.outcomes.case_export import to_export
from ophi.outcomes.past_store import Cached

log = logging.getLogger("uvicorn.error")


def clinic_denial_rate(past: Cached, connect, case: Case) -> float | None:
    """The case's clinic's past denial rate for live scoring. The clinic is the sending provider, as in the exports
    training reads; None when it has no past requests on file or the database is unavailable."""
    clinic = to_export(case)["provider"]["provider_id"]
    try:
        if not any(r["clinic_id"] == clinic for r in past.rows()):
            return None
        with connect() as conn:
            return past_store.clinic_denial_rate(conn, clinic, case.as_of)
    except Exception as e:
        log.warning("clinic denial rate unavailable: %s", e)
        return None
