"""casegen — a compact YAML dialect for authoring cases. The SME writes
`radiograph: {view: PA, tooth: 46, age: 364d}`, not raw CDM JSON.

Ages are relative to `as_of` so a case stays valid forever. Absolute dates are accepted too.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from pathlib import Path

import yaml
from dateutil.relativedelta import relativedelta

from ophi.cdm.models import (
    ArtifactType, AssertionPayload, Availability, Case, ChairVisit, ChartArtifact, ClaimFormPayload, Coverage,
    DentitionState, ExtractedDetailPayload, FileRef, Laterality, NotePayload, Notation, Patient, PerioChartPayload,
    PSRPayload, Practitioner, ProcedureHistoryItem, ProposedTreatment, Provenance, RadiographPayload,
    RadiographView, Section, SiteDepths, SourceAssurance, ToothRef, ToothState, TxPlanPayload,
)
from ophi.dental import notation, sextants

_AGE = re.compile(r"^(\d+)\s*(d|days?|m|mo|months?|y|years?)$")


def resolve_date(v, as_of: date) -> date | None:
    """`364d`, `13m`, `2y` (before as_of), an ISO date, or None."""
    if v is None:
        return None
    if isinstance(v, date):
        return v
    s = str(v).strip()
    m = _AGE.match(s)
    if not m:
        return date.fromisoformat(s)
    n, unit = int(m.group(1)), m.group(2)[0]
    if unit == "d":
        return as_of - timedelta(days=n)
    if unit == "m":
        return as_of - relativedelta(months=n)
    return as_of - relativedelta(years=n)


def _prov(kind: str = "casegen", row: str | None = None) -> Provenance:
    return Provenance(source_system="casegen", source_table=kind, source_row_key=row, extraction_method="casegen")


def load_case(path: Path) -> Case:
    return build_case(yaml.safe_load(path.read_text()), path.stem)


def build_case(d: dict, default_id: str) -> Case:
    as_of = resolve_date(d.get("as_of"), date.today()) or date.today()
    ids = _Ids()
    decl = Notation(d.get("notation", "fdi"))

    p = d["patient"]
    patient = Patient(patient_id=str(p.get("id", default_id)), display_name=p["name"], dob=resolve_date(p.get("dob"), as_of),
                      sex=p.get("sex"), cdcp_client_id=p.get("cdcp_client_id"),
                      phone=p.get("phone"), email=p.get("email"))
    prov = d.get("provider", {"name": "Dr. Lau", "licence": "ON-00000"})
    provider = Practitioner(name=prov["name"], licence=prov.get("licence"))

    t = d["treatment"]
    tooth = ToothRef(tooth_fdi=notation.to_fdi(t["tooth"], decl), tooth_as_written=str(t["tooth"]), notation_declared=decl)
    treatment = ProposedTreatment(
        code=str(t["code"]), description=t.get("description"), tooth=tooth, surfaces=list(t.get("surfaces", [])),
        provider=provider, planned_date=resolve_date(t.get("planned"), as_of), fee_cents=t.get("fee_cents"),
        lab_codes=[str(c) for c in t.get("lab_codes", [])], appointment_date=resolve_date(t.get("appointment"), as_of),
    )

    fdi = lambda x: notation.to_fdi(x, decl)  # noqa: E731 — every tooth number in the file is in the declared notation
    dent = d.get("dentition", {})
    dentition = DentitionState(
        teeth={fdi(k): ToothState(v) for k, v in dent.get("teeth", {}).items()},
        restored_surfaces={fdi(k): list(v) for k, v in dent.get("restored_surfaces", {}).items()},
        endo_treated={fdi(x) for x in dent.get("endo_treated", [])},
    )
    # `missing: [18, 28]` shorthand
    for m in dent.get("missing", []):
        dentition.teeth[fdi(m)] = ToothState.MISSING

    history = [ProcedureHistoryItem(code=str(h["code"]), tooth_fdi=fdi(h["tooth"]) if h.get("tooth") is not None else None, surfaces=list(h.get("surfaces", [])),
                                    performed_on=resolve_date(h.get("date") or h.get("age"), as_of) or as_of,
                                    status=h.get("status", "completed"), description=h.get("description"))
               for h in d.get("history", [])]

    artifacts: list[ChartArtifact] = [_radiograph(r, as_of, ids, decl) for r in d.get("radiographs", [])]
    for pc in d.get("perio_charts", []):
        artifacts.append(_perio_chart(pc, as_of, ids, dentition, decl))
    for ps in d.get("psr", []):
        artifacts.append(ChartArtifact(artifact_id=ps.get("id") or ids.next("psr"), type=ArtifactType.PSR,
                                       captured_at=resolve_date(ps.get("age", ps.get("date")), as_of), provenance=_prov("perio"),
                                       payload=PSRPayload(scores={s: ps.get("scores", {}).get(s) for s in sextants.ALL_SEXTANTS})))
    for n in d.get("notes", []):
        nid = n.get("id") or ids.next("note")
        artifacts.append(ChartArtifact(artifact_id=nid, type=ArtifactType.CLINICAL_NOTE,
                                       captured_at=resolve_date(n.get("age", n.get("date")), as_of), provenance=_prov("notes", nid),
                                       payload=NotePayload(text=n["text"], author=n.get("author"), note_type=n.get("type"),
                                                           signed_off=n.get("signed_off", True),
                                                           teeth_fdi=[notation.to_fdi(x, decl) for x in _listify(n.get("teeth", []))])))
    for tp in d.get("tx_plans", []):
        artifacts.append(ChartArtifact(artifact_id=tp.get("id") or ids.next("plan"), type=ArtifactType.TX_PLAN,
                                       captured_at=resolve_date(tp.get("age", tp.get("date")), as_of), provenance=_prov("plans"),
                                       payload=TxPlanPayload(pending_codes=[str(c) for c in tp.get("pending", [])],
                                                             completed_codes=[str(c) for c in tp.get("completed", [])],
                                                             description=tp.get("description"))))
    for ex in d.get("extracted", []):  # pre-proposed details, e.g. from a prior proposer run
        artifacts.append(ChartArtifact(artifact_id=ex.get("id") or ids.next("ext"), type=ArtifactType.TX_PLAN_DETAILS,
                                       captured_at=resolve_date(ex.get("age", ex.get("date")), as_of),
                                       provenance=Provenance(source_system="casegen", extraction_method=ex.get("method", "heuristic")),
                                       payload=ExtractedDetailPayload(source_artifact_id=ex["from"], quote=ex["quote"], claim=ex["claim"],
                                                                      confirmed_by=ex.get("confirmed_by"))))
    for a in d.get("assertions", []):
        when = resolve_date(a.get("age", a.get("date")), as_of) or as_of
        artifacts.append(ChartArtifact(artifact_id=a.get("id") or ids.next("assert"), type=ArtifactType.CLINICIAN_ASSERTION,
                                       captured_at=when, provenance=Provenance(source_system="user", extraction_method="user"),
                                       payload=AssertionPayload(criterion_id=a["criterion"], value=a.get("value", "met"),
                                                                asserted_by=a.get("by", provider.name), licence=provider.licence,
                                                                asserted_at=datetime.combine(when, datetime.min.time()), note=a.get("note"))))
    if d.get("claim_form"):
        artifacts.append(ChartArtifact(artifact_id="claim_form", type=ArtifactType.CLAIM_FORM, captured_at=as_of,
                                       provenance=_prov("packet"), payload=ClaimFormPayload()))

    assurance = {Section(k): SourceAssurance(availability=Availability(v if isinstance(v, str) else v["availability"]),
                                             reason=None if isinstance(v, str) else v.get("reason"))
                 for k, v in d.get("assurance", {}).items()}
    for sec in Section:  # default: what the case author put in is what the source saw
        assurance.setdefault(sec, SourceAssurance(availability=Availability.PRESENT))

    cov = d.get("coverage")
    coverage = Coverage(**cov) if isinstance(cov, dict) else None
    chair = d.get("in_chair")  # `in_chair: {op: "Op 2", with: "M. Haddad RDH"}`
    in_chair = ChairVisit(operatory=chair["op"], clinician=chair.get("with")) if chair else None

    return Case(case_id=d.get("id", default_id), clinic=d.get("clinic", "Fictional Dental Centre"), as_of=as_of, patient=patient,
                treatment=treatment, coverage=coverage, dentition=dentition, procedure_history=history, artifacts=artifacts,
                assurance=assurance, source=Provenance(source_system=d.get("source", "casegen"), extraction_method="casegen"),
                in_chair=in_chair)


# Chair gaps the demo closes in one tap, standing in for the imaging bridge and the perio software.
CAPTURABLE = frozenset({"radiograph_pa", "perio_chart"})


def capture_artifacts(case: Case, captures: dict[str, date]) -> list[ChartArtifact]:
    """What the chart gains once a clinician takes the film or charts the perio (demo only: fictional values)."""
    ids, decl = _Ids(), Notation.FDI
    examiner = case.in_chair.clinician if case.in_chair and case.in_chair.clinician else case.treatment.provider.name
    made = {
        "radiograph_pa": lambda day: _radiograph({"id": "demo_pa", "view": "PA", "tooth": case.requested_tooth, "date": day}, day, ids, decl),
        "perio_chart": lambda day: _perio_chart({"id": "demo_perio", "date": day, "sites": 6, "depth": 3, "examiner": examiner},
                                                day, ids, case.dentition, decl),
    }
    demo = Provenance(source_system="ophi-demo", source_table="capture", extraction_method="user")
    return [made[rid](day).model_copy(update={"provenance": demo}) for rid, day in captures.items() if rid in made]


def _radiograph(r: dict, as_of: date, ids: _Ids, decl: Notation) -> ChartArtifact:
    teeth = [notation.to_fdi(x, decl) for x in _listify(r.get("tooth", r.get("teeth", [])))]
    view = RadiographView(str(r["view"]).upper())
    lat = r.get("side")
    return ChartArtifact(
        artifact_id=r.get("id") or ids.next("rad"), type=ArtifactType.RADIOGRAPH,
        captured_at=resolve_date(r.get("age", r.get("date")), as_of), recorded_at=resolve_date(r.get("recorded"), as_of),
        provenance=_prov("imaging", r.get("id")),
        payload=RadiographPayload(view=view, teeth_fdi=teeth, laterality=Laterality(lat) if lat else None,
                                  images_apex=(view == RadiographView.PA) if r.get("images_apex") is None else r["images_apex"],
                                  description=r.get("description")),
        file=FileRef(path=r["file"]) if r.get("file") else None,
    )


def _perio_chart(pc: dict, as_of: date, ids: _Ids, dentition: DentitionState, decl: Notation) -> ChartArtifact:
    """`sites: 6` charts every present tooth; `teeth: {46: [3,2,3,4,3,3]}` overrides; `except: [17]` skips."""
    sites = int(pc.get("sites", 6))
    depth = int(pc.get("depth", 3))
    skip = {notation.to_fdi(x, decl) for x in pc.get("except", [])}
    explicit = {notation.to_fdi(k, decl): v for k, v in pc.get("teeth", {}).items()}
    universe = dentition.present_teeth(notation.ALL_FDI_PERMANENT) if pc.get("full_mouth", True) else []
    teeth = []
    for t in sorted(set(universe) | set(explicit)):
        if t in skip:
            continue
        if t in explicit:
            vals = list(explicit[t]) + [None] * (6 - len(explicit[t]))
        else:
            vals = [depth] * sites + [None] * (6 - sites)
        teeth.append(SiteDepths(tooth_fdi=t, depths_mm=vals[:6]))
    return ChartArtifact(artifact_id=pc.get("id") or ids.next("perio"), type=ArtifactType.PERIO_CHART,
                         captured_at=resolve_date(pc.get("age", pc.get("date")), as_of), provenance=_prov("Perio"),
                         payload=PerioChartPayload(teeth=teeth, examiner=pc.get("examiner"), certified=pc.get("certified", True)))


def _listify(v) -> list:
    if v is None:
        return []
    return list(v) if isinstance(v, (list, tuple)) else [v]


class _Ids:
    def __init__(self) -> None:
        self.n: dict[str, int] = {}

    def next(self, prefix: str) -> str:
        self.n[prefix] = self.n.get(prefix, 0) + 1
        return f"{prefix}_{self.n[prefix]}"
