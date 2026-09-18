"""Application layer: cases + human inputs -> assessment. The web app and CLI call this, nothing else.

Human inputs (clinician assertions, confirmations of proposed evidence, sign-off) are stored per case
in a small JSON state store and re-applied on every load, then the deterministic engine re-runs.
The engine never sees the store; it only sees artifacts.
"""

from __future__ import annotations

import hashlib
import shutil
import threading
from datetime import UTC, date, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from colombus.casegen.dsl import load_case
from colombus.cdm.models import (
    ArtifactType, AssertionPayload, Case, ChartArtifact, ExtractedDetailPayload, Provenance,
)
from colombus.engine.assess import assess
from colombus.engine.models import Assessment, Verdict
from colombus.extract.proposer import propose_for_case
from colombus.packet.documents import narrative_ascii
from colombus.packet.narrative import validate_narrative
from colombus.rules.loader import default_pack
from colombus.rules.schema import RulePack

ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT / "cases" / "demo"
VAR_DIR = ROOT / "var"

# Manual baseline per preauthorization, from docs/research/market.md (25 min per request, ~$26.70/hr
# Ontario treatment coordinator). Shown as an estimate with its source, never as a measured saving.
MANUAL_MINUTES_PER_PREAUTH = 25
COORDINATOR_HOURLY_CAD = 26.70


def _dentist_only(role: str, what: str) -> None:
    if role != "dentist":
        raise PermissionError(f"{what} may only be recorded by the treating dentist (actor role: {role})")


def _lf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


class NarrativeInvalid(ValueError):
    """The rationale text failed the grounding / copy-law validator. Carries the violations."""

    def __init__(self, violations: list[str]) -> None:
        super().__init__("; ".join(violations))
        self.violations = violations


def identity_tokens(case: Case) -> list[str]:
    """Tokens that must never appear in packet filenames or the index (checked by the verifier)."""
    raw = [*case.patient.display_name.replace(",", " ").split(), case.patient.patient_id, case.patient.cdcp_client_id or ""]
    return [t for t in raw if len(t) >= 3]


class SignOff(BaseModel):
    signed_by: str
    licence: str | None
    signed_at: datetime
    attestation: str
    narrative_sha256: str
    assessment_id: str
    ruleset_version: str


class CaseState(BaseModel):
    assertions: dict[str, dict] = Field(default_factory=dict)  # criterion_id -> {value, by, licence, at, note}
    confirmations: dict[str, dict] = Field(default_factory=dict)  # proposal artifact id -> {decision, by, at}
    narrative_edits: str | None = None
    sign_off: SignOff | None = None
    submitted_at: datetime | None = None


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

    def audit(self, case_id: str, actor: str, event: str, detail: str) -> None:
        ev = AuditEvent(at=datetime.now(UTC), case_id=case_id, actor=actor, event=event, detail=detail)
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


