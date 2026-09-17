"""Canonical data model (CDM) v1 — the typed artifact index the rules engine judges over.

Shapes follow FHIR R4 names where they exist (Patient, Coverage, Procedure) and diverge where
dentistry needs it (PerioExam, DentitionState). Two cross-cutting elements are required everywhere:
`Provenance` on every record and `SourceAssurance` on every section — "this patient has no perio
chart" and "this driver cannot see perio charts" are opposite clinical conclusions.

Tooth numbering is FDI (ISO 3950) internally. `tooth_as_written` and `notation_declared` are kept so
nothing is inferred from the number alone ("16" is valid in both FDI and Universal).
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Notation(StrEnum):
    FDI = "fdi"
    UNIVERSAL = "universal"


class Availability(StrEnum):
    """Per-section source assurance. `Unknown`/`Degraded` must never be read as "absent"."""

    PRESENT = "Present"
    ABSENT_CONFIRMED = "AbsentConfirmed"
    UNKNOWN = "Unknown"
    DEGRADED = "Degraded"


class SourceAssurance(BaseModel):
    availability: Availability
    reason: str | None = None


class Provenance(BaseModel):
    source_system: str
    source_version: str | None = None
    source_table: str | None = None
    source_row_key: str | None = None
    query_id: str | None = None
    extracted_at: datetime | None = None
    extraction_method: Literal["db_field", "decoded", "heuristic", "llm", "user", "packet", "casegen"] = "db_field"
    confidence: float | None = None


class ArtifactType(StrEnum):
    RADIOGRAPH = "radiograph"
    PERIO_CHART = "perio_chart"
    PSR = "psr"
    PERIO_MEASUREMENTS = "perio_measurements"
    PHOTO = "photo"
    CLINICAL_NOTE = "clinical_note"
    TX_PLAN = "tx_plan"
    TX_PLAN_DETAILS = "tx_plan_details"  # plan info found inside a note (footnote 1)
    CLINICIAN_ASSERTION = "clinician_assertion"
    CLAIM_FORM = "claim_form"
    NARRATIVE = "narrative"


class RadiographView(StrEnum):
    PA = "PA"
    BW = "BW"
    PANO = "PANO"
    OCCLUSAL = "OCCLUSAL"
    CBCT = "CBCT"
    OTHER = "OTHER"


class Laterality(StrEnum):
    RIGHT = "right"
    LEFT = "left"
    BOTH = "both"


class FileRef(BaseModel):
    path: str
    media_type: str | None = None
    sha256: str | None = None
    bytes: int | None = None
    width_px: int | None = None
    height_px: int | None = None
    dpi: int | None = None
    bit_depth: int | None = None


class RadiographPayload(BaseModel):
    view: RadiographView
    teeth_fdi: list[int] = Field(default_factory=list)
    laterality: Laterality | None = None
    images_apex: bool | None = None  # bitewings do not image the periapical region
    description: str | None = None


class SiteDepths(BaseModel):
    """Six probing depths in mm for one tooth: DB, B, MB, DL, L, ML. None = not measured."""

    tooth_fdi: int
    depths_mm: list[int | None] = Field(min_length=6, max_length=6)
    bleeding: list[bool] | None = None
    furcation: int | None = None  # 0–3 Glickman grade where recorded
    mobility: int | None = None

    @property
    def sites_measured(self) -> int:
        return sum(1 for d in self.depths_mm if d is not None)


class PerioChartPayload(BaseModel):
    teeth: list[SiteDepths]
    examiner: str | None = None
    certified: bool = True  # ABELDent `DateCertified`; uncertified charts are drafts

    @property
    def point_count(self) -> int:
        return sum(t.sites_measured for t in self.teeth)

    @property
    def teeth_charted(self) -> set[int]:
        return {t.tooth_fdi for t in self.teeth if t.sites_measured > 0}

    def sites_for(self, tooth_fdi: int) -> int:
        return next((t.sites_measured for t in self.teeth if t.tooth_fdi == tooth_fdi), 0)


class PSRPayload(BaseModel):
    """Periodontal Screening and Recording, one score 0–4 per sextant S1..S6. None = not recorded."""

    scores: dict[str, int | None]


class NotePayload(BaseModel):
    text: str
    author: str | None = None
    note_type: str | None = None
    signed_off: bool = True
    teeth_fdi: list[int] = Field(default_factory=list)


class TxPlanPayload(BaseModel):
    """A structured treatment plan: what is pending and what was completed that is relevant."""

    plan_id: str | None = None
    pending_codes: list[str] = Field(default_factory=list)
    completed_codes: list[str] = Field(default_factory=list)
    description: str | None = None


class ExtractedDetailPayload(BaseModel):
    """A fact a proposer found inside free text. `quote` must be an exact substring of the source."""

    source_artifact_id: str
    quote: str
    claim: str
    teeth_fdi: list[int] = Field(default_factory=list)
    confirmed_by: str | None = None
    confirmed_at: datetime | None = None
    rejected: bool = False


class AssertionPayload(BaseModel):
    """A clinician's attributed answer to one CDCP criterion. Colombus never asserts these itself."""

    criterion_id: str
    value: Literal["met", "not_met", "not_applicable"]
    asserted_by: str
    licence: str | None = None
    asserted_at: datetime
    note: str | None = None


class ClaimFormPayload(BaseModel):
    form: Literal["cda_clhia", "computer_generated"] = "computer_generated"


