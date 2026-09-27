"""Application layer: cases + human inputs -> assessment. The web app and CLI call this, nothing else.

Human inputs (clinician assertions, confirmations of proposed evidence, sign-off) are stored per case
in a small JSON state store and re-applied on every load, then the deterministic engine re-runs.
The engine never sees the store; it only sees artifacts. What happens after sign-off (sent, Sun Life's
decision, booked) is recorded here too; `ophi.workflow` derives the case's stage from it.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Literal, get_args

from pydantic import BaseModel, Field, model_validator

from ophi import fixes
from ophi.casegen.dsl import CAPTURABLE, capture_artifacts, load_case
from ophi.cdm.models import (
    ArtifactType, AssertionPayload, Case, ChartArtifact, ExtractedDetailPayload, Provenance,
)
from ophi.engine.assess import assess
from ophi.engine.models import Assessment, Verdict
from ophi.extract.proposer import propose_for_case
from ophi.packet.documents import narrative_ascii
from ophi.packet.narrative import validate_narrative
from ophi.outcomes.weights import Weights
from ophi.lookback import LookBackReport, LookBackRow
from ophi.rules.loader import default_pack, pack_for
from ophi.rules.schema import RulePack
from ophi.sources.abeldent import Predetermination
from ophi.sources.fixture_lookback import fixture_lookback
from ophi.workflow import REASONS, Stage, chair_actions, chart_actions, documentation_gaps, stage_of, valid_until, with_ask

ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT / "cases" / "demo"
# Hosted demo points this at a writable scratch dir; the repo checkout may be read-only.
VAR_DIR = Path(os.environ.get("OPHI_VAR_DIR") or ROOT / "var")

# Manual baseline per preauthorization, from docs/research/market.md (25 min per request, ~$26.70/hr
# Ontario treatment coordinator). Shown as an estimate with its source, never as a measured saving.
MANUAL_MINUTES_PER_PREAUTH = 25
COORDINATOR_HOURLY_CAD = 26.70


def _dentist_only(role: str, what: str) -> None:
    if role != "dentist":
        raise PermissionError(f"{what} may only be recorded by the treating dentist (actor role: {role})")


def _not_sent(st: CaseState) -> None:
    if st.sent:
        raise PermissionError("this request is already with Sun Life; start a resubmission to change it")


def _lf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


# Demo seeding replays past steps "as of" their day. The override is per call context, not a swap of the
# shared service's clock, so requests served while a reset reseeds still see the real day.
_STAMP: ContextVar[datetime | None] = ContextVar("ophi_stamp", default=None)


class NarrativeInvalid(ValueError):
    """The rationale text failed the grounding / copy-law validator. Carries the violations."""

    def __init__(self, violations: list[str]) -> None:
        super().__init__("; ".join(violations))
        self.violations = violations


def identity_tokens(case: Case) -> list[str]:
    """Tokens that must never appear in packet filenames or the index (checked by the verifier)."""
    raw = [*case.patient.display_name.replace(",", " ").split(), case.patient.patient_id, case.patient.cdcp_client_id or ""]
    return [t for t in raw if len(t) >= 3]


log = logging.getLogger("uvicorn.error")


class SignOff(BaseModel):
    signed_by: str
    licence: str | None
    signed_at: datetime
    attestation: str
    narrative_sha256: str
    assessment_id: str
    ruleset_version: str


class Decision(BaseModel):
    """Sun Life's answer as staff recorded it. `reason` is Sun Life's wording, verbatim."""

    outcome: Literal["approved", "denied"]
    decided_on: date
    reason: str | None = None
    reason_key: str | None = None  # which of workflow.REASONS Sun Life's words name, as staff confirmed it
    recorded_by: str
    recorded_at: datetime


class Sent(BaseModel):
    """The request as it actually went out: the chart in export shape and Ophi's reading of it, frozen on the
    send date. A case can go to Sun Life any number of times, and each attempt changes the chart, so a training
    row labelled with one attempt's decision has to carry that attempt's chart and not today's."""

    export: dict
    assessment: dict
    # The signature this request went out under, kept here because `start_resubmission` clears the case's
    # sign-off (the dentist attests to each request), so an archived attempt could not otherwise say whether
    # a dentist ever attested to it. An ABELDent-synced send and a signed packet send read the same otherwise.
    sign_off: SignOff | None = None

    @property
    def signed(self) -> bool:
        """Signed for the chart in this snapshot, not merely at some point on this case."""
        return self.sign_off is not None and self.sign_off.assessment_id == self.assessment.get("assessment_id")


class Attempt(BaseModel):
    """An earlier submission of this case, kept when staff start a resubmission."""

    submitted_on: date
    decision: Decision
    sent: Sent | None = None  # absent only on attempts made before snapshots were kept


class Ask(BaseModel):
    """What Sun Life's denial asks for before the request goes again, and the column that does it."""

    reason_key: str
    title: str
    stage: Stage
    since: date
    done_by: str | None = None