class CaseService:
    def __init__(
        self,
        cases_dir: Path = CASES_DIR,
        store: Store | None = None,
        pack: RulePack | None = None,
        repository=None,
    ) -> None:
        self.cases_dir = cases_dir
        self.store = store or Store()
        self.pack = pack or default_pack()
        # Optional PMS repository abstraction; toggle-aware default.
        if repository is not None:
            self.repository = repository
        else:
            from colombus.sources.pms_repository import (
                FileSystemPmsRepository,
                MockPmsRepository,
                should_use_mocks,
            )

            if should_use_mocks():
                self.repository = MockPmsRepository()
            else:
                self.repository = FileSystemPmsRepository(cases_dir)

    # --- reads --------------------------------------------------------------------------------

    def case_ids(self) -> list[str]:
        return self.repository.list_case_ids()

    def base_case(self, case_id: str) -> Case:
        return self.repository.get_case(case_id)

    def view(self, case_id: str) -> CaseView:
        base = self.base_case(case_id)
        st = self.store.load(case_id)
        proposals = [self._apply_confirmation(p, st) for p in propose_for_case(base)]
        user_assertions = [self._assertion_artifact(base, cid, a) for cid, a in st.assertions.items()]
        case = base.with_artifacts(proposals + user_assertions)
        a = assess(case, self.pack)
        return CaseView(case=case, base_case=base, proposals=proposals, state=st, assessment=a,
                        minutes_estimate=self.minutes_estimate(case, a))

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
        if criterion_id not in self.pack.assertion_criteria:
            raise KeyError(criterion_id)
        if value not in ("met", "not_met", "not_applicable"):
            raise ValueError(value)
        st = self.store.load(case_id)
        st.assertions[criterion_id] = {"value": value, "by": by, "licence": licence, "at": datetime.now(UTC).isoformat(), "note": note}
        st.sign_off = None  # any new clinical input invalidates a prior sign-off
        self.store.save(case_id, st)
        self.store.audit(case_id, by, "assert", f"{criterion_id}={value}" + (f" ({note})" if note else ""))

    def assert_many(self, case_id: str, items: list[dict], by: str, licence: str | None, role: str = "dentist") -> int:
        """Record several clinician assertions in one store transaction.

        items: list of {criterion_id, value, note}
        Returns number recorded. Validation is per-item; unknown criteria or
        values raise and no state is written.
        """
        _dentist_only(role, "clinician assertions")
        if not items:
            raise ValueError("no assertions supplied")
        # validate all before mutating
        for it in items:
            cid = it.get("criterion_id")
            val = it.get("value")
            if cid not in self.pack.assertion_criteria:
                raise KeyError(cid)
            if val not in ("met", "not_met", "not_applicable"):
                raise ValueError(val)
        st = self.store.load(case_id)
        now = datetime.now(UTC).isoformat()
        for it in items:
            cid = it["criterion_id"]
            st.assertions[cid] = {"value": it["value"], "by": by, "licence": licence, "at": now, "note": it.get("note")}
        st.sign_off = None
        self.store.save(case_id, st)
        for it in items:
            self.store.audit(case_id, by, "assert", f"{it['criterion_id']}={it['value']}" + (f" ({it.get('note')})" if it.get("note") else ""))
        return len(items)

    def confirm_proposal(self, case_id: str, artifact_id: str, decision: str, by: str) -> None:
        if decision not in ("confirmed", "rejected"):
            raise ValueError(decision)
        st = self.store.load(case_id)
        st.confirmations[artifact_id] = {"decision": decision, "by": by, "at": datetime.now(UTC).isoformat()}
        st.sign_off = None
        self.store.save(case_id, st)
        self.store.audit(case_id, by, "confirm_proposal", f"{artifact_id}: {decision}")

    def save_narrative(self, case_id: str, text: str, by: str) -> None:
        text = _lf(text)
        self._validate(case_id, text)
        st = self.store.load(case_id)
        st.narrative_edits = text
        st.sign_off = None
        self.store.save(case_id, st)
        self.store.audit(case_id, by, "edit_narrative", f"{len(text)} chars")

    def sign_off(self, case_id: str, by: str, licence: str | None, narrative_text: str, role: str = "dentist") -> SignOff:
        """Non-skippable, one case, one human, one action. Dentist only. Blocked unless the verdict is READY
        and the narrative passes the grounding validator."""
        _dentist_only(role, "sign-off")
        narrative_text = _lf(narrative_text)
        self._validate(case_id, narrative_text)
        v = self.view(case_id)
        if v.assessment.verdict not in (Verdict.READY_TO_SUBMIT, Verdict.READY_WITH_RISKS):
            raise PermissionError(f"cannot sign off: verdict is {v.assessment.verdict}")
        so = SignOff(
            signed_by=by, licence=licence, signed_at=datetime.now(UTC),
            attestation="I have reviewed this packet and it reflects my clinical judgment and the contents of this patient's record.",
            # Hash the ASCII text exactly as the packet ships it, so the verifier can match attestation to file.
            narrative_sha256=hashlib.sha256(narrative_ascii(narrative_text).encode()).hexdigest(),
            assessment_id=v.assessment.assessment_id, ruleset_version=v.assessment.ruleset.version,
        )
        st = v.state
        st.narrative_edits = narrative_text
        st.sign_off = so
        self.store.save(case_id, st)
        self.store.audit(case_id, by, "sign_off", f"assessment {so.assessment_id}, narrative sha256 {so.narrative_sha256[:12]}")
        return so

    def mark_submitted(self, case_id: str, by: str) -> None:
        st = self.store.load(case_id)
        st.submitted_at = datetime.now(UTC)
        self.store.save(case_id, st)
        self.store.audit(case_id, by, "mark_submitted", "staff recorded submission via the PMS/CDAnet")

    def reset(self) -> None:
        self.store.reset()

    # --- helpers ------------------------------------------------------------------------------

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
            provenance=Provenance(source_system="colombus", source_table="assertions", extraction_method="user"),
            payload=AssertionPayload(criterion_id=criterion_id, value=a["value"], asserted_by=a["by"], licence=a.get("licence"),
                                     asserted_at=at, note=a.get("note")),
        )