Payload = (
    RadiographPayload
    | PerioChartPayload
    | PSRPayload
    | NotePayload
    | TxPlanPayload
    | ExtractedDetailPayload
    | AssertionPayload
    | ClaimFormPayload
)


class ChartArtifact(BaseModel):
    artifact_id: str
    type: ArtifactType
    captured_at: date | None = None  # when the evidence was CREATED — the only date recency may use
    recorded_at: date | None = None  # when it was entered into the PMS
    date_confidence: Literal["source", "inferred", "unknown"] = "source"
    provenance: Provenance
    payload: Payload
    file: FileRef | None = None

    @model_validator(mode="after")
    def _date_confidence_honest(self) -> ChartArtifact:
        if self.captured_at is None and self.date_confidence == "source":
            self.date_confidence = "unknown"
        return self

    @property
    def is_unconfirmed_extraction(self) -> bool:
        p = self.payload
        return isinstance(p, ExtractedDetailPayload) and p.confirmed_by is None and not p.rejected

    @property
    def teeth_fdi(self) -> list[int]:
        p = self.payload
        if isinstance(p, RadiographPayload):
            return p.teeth_fdi
        if isinstance(p, PerioChartPayload):
            return sorted(p.teeth_charted)
        if isinstance(p, (NotePayload, ExtractedDetailPayload)):
            return p.teeth_fdi
        return []


# --- Patient-side entities -------------------------------------------------------------------


class Patient(BaseModel):
    patient_id: str
    display_name: str  # demo-only; the LLM boundary (DeidentifiedCaseView) never sees this
    dob: date | None = None
    sex: str | None = None
    cdcp_client_id: str | None = None

    def age_on(self, on: date) -> int | None:
        if self.dob is None:
            return None
        years = on.year - self.dob.year
        if (on.month, on.day) < (self.dob.month, self.dob.day):
            years -= 1
        return years


class Practitioner(BaseModel):
    name: str
    licence: str | None = None
    role: str = "dentist"


class Coverage(BaseModel):
    payer: str = "CDCP"
    plan_number: str | None = None
    member_id: str | None = None
    active: bool | None = None
    copay_tier: str | None = None


class ToothRef(BaseModel):
    tooth_fdi: int
    tooth_as_written: str
    notation_declared: Notation


class ProposedTreatment(BaseModel):
    code: str  # USC&LS procedure code, e.g. 27211
    description: str | None = None
    tooth: ToothRef
    surfaces: list[str] = Field(default_factory=list)
    provider: Practitioner
    planned_date: date | None = None
    fee_cents: int | None = None
    lab_codes: list[str] = Field(default_factory=list)
    appointment_date: date | None = None


class ProcedureHistoryItem(BaseModel):
    code: str
    tooth_fdi: int | None = None
    surfaces: list[str] = Field(default_factory=list)
    performed_on: date
    status: Literal["completed", "planned"] = "completed"
    description: str | None = None
    provenance: Provenance | None = None


class ToothState(StrEnum):
    PRESENT = "present"
    MISSING = "missing"
    UNERUPTED = "unerupted"
    IMPLANT = "implant"
    PONTIC = "pontic"


class DentitionState(BaseModel):
    """The odontogram. Teeth not listed default to PRESENT."""

    teeth: dict[int, ToothState] = Field(default_factory=dict)
    restored_surfaces: dict[int, list[str]] = Field(default_factory=dict)
    endo_treated: set[int] = Field(default_factory=set)

    def state(self, tooth_fdi: int) -> ToothState:
        return self.teeth.get(tooth_fdi, ToothState.PRESENT)

    def present_teeth(self, universe: list[int]) -> list[int]:
        return [t for t in universe if self.state(t) == ToothState.PRESENT]


class Section(StrEnum):
    IMAGING = "imaging"
    PERIO = "perio"
    NOTES = "notes"
    PROCEDURE_HISTORY = "procedure_history"
    PLANNED = "planned_procedures"
    DENTITION = "dentition"
    COVERAGE = "coverage"


class Case(BaseModel):
    """One patient + one proposed treatment, assessed as of an intended submission date."""

    case_id: str
    clinic: str = "Fictional Dental Centre"
    as_of: date  # intended submission date — the pack effective on this date applies
    patient: Patient
    treatment: ProposedTreatment
    coverage: Coverage | None = None
    dentition: DentitionState = Field(default_factory=DentitionState)
    procedure_history: list[ProcedureHistoryItem] = Field(default_factory=list)
    artifacts: list[ChartArtifact] = Field(default_factory=list)
    assurance: dict[Section, SourceAssurance] = Field(default_factory=dict)
    source: Provenance | None = None

    def assurance_for(self, section: Section) -> SourceAssurance:
        return self.assurance.get(section, SourceAssurance(availability=Availability.UNKNOWN, reason="section not reported by driver"))

    def artifacts_of(self, *types: ArtifactType) -> list[ChartArtifact]:
        return [a for a in self.artifacts if a.type in types]

    def artifact(self, artifact_id: str) -> ChartArtifact | None:
        return next((a for a in self.artifacts if a.artifact_id == artifact_id), None)

    def with_artifacts(self, extra: list[ChartArtifact]) -> Case:
        return self.model_copy(update={"artifacts": [*self.artifacts, *extra]})

    @property
    def requested_tooth(self) -> int:
        return self.treatment.tooth.tooth_fdi