class FirstCheck(BaseModel):
    """The documentation gaps Ophi found the first time it read the chart, so a gap staff later close
    still counts as caught before sending."""

    at: datetime
    gaps: list[str]  # requirement ids


class CaseState(BaseModel):
    assertions: dict[str, dict] = Field(default_factory=dict)  # criterion_id -> {value, by, licence, at, note, ophi}
    confirmations: dict[str, dict] = Field(default_factory=dict)  # proposal artifact id -> {decision, by, at}
    narrative_edits: str | None = None
    fixes: dict[str, dict] = Field(default_factory=dict)  # requirement id -> {by, at, title}: Ophi's safe fixes staff applied
    sign_off: SignOff | None = None
    submitted_at: datetime | None = None  # when staff recorded the submission
    submitted_on: date | None = None  # the day it went to Sun Life
    decision: Decision | None = None
    booked_on: date | None = None
    attempts: list[Attempt] = Field(default_factory=list)
    snapshot: Sent | None = None  # the request now with Sun Life, frozen as it was sent
    ask: Ask | None = None
    pms_synced: list[str] = Field(default_factory=list)  # "<claim id>:sent" / ":decision" steps already taken from the PMS
    first_check: FirstCheck | None = None
    test_skips: list[str] = Field(default_factory=list)  # requirement ids a test run treats as fixed
    captures: dict[str, date] = Field(default_factory=dict)  # demo: requirement id -> day the chair gap was taken

    @model_validator(mode="after")
    def _sent_day_from_legacy_state(self) -> CaseState:
        """State saved before the send date was recorded kept only the moment staff clicked."""
        if self.submitted_at and self.submitted_on is None:
            self.submitted_on = self.submitted_at.date()
        return self

    @property
    def sent(self) -> bool:
        """The request is with Sun Life or decided: its chart inputs and signature are part of the record."""
        return self.submitted_on is not None


FollowUpStatus = Literal["left_message", "rebooking", "declined", "reopened"]
# Statuses that mean the clinic is still chasing this patient, so the row wants a date to call back on.
OPEN_FOLLOWUP = ("left_message", "rebooking", "reopened")


class FollowUp(BaseModel):
    """One call staff made on a past denial that was never resubmitted (the Recover list).

    Kept as a history, not a latest-value: three failed attempts to reach a patient and one are different
    facts, and only the history tells staff when to stop chasing."""

    status: FollowUpStatus
    note: str | None = None
    callback_on: date | None = None  # when to try again; without it a call list has no next action and rots
    by: str
    at: datetime


class AuditEvent(BaseModel):
    at: datetime
    case_id: str
    actor: str
    event: str
    detail: str


class Store:
    """JSON-file state store. One file per case plus an append-only audit log."""

    def __init__(self, root: Path = VAR_DIR) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def load(self, case_id: str) -> CaseState:
        p = self.root / f"{case_id}.json"
        return CaseState.model_validate_json(p.read_text()) if p.exists() else CaseState()

    def save(self, case_id: str, st: CaseState) -> None:
        with self._lock:
            (self.root / f"{case_id}.json").write_text(st.model_dump_json(indent=2))

    def record_first_check(self, case_id: str, fc: FirstCheck) -> None:
        """Set the first check if no one has yet, re-reading under the lock so a concurrent write survives."""
        with self._lock:
            st = self.load(case_id)
            if st.first_check is None:
                st.first_check = fc
                (self.root / f"{case_id}.json").write_text(st.model_dump_json(indent=2))

    def load_followup_calls(self) -> dict[str, list[FollowUp]]:
        """Every call made against each row, oldest first. Reads the pre-history format (one call per row) too."""
        p = self.root / "followups.json"
        if not p.exists():
            return {}
        raw = json.loads(p.read_text())
        return {k: [FollowUp.model_validate(c) for c in (v if isinstance(v, list) else [v])] for k, v in raw.items()}

    def load_followups(self) -> dict[str, FollowUp]:
        """The latest call on each row, for screens that show one status."""
        return {k: calls[-1] for k, calls in self.load_followup_calls().items() if calls}

    def add_followup(self, row_id: str, followup: FollowUp) -> None:
        with self._lock:
            calls = self.load_followup_calls()
            calls.setdefault(row_id, []).append(followup)
            (self.root / "followups.json").write_text(
                json.dumps({k: [c.model_dump(mode="json") for c in v] for k, v in calls.items()}, indent=2))

    def audit(self, case_id: str, actor: str, event: str, detail: str, at: datetime | None = None) -> None:
        ev = AuditEvent(at=at or datetime.now(UTC), case_id=case_id, actor=actor, event=event, detail=detail)
        with self._lock:
            with (self.root / "audit.jsonl").open("a") as fh:
                fh.write(ev.model_dump_json() + "\n")

    def audit_log(self, case_id: str | None = None) -> list[AuditEvent]:
        p = self.root / "audit.jsonl"
        if not p.exists():
            return []
        evs = [AuditEvent.model_validate_json(line) for line in p.read_text().splitlines() if line.strip()]
        return [e for e in evs if case_id is None or e.case_id == case_id]

    def reset(self) -> None:
        for p in self.root.glob("*.json"):
            p.unlink()
        (self.root / "audit.jsonl").unlink(missing_ok=True)
        shutil.rmtree(self.root / "packets", ignore_errors=True)


