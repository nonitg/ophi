"""The fix plan scored live: Laya and LightGBM run on the chart as it stands each time a case page opens.

Replaces the offline readouts (cases/demo/laya) in the running app, so a new case or a PMS change is scored
the moment it's opened. The models load once per process; the board reuses the latest live plan per chart.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

from ophi.cdm.models import Case
from ophi.outcomes.case_export import to_export
from ophi.outcomes.fixer import plan_fixes
from ophi.outcomes.readout import Readout, ScoredPlan, fingerprint, text_for
from ophi.rules.schema import RulePack

log = logging.getLogger("uvicorn.error")


class LiveScorer:
    def __init__(self, pack_for: Callable[[Case], RulePack], model=None):
        """`pack_for` gives each request the pack for its date (CaseService.pack_for)."""
        self.pack_for, self._model = pack_for, model
        self._lock = threading.Lock()  # one GPU, one forward pass at a time
        self._latest: dict[str, Readout] = {}  # case id -> last live plan, for the board
        self.clinic_rate: Callable[[Case], float | None] | None = None  # the clinic's past denials, when the app has them

    def warm(self) -> None:
        with self._lock:
            self._load()

    def _load(self):
        if self._model is None:
            import torch

            from ophi.outcomes.risk import RiskModel

            t = time.perf_counter()
            self._model = RiskModel.load()
            device = "cuda" if torch.cuda.is_available() else "cpu"
            log.info(f"ML Laya + LightGBM loaded on {device} in {time.perf_counter() - t:.1f}s")
            if device == "cpu":
                log.warning("ML no GPU: each live plan takes about 40s on CPU")
        return self._model

    def score(self, case: Case) -> Readout:
        """Run both models on the case now."""
        rate = self.clinic_rate(case) if self.clinic_rate else None
        with self._lock:
            model = self._load()
            t = time.perf_counter()
            plan = plan_fixes(to_export(case), case.as_of, self.pack_for(case), model, clinic_denial_rate=rate, request_id=case.case_id)
            log.info(f"ML ran Laya + LightGBM live for {case.case_id} in {1000 * (time.perf_counter() - t):.0f}ms")
        rd = Readout(case_id=case.case_id, scored_on=case.as_of,
                     plans=[ScoredPlan(state="live", text_sha256=fingerprint(text_for(case)), plan=plan.model_dump(mode="json"))])
        self._latest[case.case_id] = rd
        return rd

    def cached(self, case: Case) -> Readout | None:
        """The last live plan if the chart hasn't changed since; never scores."""
        rd = self._latest.get(case.case_id)
        return rd if rd and rd.matching(case) else None

    def latest(self, case: Case) -> Readout:
        """The last live plan if the chart hasn't changed since; otherwise score it now."""
        return self.cached(case) or self.score(case)