class CaseView(BaseModel):
    """Everything a screen needs for one case."""

    case: Case
    base_case: Case  # without proposals or user inputs, for the evidence panel
    proposals: list[ChartArtifact]
    state: CaseState
    assessment: Assessment
    minutes_estimate: dict
    pms: Predetermination | None = None  # the request as the PMS last showed it, once sent
    pack: RulePack  # the pack in force on this request's date

    @property
    def signed(self) -> bool:
        """Signed for THIS assessment. A chart change produces a new assessment id and voids the sign-off."""
        so = self.state.sign_off
        return so is not None and so.assessment_id == self.assessment.assessment_id

    @property
    def sign_off_stale(self) -> bool:
        return self.state.sign_off is not None and not self.signed

    @property
    def dollars_at_risk(self) -> float:
        return (self.case.treatment.fee_cents or 0) / 100

    @property
    def test_run(self) -> bool:
        """Chart gaps were skipped to try the flow: the packet is incomplete and must never be sent."""
        return self.assessment.test_run

    @property
    def stage(self) -> Stage:
        st = self.state
        s = stage_of(self.assessment, self.signed, st.submitted_on, st.decision.outcome if st.decision else None, st.booked_on)
        return with_ask(s, st.ask.stage if st.ask and not st.ask.done_by else None)


class CaseService:
    def __init__(
        self,
        cases_dir: Path = CASES_DIR,
        store: Store | None = None,
        pack: RulePack | None = None,
        repository=None,
        clock: Callable[[], datetime] | None = None,
        weights: Weights | None = None,
        pms_claims: Callable[[], list[Predetermination]] | None = None,
        note_reader: Callable[[str], str | None] | None = None,
        lookback_report: Callable[[], LookBackReport] | None = None,
        record_outcome: Callable[[str, int, date, str, str | None], None] | None = None,
    ) -> None:
        """`pms_claims` reads the predeterminations the PMS sent; `note_reader` names the REASONS key in Sun Life's
        note text. Both are optional: without them staff record every step by hand. `lookback_report` reads the
        clinic's own past submissions; without it the Look-Back reads the saved ABELDent rows, so the demo and a
        live clinic go down the same path."""
        self.cases_dir = cases_dir
        self.store = store or Store()
        self._pinned = pack  # tests pin one pack; otherwise each request gets the pack for its own date
        self.weights = weights
        self.pms_claims, self.note_reader = pms_claims, note_reader
        self.lookback_report = lookback_report
        # Sun Life's answer to a request Ophi ran, kept for training; without it nothing is learned from it.
        self.record_outcome = record_outcome
        self._pms: dict[str, Predetermination] = {}  # case id -> its predetermination at the last sync
        self.clock = clock or self._chart_clock
        self._chart_day: tuple[date, date] | None = None  # (real day it was computed, chart day)
        # Optional PMS repository abstraction; toggle-aware default.
        if repository is not None:
            self.repository = repository
        else:
            from ophi.sources.pms_repository import (
                AbelDentPmsRepository,
                FileSystemPmsRepository,
                create_auto_repository,
                should_use_abeldent,
                should_use_mocks,
            )

            if should_use_abeldent():
                self.repository = AbelDentPmsRepository()
            elif should_use_mocks():
                self.repository = create_auto_repository()
            else:
                self.repository = FileSystemPmsRepository(cases_dir)

    # --- reads --------------------------------------------------------------------------------

    def case_ids(self) -> list[str]:
        return self.repository.list_case_ids()

    def base_case(self, case_id: str) -> Case:
        return self.repository.get_case(case_id)

    @property
    def pack(self) -> RulePack:
        """The pack in force on the chart's day, for screens not about one request."""
        return self._pinned or default_pack(self.today())

    def pack_for(self, case: Case) -> RulePack:
        return self._pinned or pack_for(case)

    def now(self) -> datetime:
        return _STAMP.get() or self.clock()

    def today(self) -> date:
        return self.now().date()

    @contextmanager
    def at(self, day: date) -> Iterator[None]:
        """Stamp writes as if made on `day` (demo seeding replays past steps through the real calls)."""
        token = _STAMP.set(datetime.combine(day, time(13, 30), UTC))
        try:
            yield
        finally:
            _STAMP.reset(token)

    def _chart_clock(self) -> datetime:
        """Today is the day the chart was read: the latest `as_of` across cases, at the current time of day.
        A live PMS read makes that the real date; the demo fixtures freeze it at 2026-09-17. Re-read once a
        real day, so a long-running server moves forward with the chart."""
        real = datetime.now(UTC)
        if self._chart_day is None or self._chart_day[0] != real.date():
            days = [self.base_case(cid).as_of for cid in self.case_ids()]
            self._chart_day = (real.date(), max(days) if days else real.date())
        return datetime.combine(self._chart_day[1], real.time(), UTC)

    def _built(self, case_id: str, st: CaseState, pack: RulePack | None = None):
        """The chart as staff see it (captures, Ophi's proposals, answers, fixes) and its assessment under `pack`
        (the pack for the request's date by default)."""
        base = self.base_case(case_id)
        base = base.with_artifacts(capture_artifacts(base, st.captures))  # demo captures reach the chart like any film
        proposals = [self._apply_confirmation(p, st) for p in propose_for_case(base)]
        user_assertions = [self._assertion_artifact(base, cid, a) for cid, a in st.assertions.items()]
        pack = pack or self.pack_for(base)
        case = fixes.apply(base, st.fixes, pack).with_artifacts(proposals + user_assertions)
        return base, proposals, case, pack, assess(case, pack, self.weights, frozenset(st.test_skips))

    def assess_under(self, case_id: str, pack: RulePack) -> tuple[Case, Assessment]:
        """The request assessed under another pack (a rule update under review); nothing is recorded."""
        _, _, case, _, a = self._built(case_id, self.store.load(case_id), pack)
        return case, a

    def view(self, case_id: str) -> CaseView:
        st = self.store.load(case_id)
        base, proposals, case, pack, a = self._built(case_id, st)
        if st.first_check is None:
            st.first_check = FirstCheck(at=self.now(), gaps=[r.requirement_id for r in documentation_gaps(a)])
            self.store.record_first_check(case_id, st.first_check)
        return CaseView(case=case, base_case=base, proposals=proposals, state=st, assessment=a,
                        minutes_estimate=self.minutes_estimate(case, a), pms=self._pms.get(case_id), pack=pack)

    def sync_from_pms(self) -> None:
        """Take what the PMS knows about each request: that it was sent, and Sun Life's electronic answer.
        Each step is taken once per PMS claim, so staff can still undo it. The PMS is the record of what was sent,
        so a request sent without Ophi's sign-off still moves on, and the audit log says so."""
        if self.pms_claims is None:
            return
        claims = self.pms_claims()
        self._pms = {}
        for cid in self.case_ids():
            case = self.base_case(cid)
            # The same patient, code and tooth: the PMS has no Ophi case id.
            claim = next((c for c in claims if str(c.patient_id) == case.patient.patient_id
                          and c.code == case.treatment.code and c.tooth == case.requested_tooth), None)
            if claim is None:
                continue
            self._pms[cid] = claim
            st = self.store.load(cid)
            sent, decided = f"{claim.claim_id}:sent", f"{claim.claim_id}:decision"
            if sent not in st.pms_synced and st.submitted_on is None and claim.answer_at != "rejected":
                self._record_sent(cid, st, claim.sent_on)
                signed = st.sign_off is not None and st.sign_off.signed_at.date() <= claim.sent_on
                self.audit(cid, "ABELDent", "mark_submitted", f"sent to Sun Life on {claim.sent_on.isoformat()} from ABELDent"
                           + ("" if signed else ", without a sign-off in Ophi"))
                self._synced(cid, sent)
            st = self.store.load(cid)
            if claim.outcome and decided not in st.pms_synced and st.submitted_on == claim.sent_on and st.decision is None:
                self.record_decision(cid, claim.outcome, claim.decided_on, claim.reason, "ABELDent")
                self._synced(cid, decided)

    def _synced(self, case_id: str, step: str) -> None:
        st = self.store.load(case_id)
        st.pms_synced.append(step)
        self.store.save(case_id, st)

    def queue(self) -> list[CaseView]:
        views = [self.view(cid) for cid in self.case_ids()]
        order = {Verdict.BLOCKED: 0, Verdict.NEEDS_INPUT: 1, Verdict.READY_WITH_RISKS: 2, Verdict.READY_TO_SUBMIT: 3,
                 Verdict.EXCLUDED_AS_CODED: 4, Verdict.PREAUTH_NOT_REQUIRED: 5}
        return sorted(views, key=lambda v: (v.signed, order[v.assessment.verdict],
                                            v.case.treatment.appointment_date or date.max, -v.dollars_at_risk))

    # --- writes -------------------------------------------------------------------------------

    def assert_criterion(self, case_id: str, criterion_id: str, value: str, by: str, licence: str | None, note: str | None = None,
                         role: str = "dentist") -> None:
        _dentist_only(role, "clinician assertions")
        if criterion_id not in self.pack_for(self.base_case(case_id)).assertion_criteria:
            raise KeyError(criterion_id)
        if value not in ("met", "not_met", "not_applicable"):
            raise ValueError(value)
        st = self.store.load(case_id)
        _not_sent(st)
        st.assertions[criterion_id] = {"value": value, "by": by, "licence": licence, "at": self.now().isoformat(), "note": note}
        st.sign_off = None  # any new clinical input invalidates a prior sign-off
        self.store.save(case_id, st)
        self.audit(case_id, by, "assert", f"{criterion_id}={value}" + (f" ({note})" if note else ""))

    def assert_many(self, case_id: str, items: list[dict], by: str, licence: str | None, role: str = "dentist") -> int:
        """Record several clinician assertions in one store transaction.

        items: list of {criterion_id, value, note, ophi}; `ophi` is what Ophi pre-filled, if anything, so whether the
        dentist kept or changed it stays on record.
        Returns number recorded. Validation is per-item; unknown criteria or
        values raise and no state is written.
        """
        _dentist_only(role, "clinician assertions")
        if not items:
            raise ValueError("no assertions supplied")
        # validate all before mutating
        criteria = self.pack_for(self.base_case(case_id)).assertion_criteria
        for it in items:
            cid = it.get("criterion_id")
            val = it.get("value")
            if cid not in criteria:
                raise KeyError(cid)
            if val not in ("met", "not_met", "not_applicable"):
                raise ValueError(val)
        st = self.store.load(case_id)
        _not_sent(st)
        now = self.now().isoformat()
        for it in items:
            cid = it["criterion_id"]
            st.assertions[cid] = {"value": it["value"], "by": by, "licence": licence, "at": now, "note": it.get("note"), "ophi": it.get("ophi")}
        st.sign_off = None
        self.store.save(case_id, st)
        for it in items:
            ophi = it.get("ophi")
            pre = "" if not ophi else ", as pre-filled" if ophi == it["value"] else f", pre-filled {ophi}"
            self.audit(case_id, by, "assert", f"{it['criterion_id']}={it['value']}{pre}" + (f" ({it.get('note')})" if it.get("note") else ""))
        return len(items)

    def confirm_proposal(self, case_id: str, artifact_id: str, decision: str, by: str) -> None:
        if decision not in ("confirmed", "rejected"):
            raise ValueError(decision)
        st = self.store.load(case_id)
        _not_sent(st)
        st.confirmations[artifact_id] = {"decision": decision, "by": by, "at": self.now().isoformat()}
        st.sign_off = None
        self.store.save(case_id, st)
        self.audit(case_id, by, "confirm_proposal", f"{artifact_id}: {decision}")

    def apply_fixes(self, case_id: str, requirement_ids: list[str], by: str) -> list[str]:
        """Close chart gaps Ophi can fix itself (ophi.fixes). Only gaps open on the case now; returns what was applied."""
        v = self.view(case_id)
        _not_sent(v.state)
        unknown = [rid for rid in requirement_ids if rid not in fixes.open_on(v.assessment)]
        if unknown or not requirement_ids:
            raise ValueError(f"no fix Ophi can apply for {', '.join(unknown) or 'this case'}")
        st, now = v.state, self.now().isoformat()
        titles = [fixes.title(v.case, rid, v.pack) for rid in requirement_ids]
        for rid, t in zip(requirement_ids, titles):
            st.fixes[rid] = {"by": by, "at": now, "title": t}
        st.sign_off = None
        self.store.save(case_id, st)
        for t in titles:
            self.audit(case_id, by, "apply_fix", t)
        return requirement_ids

    def save_narrative(self, case_id: str, text: str, by: str) -> None:
        text = _lf(text)
        self._validate(case_id, text)
        st = self.store.load(case_id)
        _not_sent(st)
        st.narrative_edits = text
        st.sign_off = None
        self.store.save(case_id, st)
        self.audit(case_id, by, "edit_narrative", f"{len(text)} chars")

    def sign_off(self, case_id: str, by: str, licence: str | None, narrative_text: str, role: str = "dentist") -> SignOff:
        """Non-skippable, one case, one human, one action. Dentist only. Blocked unless the verdict is READY
        and the narrative passes the grounding validator."""
        _dentist_only(role, "sign-off")
        narrative_text = _lf(narrative_text)
        self._validate(case_id, narrative_text)
        v = self.view(case_id)
        _not_sent(v.state)
        if v.assessment.verdict not in (Verdict.READY_TO_SUBMIT, Verdict.READY_WITH_RISKS):
            raise PermissionError(f"every applicable requirement must be documented before signing (the case is {v.assessment.verdict.value.lower().replace('_', ' ')})")
        so = SignOff(
            signed_by=by, licence=licence, signed_at=self.now(),
            attestation="I have reviewed this packet and it reflects my clinical judgment and the contents of this patient's record.",
            # Hash the ASCII text exactly as the packet ships it, so the verifier can match attestation to file.
            narrative_sha256=hashlib.sha256(narrative_ascii(narrative_text).encode()).hexdigest(),
            assessment_id=v.assessment.assessment_id, ruleset_version=v.assessment.ruleset.version,
        )
        st = v.state
        st.narrative_edits = narrative_text
        st.sign_off = so
        self.store.save(case_id, st)
        self.audit(case_id, by, "sign_off", f"assessment {so.assessment_id}, narrative sha256 {so.narrative_sha256[:12]}")
        return so

    def _snapshot(self, case_id: str, st: CaseState) -> Sent | None:
        """The chart, Ophi's reading of it and the signature it went out under, as the request goes out.
        Best effort: a chart Ophi cannot read is not a reason to refuse to record that the clinic sent it."""
        from ophi.outcomes.case_export import to_export
        try:
            v = self.view(case_id)
            return Sent(export=to_export(v.case), assessment=v.assessment.model_dump(mode="json"), sign_off=st.sign_off)
        except Exception:  # noqa: BLE001 — any unreadable chart
            log.warning("no send snapshot for %s: this attempt cannot become a training row", case_id, exc_info=True)
            return None

    def _record_sent(self, case_id: str, st: CaseState, on: date) -> None:
        """Both ways a request reaches Sun Life: staff sending a signed packet, and the PMS reporting one it
        already sent. The snapshot is taken here so neither path can leave an attempt without its chart."""
        st.snapshot = self._snapshot(case_id, st)  # while the sign-off is still on the case
        st.submitted_at, st.submitted_on = self.now(), on
        self.store.save(case_id, st)

    def mark_submitted(self, case_id: str, by: str, on: date | None = None) -> None:
        """Staff sent the signed packet through their PMS. Ophi never transmits; this records that they did."""
        v = self.view(case_id)
        _not_sent(v.state)
        if not v.signed:
            raise PermissionError("the packet has not been signed for the current chart")
        on = on or self.today()
        self._not_future(on, "the send date")
        if on < v.state.sign_off.signed_at.date():
            raise ValueError("the send date is before the dentist signed")
        self._record_sent(case_id, v.state, on)
        self.audit(case_id, by, "mark_submitted", f"sent to Sun Life on {on.isoformat()} through the PMS")

    def record_decision(self, case_id: str, outcome: str, decided_on: date, reason: str | None, by: str,
                        reason_key: str | None = None) -> None:
        st = self.store.load(case_id)
        if st.submitted_on is None or st.decision is not None:
            raise PermissionError("a decision can only be recorded for a case waiting on Sun Life")
        if outcome not in ("approved", "denied"):
            raise ValueError(outcome)
        reason = (reason or "").strip() or None
        if outcome == "denied" and reason and reason_key is None and self.note_reader:
            # Nobody classifies a denial by hand: the reader names it from Sun Life's own words, wherever they came
            # from -- an EOB note, a letter Gemini read, or text staff pasted. A reason it can't name stays unnamed.
            named = self.note_reader(reason)
            reason_key = named if named in REASONS else None
        if reason_key is not None and (reason_key not in REASONS or outcome != "denied"):
            raise ValueError(f"no denial reason '{reason_key}'")
        self._not_future(decided_on, "the decision date")
        if decided_on < st.submitted_on:
            raise ValueError("the decision date is before the day it was sent")
        st.decision = Decision(outcome=outcome, decided_on=decided_on, reason=reason,
                               reason_key=reason_key, recorded_by=by, recorded_at=self.now())
        self.store.save(case_id, st)
        self.audit(case_id, by, "record_decision", f"Sun Life {outcome} on {decided_on.isoformat()}" + (f": {st.decision.reason}" if st.decision.reason else ""))
        if self.record_outcome:  # the chart still describes what was sent; a resubmission's fixes come after this
            self.record_outcome(case_id, len(st.attempts) + 1, st.submitted_on, outcome, reason_key)

    def start_resubmission(self, case_id: str, by: str, reason_key: str | None = None) -> None:
        """A denied case starts over as a new request. The earlier attempt is kept; the old sign-off is not,
        because the dentist attests to each request. `reason_key` is what staff read Sun Life's reason as: when a
        new request can fix it, the case goes back to the column that does."""
        st = self.store.load(case_id)
        if st.decision is None or st.decision.outcome != "denied" or st.submitted_on is None:
            raise PermissionError("only a denied request can be resubmitted")
        if reason_key is not None and reason_key not in REASONS:
            raise ValueError(f"no denial reason '{reason_key}'")
        _, title, stage = REASONS.get(reason_key, (None, None, None))
        st.attempts.append(Attempt(submitted_on=st.submitted_on, decision=st.decision.model_copy(update={"reason_key": reason_key}),
                                   sent=st.snapshot))
        st.sign_off, st.submitted_at, st.submitted_on, st.decision = None, None, None, None
        st.snapshot = None  # the next attempt takes its own when it is sent
        st.ask = Ask(reason_key=reason_key, title=title, stage=stage, since=self.today()) if title else None
        self.store.save(case_id, st)
        self.audit(case_id, by, "start_resubmission", f"attempt {len(st.attempts) + 1}" + (f": {title}" if title else ""))

    def resolve_ask(self, case_id: str, by: str) -> None:
        """Staff did what Sun Life's denial asked for."""
        st = self.store.load(case_id)
        if st.ask is None or st.ask.done_by:
            raise PermissionError("Sun Life asked for nothing that is still open")
        st.ask.done_by = by
        st.sign_off = None
        self.store.save(case_id, st)
        self.audit(case_id, by, "resolve_ask", st.ask.title)

    def mark_booked(self, case_id: str, on: date, by: str) -> None:
        st = self.store.load(case_id)
        if st.decision is None or st.decision.outcome != "approved":
            raise PermissionError("book the crown once Sun Life's decision is recorded")
        if not st.decision.decided_on <= on <= valid_until(st.decision.decided_on):
            raise ValueError(f"the appointment must fall between the decision and {valid_until(st.decision.decided_on).isoformat()}, while it is valid")
        st.booked_on = on
        self.store.save(case_id, st)
        self.audit(case_id, by, "mark_booked", f"crown appointment booked for {on.isoformat()}")

    def skip_gaps(self, case_id: str, by: str) -> None:
        """Test runs: move the case past its chart gaps without fixing them, to try the rest of the flow."""
        v = self.view(case_id)
        _not_sent(v.state)
        rids = [rid for x in chart_actions(v.assessment) if x.action_type != "criterion_not_met" for rid in x.unblocks]
        if not rids:
            raise PermissionError("this case has no chart gaps to skip")
        st = v.state
        st.test_skips = sorted(set(st.test_skips) | set(rids))
        st.sign_off = None
        self.store.save(case_id, st)
        self.audit(case_id, by, "test_skip", ", ".join(rids))

    def restore_gaps(self, case_id: str, by: str) -> None:
        st = self.store.load(case_id)
        _not_sent(st)
        if not st.test_skips:
            raise PermissionError("no gaps were skipped on this case")
        st.test_skips, st.sign_off = [], None
        self.store.save(case_id, st)
        self.audit(case_id, by, "test_restore", "")

    def record_capture(self, case_id: str, requirement_id: str, by: str) -> None:
        """Demo: a clinician took the film or charted the perio while the patient was in the chair, and it reached
        the chart. Stands in for the imaging bridge; the engine then judges it like any other evidence."""
        v = self.view(case_id)
        _not_sent(v.state)
        if requirement_id not in CAPTURABLE or not any(requirement_id in x.unblocks for x in chair_actions(v.assessment)):
            raise PermissionError(f"this case has no chair gap to take for {requirement_id}")
        st = v.state
        st.captures[requirement_id] = self.today()
        st.sign_off = None
        self.store.save(case_id, st)
        self.audit(case_id, by, "demo_capture", requirement_id)

    def undo(self, case_id: str, step: str, by: str) -> None:
        """Take back the latest recorded step (a mis-tap at a busy front desk). Only the latest can go."""
        st = self.store.load(case_id)
        if step == "capture" and st.captures and not st.sent:
            st.captures.pop(list(st.captures)[-1])
            st.sign_off = None
        elif step == "booked" and st.booked_on:
            st.booked_on = None
        elif step == "decision" and st.decision and not st.booked_on:
            st.decision = None
        elif step == "sent" and st.submitted_on and not st.decision:
            st.submitted_at, st.submitted_on, st.snapshot = None, None, None
        else:
            raise PermissionError(f"'{step}' is not the latest step on this case")
        self.store.save(case_id, st)
        self.audit(case_id, by, "undo", step)

    # --- recover: past denials never resubmitted ---------------------------------------------------

    def lookback(self) -> LookBackReport:
        return self.lookback_report() if self.lookback_report else fixture_lookback()

    def _board_index(self) -> dict[tuple[str, str, int], str]:
        """Board cases keyed by patient, code and tooth -- how a past denial recognises its own crown once the
        clinic re-plans it. The PMS has no Ophi case id and Ophi never writes one back, so identity is the
        same triple `sync_from_pms` matches claims on."""
        idx = {}
        for cid in self.case_ids():
            c = self.base_case(cid)
            idx[(c.patient.display_name.casefold(), c.treatment.code, c.requested_tooth)] = cid
        return idx

    def _linked_case(self, row: LookBackRow, idx: dict[tuple[str, str, int], str]) -> str | None:
        return idx.get((row.patient_name.casefold(), row.code, row.tooth_fdi))

    def recover_rows(self) -> list[dict]:
        """Denials from the look-back that were never resubmitted: each with every call staff made on it, and
        the board case it turned into once the crown was re-planned."""
        calls = self.store.load_followup_calls()
        idx = self._board_index()
        rows = [r for r in self.lookback().rows if r.decision == "denied" and not r.resubmitted]
        return [{"row": r, "calls": calls.get(r.case_id, []), "followup": (calls.get(r.case_id) or [None])[-1],
                 "case_id": self._linked_case(r, idx)} for r in rows]

    def clinic_name(self) -> str:
        """What the clinic is called out loud, for a script a staffer reads to a patient. The charts carry it;
        `OPHI_CLINIC_NAME` overrides when a driver doesn't."""
        override = os.environ.get("OPHI_CLINIC_NAME", "").strip()
        if override:
            return override
        ids = self.case_ids()
        return self.base_case(ids[0]).clinic if ids else "Fictional Dental Centre"

    def recovered_rows(self) -> list[dict]:
        """Past denials that are moving again -- a crown for the same patient and tooth is back on the board.
        This is the only honest measure of what the call list won back: Ophi cannot write to the PMS, so a
        re-planned crown appearing there is the clinic acting, not Ophi claiming."""
        idx, calls = self._board_index(), self.store.load_followup_calls()
        return [{"row": r, "case_id": cid, "calls": calls.get(r.case_id, [])}
                for r in self.lookback().rows if r.decision == "denied"
                if (cid := self._linked_case(r, idx))]

    def orphan_followups(self) -> int:
        """Follow-ups recorded against rows the current source no longer lists -- staff's calls against an
        earlier history. Counted, not hidden: the work was done even if the row it belonged to is gone."""
        listed = {r.case_id for r in self.lookback().rows}
        return sum(1 for row_id in self.store.load_followups() if row_id not in listed)

    def record_followup(self, row_id: str, status: FollowUpStatus, note: str | None, by: str,
                        callback_on: date | None = None) -> None:
        if row_id not in {x["row"].case_id for x in self.recover_rows()}:
            raise KeyError(row_id)
        if status not in get_args(FollowUpStatus):
            raise ValueError(status)
        if callback_on is not None and callback_on < self.today():
            raise ValueError("a call-back date is in the past")
        if status == "declined" and callback_on is not None:
            raise ValueError("a patient who is not proceeding has no call-back date")
        f = FollowUp(status=status, note=(note or "").strip() or None, callback_on=callback_on, by=by, at=self.now())
        self.store.add_followup(row_id, f)
        detail = status + (f", call back {callback_on.isoformat()}" if callback_on else "") + (f" ({f.note})" if f.note else "")
        self.audit(row_id, by, "recover_followup", detail)

    def reset(self) -> None:
        self.store.reset()

    # --- helpers ------------------------------------------------------------------------------

    def audit(self, case_id: str, actor: str, event: str, detail: str) -> None:
        self.store.audit(case_id, actor, event, detail, at=self.now())

    def _not_future(self, day: date, what: str) -> None:
        if day > self.today():
            raise ValueError(f"{what} is in the future")

    def _validate(self, case_id: str, text: str) -> None:
        violations = validate_narrative(text, self.view(case_id).case)
        if violations:
            raise NarrativeInvalid(violations)

    @staticmethod
    def minutes_estimate(case: Case, a: Assessment) -> dict:
        """Transparent, sourced estimate of the manual cross-check this assessment replaced."""
        return {
            "manual_minutes": MANUAL_MINUTES_PER_PREAUTH,
            "manual_source": "docs/research/market.md — ~25 min staff time per preauthorization; ~$26.70/hr Ontario treatment coordinator",
            "engine_ms": a.workload.elapsed_ms,
            "artifacts_scanned": a.workload.artifacts_scanned,
            "subsystems_read": a.workload.subsystems_read,
            "requirements_evaluated": a.workload.requirements_evaluated,
            "labour_cad": round(MANUAL_MINUTES_PER_PREAUTH / 60 * COORDINATOR_HOURLY_CAD, 2),
        }

    def _apply_confirmation(self, p: ChartArtifact, st: CaseState) -> ChartArtifact:
        c = st.confirmations.get(p.artifact_id)
        if not c:
            return p
        payload = p.payload
        assert isinstance(payload, ExtractedDetailPayload)
        if c["decision"] == "confirmed":
            payload = payload.model_copy(update={"confirmed_by": c["by"], "confirmed_at": datetime.fromisoformat(c["at"])})
        else:
            payload = payload.model_copy(update={"rejected": True})
        return p.model_copy(update={"payload": payload})

    def _assertion_artifact(self, case: Case, criterion_id: str, a: dict) -> ChartArtifact:
        at = datetime.fromisoformat(a["at"])
        return ChartArtifact(
            artifact_id=f"assert_{criterion_id}", type=ArtifactType.CLINICIAN_ASSERTION, captured_at=at.date(),
            provenance=Provenance(source_system="ophi", source_table="assertions", extraction_method="user"),
            payload=AssertionPayload(criterion_id=criterion_id, value=a["value"], asserted_by=a["by"], licence=a.get("licence"),
                                     asserted_at=at, note=a.get("note")),
        )
