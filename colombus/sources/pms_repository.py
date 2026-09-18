"""PMS repository abstraction — Repository/Service pattern over PMS data fetching.

Wraps all data-fetching paths that previously lived scattered across
`lab/tools/chart_dump.py` (ABELDent live SQL), `colombus/casegen/dsl.py`
(YAML case files), and `colombus/service.py` (`CaseService.base_case`).

No behaviour change: every method delegates to the original implementation.
The interface is intentionally toggleable — a future flag/factory can swap
the concrete implementation (live PMS vs. filesystem fixtures vs. mocks)
without touching call sites.

Toggle (env var, primary: USE_MOCK_PMS_API):
    USE_MOCK_PMS_API=true  -> MockPmsRepository (mocks/*.json)
    USE_MOCK_PMS_API=false -> FileSystemPmsRepository (cases/demo/*.yaml)
    Aliases: USE_MOCK_DATA, PMS_USE_MOCKS (same truthy parsing).
    Truthy (case-insensitive): "true", "1", "yes", "on", "y"
    Falsy: "false", "0", "no", "off", "n", ""
    Helpers: should_use_mocks() / is_mock_enabled(), create_repository("auto"), create_auto_repository()

Usage:
    from colombus.sources.pms_repository import FileSystemPmsRepository, AbelDentPmsRepository, MockPmsRepository

    repo = FileSystemPmsRepository()          # filesystem / casegen (default)
    case = repo.get_case("singh")
    ids  = repo.list_case_ids()

    live = AbelDentPmsRepository()            # live ABELDent VM
    pids = live.planned_patient_ids()
    chart = live.fetch_patient_charts(pids)

    mock = MockPmsRepository()                # local mocks/mocks/pms/*.json
    auto = create_repository("auto")          # env-var toggle
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

import yaml

from colombus.casegen.dsl import build_case, load_case
from colombus.cdm.models import Case

# ---------------------------------------------------------------------------
# Protocol — the abstraction boundary
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES_DIR = ROOT / "cases" / "demo"
DEFAULT_LOOKBACK_DIR = ROOT / "cases" / "lookback"
DEFAULT_MOCKS_DIR = ROOT / "mocks"

# ---------------------------------------------------------------------------
# Toggle — env-var based mock switch
# ---------------------------------------------------------------------------

MOCK_ENV_VARS = ("USE_MOCK_PMS_API", "USE_MOCK_DATA", "PMS_USE_MOCKS")
_TRUTHY = {"true", "1", "yes", "on", "y"}
_FALSY = {"false", "0", "no", "off", "n", ""}


def _parse_bool_env(value: str | None) -> bool | None:
    """Parse truthy/falsy string; None if unset or unrecognised."""
    if value is None:
        return None
    v = value.strip().lower()
    if v in _TRUTHY:
        return True
    if v in _FALSY:
        return False
    return None


def should_use_mocks() -> bool:
    """Return True if env var requests mock PMS data.

    Checks USE_MOCK_PMS_API (primary), USE_MOCK_DATA, PMS_USE_MOCKS in order.
    Truthy values (case-insensitive): "true", "1", "yes", "on", "y".
    Falsy values: "false", "0", "no", "off", "n", "".
    Any truthy wins; otherwise False.
    """
    for key in MOCK_ENV_VARS:
        parsed = _parse_bool_env(os.environ.get(key))
        if parsed is True:
            return True
    return False


# alias for ergonomics
is_mock_enabled = should_use_mocks


@runtime_checkable
class PmsRepository(Protocol):
    """Abstract PMS data source. Concrete impls: filesystem or live ABELDent."""

    # --- case-level (CDM) --------------------------------------------------
    def list_case_ids(self) -> list[str]:
        """Return sorted case ids available from this source."""
        ...

    def get_case(self, case_id: str) -> Case:
        """Load a single Case by id. Raises FileNotFoundError if absent."""
        ...

    def get_cases(self, case_ids: list[str] | None = None) -> list[Case]:
        """Load multiple cases; if None, load all."""
        ...

    # --- PMS-level (raw chart) — only live PMS impls support these --------
    def planned_patient_ids(self) -> list[int]:
        """Patient ids with planned work (Transactions Type='P')."""
        ...

    def fetch_patient_charts(self, pids: list[int]) -> dict[int, dict]:
        """Fetch raw chart dump dicts keyed by pid (as chart_dump.build does)."""
        ...

    def fetch_raw(self, pids: list[int]) -> dict:
        """Low-level raw fetch (pat/tx/tdi/perio/notes/img) as in chart_dump.fetch."""
        ...


# ---------------------------------------------------------------------------
# FileSystem implementation — wraps casegen DSL (existing logic, preserved)
# ---------------------------------------------------------------------------

class FileSystemPmsRepository:
    """Filesystem-backed repository reading YAML cases via casegen DSL.

    This is the current production path for demo/eval/lookback.
    Preserves original logic: delegates to `load_case` / `build_case`.
    """

    def __init__(self, cases_dir: Path = DEFAULT_CASES_DIR) -> None:
        self.cases_dir = Path(cases_dir)

    # -- PmsRepository interface --------------------------------------------

    def list_case_ids(self) -> list[str]:
        return sorted(p.stem for p in self.cases_dir.glob("*.yaml"))

    def get_case(self, case_id: str) -> Case:
        path = self.cases_dir / f"{case_id}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"No case '{case_id}' in {self.cases_dir}")
        return load_case(path)

    def get_cases(self, case_ids: list[str] | None = None) -> list[Case]:
        ids = case_ids if case_ids is not None else self.list_case_ids()
        return [self.get_case(cid) for cid in ids]

    def planned_patient_ids(self) -> list[int]:
        raise NotImplementedError("FileSystemPmsRepository has no PMS connection; use AbelDentPmsRepository")

    def fetch_patient_charts(self, pids: list[int]) -> dict[int, dict]:
        raise NotImplementedError("FileSystemPmsRepository has no PMS connection; use AbelDentPmsRepository")

    def fetch_raw(self, pids: list[int]) -> dict:
        raise NotImplementedError("FileSystemPmsRepository has no PMS connection; use AbelDentPmsRepository")

    # -- additional helpers (lookback / raw dict) ---------------------------

    def load_raw_dict(self, case_id: str) -> dict:
        """Return the raw YAML dict for a case (before CDM build)."""
        path = self.cases_dir / f"{case_id}.yaml"
        return yaml.safe_load(path.read_text())

    def build_case_from_dict(self, data: dict, case_id: str) -> Case:
        """Build a Case from an in-memory dict (wraps build_case)."""
        return build_case(data, case_id)


# ---------------------------------------------------------------------------
# ABELDent live implementation — wraps lab/tools/chart_dump.py logic
# ---------------------------------------------------------------------------

class AbelDentPmsRepository:
    """Live ABELDent PMS repository. Delegates to chart_dump fetch logic.

    Preserves original SQL/fetch/build logic verbatim; adds no new
    behaviour. Requires the VM bridge at lab/vm/vm.
    """

    def __init__(self, vm_path: Path | None = None) -> None:
        self.vm_path = Path(vm_path) if vm_path else ROOT / "lab" / "vm" / "vm"
        # Lazy import to avoid hard dependency on VM at import time
        self._chart_dump = None

    def _load_chart_dump(self):
        if self._chart_dump is None:
            import importlib.util
            import sys
            spec = importlib.util.spec_from_file_location(
                "chart_dump", str(ROOT / "lab" / "tools" / "chart_dump.py"))
            if spec is None or spec.loader is None:
                raise ImportError("Cannot load lab/tools/chart_dump.py")
            mod = importlib.util.module_from_spec(spec)
            sys.modules["chart_dump"] = mod
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            self._chart_dump = mod
        return self._chart_dump

    # -- low-level SQL (preserved from chart_dump.sql) ---------------------

    def sql(self, query: str) -> list[dict]:
        """Run one SELECT against ABELDent and return rows as dicts."""
        r = subprocess.run([str(self.vm_path), "sql", query, "", "json"],
                           capture_output=True, text=True)
        body = r.stdout.strip()
        if not body:
            raise RuntimeError(f"empty response from vm sql (stderr: {r.stderr.strip()[:200]})")
        if body.startswith("REFUSED") or "Exception" in body[:200]:
            raise RuntimeError(body[:400])
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise RuntimeError(f"non-JSON from vm sql: {body[:300]}")
        if isinstance(data, dict):
            data = data["value"] if "value" in data and "Count" in data else [data]
        return data

    # -- PmsRepository interface --------------------------------------------

    def list_case_ids(self) -> list[str]:
        # Live PMS has no YAML case ids; delegate to filesystem or raise
        raise NotImplementedError("AbelDentPmsRepository lists pids, not case ids; use planned_patient_ids()")

    def get_case(self, case_id: str) -> Case:
        raise NotImplementedError("AbelDentPmsRepository fetches patient charts, not CDM cases directly")

    def get_cases(self, case_ids: list[str] | None = None) -> list[Case]:
        raise NotImplementedError("AbelDentPmsRepository fetches patient charts, not CDM cases directly")

    def planned_patient_ids(self) -> list[int]:
        mod = self._load_chart_dump()
        return mod.planned_pids()

    def fetch_raw(self, pids: list[int]) -> dict:
        mod = self._load_chart_dump()
        return mod.fetch(pids)

    def fetch_patient_charts(self, pids: list[int]) -> dict[int, dict]:
        """Fetch and build per-patient chart dicts (as chart_dump.build does)."""
        mod = self._load_chart_dump()
        raw = mod.fetch(pids)
        img_counts = {r["t"]: r["n"] for r in raw["img"]}
        out: dict[int, dict] = {}
        for pid in pids:
            case = mod.build(pid, raw, img_counts)
            if case is not None:
                out[pid] = case
        return out

    # -- passthrough helpers preserving original helpers --------------------

    def fetch_coverage(self, pids: list[int]):
        mod = self._load_chart_dump()
        P = _in_list(pids)
        return mod.fetch_coverage(P)


def _in_list(pids: list[int]) -> str:
    return ",".join(str(int(p)) for p in pids)


# ---------------------------------------------------------------------------
# Mock implementation — reads from mocks/*.json
# ---------------------------------------------------------------------------

class MockPmsRepository:
    """Local mock repository reading JSON fixtures from mocks/.

    Implements PmsRepository using synthetic data in mocks/*.json and
    mocks/pms/chart_dump_*.json. No network or VM required.
    """

    def __init__(self, mocks_dir: Path | None = None, **kwargs) -> None:
        # accept cases_dir etc. from auto factory without error
        if mocks_dir is None and "mocks_dir" in kwargs:
            mocks_dir = kwargs.pop("mocks_dir")
        # ignore unrelated kwargs like cases_dir
        self.mocks_dir = Path(mocks_dir) if mocks_dir else DEFAULT_MOCKS_DIR
        self._cache: dict[str, dict | list] = {}

    # -- internal helpers ---------------------------------------------------

    def _load(self, name: str) -> dict:
        """Load mocks/<name>.json (cached)."""
        if name in self._cache:
            return self._cache[name]  # type: ignore[return-value]
        path = self.mocks_dir / f"{name}.json"
        if not path.exists():
            # also try mocks/pms/ for chart dumps loaded via name
            path = self.mocks_dir / "pms" / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Mock file not found: {name}.json in {self.mocks_dir}")
        data = json.loads(path.read_text())
        self._cache[name] = data
        return data

    def _patients(self) -> list[dict]:
        return self._load("patients").get("patients", [])  # type: ignore[return-value]

    def _chart_for_pid(self, pid: int) -> dict | None:
        # try pms/chart_dump_<pid>.json
        for cand in [f"chart_dump_{pid}", f"chart_dump_{pid:03d}"]:
            p = self.mocks_dir / "pms" / f"{cand}.json"
            if p.exists():
                return json.loads(p.read_text())
        # fallback: search any chart_dump file with matching patient.pid
        pms_dir = self.mocks_dir / "pms"
        if pms_dir.exists():
            for jf in pms_dir.glob("*.json"):
                try:
                    d = json.loads(jf.read_text())
                    if d.get("patient", {}).get("pid") == pid:
                        return d
                except Exception:
                    continue
        return None

    def _chart_to_case(self, chart: dict) -> Case:
        """Convert a chart_dump-shaped dict to a CDM Case."""
        from colombus.cdm.models import (
            ArtifactType, Availability, ChartArtifact, Coverage, DentitionState,
            NotePayload, PerioChartPayload, Practitioner, ProcedureHistoryItem,
            ProposedTreatment, Provenance, RadiographPayload, Section, SiteDepths,
            SourceAssurance, ToothRef, Notation, Patient, Availability as Av,
        )

        patient_raw = chart.get("patient", {})
        pid = patient_raw.get("pid", 0)
        # map patient
        dob = None
        if patient_raw.get("dob"):
            try:
                dob = date.fromisoformat(patient_raw["dob"])
            except Exception:
                dob = None
        patient = Patient(
            patient_id=str(pid),
            display_name=f"{patient_raw.get('given','')} {patient_raw.get('surname','')}".strip() or str(pid),
            dob=dob,
            sex=patient_raw.get("gender") or patient_raw.get("sex"),
            cdcp_client_id=patient_raw.get("cdcp_client_id"),
        )
        # treatment from first planned_procedure
        planned_items = chart.get("planned_procedures", {}).get("items", []) if isinstance(chart.get("planned_procedures"), dict) else []
        if planned_items:
            first = planned_items[0]
        else:
            # try treatments.json style
            first = None
        if first is None:
            # fallback: look up in treatments.json
            try:
                tdata = self._load("treatments")
                for it in tdata.get("planned_procedures", []):
                    if it.get("pid") == pid:
                        first = it
                        break
            except FileNotFoundError:
                pass
        if first is None:
            raise ValueError(f"No planned procedure for pid {pid} in mocks")

        code = str(first.get("code", "27211"))
        tooth_fdi = int(first.get("tooth_fdi") or 16)
        provider = Practitioner(name=first.get("provider") or patient_raw.get("provider_name") or "Dr. Mock", licence=patient_raw.get("licence"))
        planned_date = None
        for k in ("date", "planned_date", "appointment_date"):
            if first.get(k):
                try:
                    planned_date = date.fromisoformat(first[k])
                    break
                except Exception:
                    pass
        fee_cents = None
        if first.get("fee") is not None:
            fee_cents = int(round(float(first["fee"]) * 100))

        tooth_ref = ToothRef(tooth_fdi=tooth_fdi, tooth_as_written=str(tooth_fdi), notation_declared=Notation.FDI)
        # as_of = planned date or today
        as_of = planned_date or date.today()
        treatment = ProposedTreatment(
            code=code, description=first.get("description"), tooth=tooth_ref,
            surfaces=list(first.get("surfaces") or []),
            provider=provider, planned_date=planned_date, fee_cents=fee_cents,
            appointment_date=planned_date,
        )
        # coverage
        coverage = None
        cov_items = chart.get("coverage", {}).get("items", []) if isinstance(chart.get("coverage"), dict) else []
        if cov_items:
            c0 = cov_items[0]
            coverage = Coverage(payer=c0.get("carrier_name") or "CDCP", plan_number=c0.get("plan_id"), member_id=c0.get("certificate"), active=c0.get("active", True))
        # procedure history from completed_procedures
        history: list[ProcedureHistoryItem] = []
        for cp in chart.get("completed_procedures", {}).get("items", []) if isinstance(chart.get("completed_procedures"), dict) else []:
            try:
                d = date.fromisoformat(cp["date"]) if cp.get("date") else as_of
            except Exception:
                d = as_of
            history.append(ProcedureHistoryItem(
                code=str(cp.get("code","")), tooth_fdi=cp.get("tooth_fdi"), surfaces=list(cp.get("surfaces") or []) if cp.get("surfaces") else [],
                performed_on=d, status="completed", description=cp.get("description"),
            ))
        # artifacts: perio, notes, radiographs
        artifacts: list[ChartArtifact] = []
        for exam in chart.get("perio_exams", {}).get("items", []) if isinstance(chart.get("perio_exams"), dict) else []:
            pocket = exam.get("pocket") or {}
            by_tooth = pocket.get("by_tooth_fdi") or {}
            teeth = []
            for k, depths in by_tooth.items():
                try:
                    fdi = int(k)
                except Exception:
                    continue
                vals = list(depths) + [None] * (6 - len(depths))
                teeth.append(SiteDepths(tooth_fdi=fdi, depths_mm=vals[:6]))
            if teeth:
                artifacts.append(ChartArtifact(
                    artifact_id=f"perio_{exam.get('exam_num',1)}_{pid}", type=ArtifactType.PERIO_CHART,
                    captured_at=date.fromisoformat(exam["date"]) if exam.get("date") else as_of,
                    provenance=Provenance(source_system="mocks", source_table="Perio", extraction_method="db_field"),
                    payload=PerioChartPayload(teeth=teeth, examiner=exam.get("provider"), certified=bool(exam.get("date_certified"))),
                ))
        for note in chart.get("clinical_notes", {}).get("items", []) if isinstance(chart.get("clinical_notes"), dict) else []:
            txt = note.get("text") or ""
            try:
                nd = date.fromisoformat(note["date"]) if note.get("date") else as_of
            except Exception:
                nd = as_of
            artifacts.append(ChartArtifact(
                artifact_id=f"note_{note.get('chart_num',1)}_{pid}", type=ArtifactType.CLINICAL_NOTE,
                captured_at=nd, provenance=Provenance(source_system="mocks", source_table="Notes", extraction_method="db_field"),
                payload=NotePayload(text=txt, author=note.get("operator"), teeth_fdi=[note["tooth_fdi"]] if note.get("tooth_fdi") else []),
            ))
        # imaging: treat procedure_events with ChartCode 242 as radiographs if no items
        for img in chart.get("imaging", {}).get("items", []) if isinstance(chart.get("imaging"), dict) else []:
            artifacts.append(ChartArtifact(
                artifact_id=f"rad_{pid}_{img.get('view','BW')}", type=ArtifactType.RADIOGRAPH,
                captured_at=as_of, provenance=Provenance(source_system="mocks", source_table="ChartArtifact", extraction_method="db_field"),
                payload=RadiographPayload(view=img.get("view","BW"), teeth_fdi=img.get("teeth_fdi") or []),
            ))
        # also surface procedure_events as radiograph hints
        if not any(a.type == ArtifactType.RADIOGRAPH for a in artifacts):
            for ev in chart.get("imaging", {}).get("procedure_events", []) if isinstance(chart.get("imaging"), dict) else []:
                artifacts.append(ChartArtifact(
                    artifact_id=f"rad_ev_{ev.get('trans_id',pid)}", type=ArtifactType.RADIOGRAPH,
                    captured_at=date.fromisoformat(ev["date"]) if ev.get("date") else as_of,
                    provenance=Provenance(source_system="mocks", source_table="Transactions", extraction_method="heuristic"),
                    payload=RadiographPayload(view="BW", teeth_fdi=[ev["tooth_fdi"]] if ev.get("tooth_fdi") else [], description=ev.get("description")),
                ))

        # assurance
        assurance: dict[Section, SourceAssurance] = {}
        for sec_key in ["imaging", "perio_exams", "clinical_notes"]:
            sec_map = {"imaging": Section.IMAGING, "perio_exams": Section.PERIO, "clinical_notes": Section.NOTES}
            sec = sec_map[sec_key]
            sa = chart.get(sec_key, {}).get("source_assurance") if isinstance(chart.get(sec_key), dict) else None
            if sa:
                status = sa.get("status", "present")
                avail_map = {"present": Av.PRESENT, "none_recorded": Av.ABSENT_CONFIRMED, "indeterminate": Av.UNKNOWN}
                assurance[sec] = SourceAssurance(availability=avail_map.get(status, Av.PRESENT), reason=sa.get("detail"))

        case_id = f"mock_{pid}"
        return Case(
            case_id=case_id, clinic="Mock Dental Centre", as_of=as_of,
            patient=patient, treatment=treatment, coverage=coverage,
            dentition=DentitionState(), procedure_history=history,
            artifacts=artifacts, assurance=assurance,
            source=Provenance(source_system="mocks", extraction_method="casegen"),
        )

    # -- PmsRepository interface --------------------------------------------

    def list_case_ids(self) -> list[str]:
        pms_dir = self.mocks_dir / "pms"
        ids: list[str] = []
        if pms_dir.exists():
            for p in sorted(pms_dir.glob("*.json")):
                ids.append(p.stem)
        if not ids:
            # fallback to patients as mock_101 etc
            for p in self._patients():
                ids.append(f"mock_{p.get('pid')}")
        return sorted(ids)

    def get_case(self, case_id: str) -> Case:
        # try direct chart_dump file
        p = self.mocks_dir / "pms" / f"{case_id}.json"
        if p.exists():
            chart = json.loads(p.read_text())
            return self._chart_to_case(chart)
        # try mock_101 style
        if case_id.startswith("mock_"):
            try:
                pid = int(case_id.split("_", 1)[1])
                chart = self._chart_for_pid(pid)
                if chart:
                    return self._chart_to_case(chart)
            except ValueError:
                pass
        # try chart_dump_<pid> indirection
        chart = self._chart_for_pid(int(case_id)) if case_id.isdigit() else None
        if chart:
            return self._chart_to_case(chart)
        raise FileNotFoundError(f"No mock case '{case_id}' in {self.mocks_dir / 'pms'}")

    def get_cases(self, case_ids: list[str] | None = None) -> list[Case]:
        ids = case_ids if case_ids is not None else self.list_case_ids()
        return [self.get_case(cid) for cid in ids]

    def planned_patient_ids(self) -> list[int]:
        # from patients + treatments planned
        pids: set[int] = set()
        for pat in self._patients():
            if pat.get("pid") is not None:
                pids.add(int(pat["pid"]))
        # intersect with planned if treatments file exists
        try:
            tdata = self._load("treatments")
            planned = {int(x["pid"]) for x in tdata.get("planned_procedures", []) if x.get("pid") is not None}
            if planned:
                pids &= planned
        except FileNotFoundError:
            pass
        # also from chart_dumps
        for cid in self.list_case_ids():
            try:
                case = self.get_case(cid)
                pids.add(int(case.patient.patient_id))
            except Exception:
                pass
        return sorted(pids)

    def fetch_patient_charts(self, pids: list[int]) -> dict[int, dict]:
        out: dict[int, dict] = {}
        for pid in pids:
            chart = self._chart_for_pid(pid)
            if chart is not None:
                out[pid] = chart
            else:
                # synthesize minimal chart from patients/treatments
                out[pid] = {"patient": next((x for x in self._patients() if x.get("pid")==pid), {"pid": pid}), "pid": pid}
        return out

    def fetch_raw(self, pids: list[int]) -> dict:
        charts = self.fetch_patient_charts(pids)
        return {"charts": charts, "pids": pids, "source": "mocks"}


# ---------------------------------------------------------------------------
# Factory — toggle point (no hardcoding yet; caller decides)
# ---------------------------------------------------------------------------

def create_repository(kind: str = "filesystem", **kwargs) -> PmsRepository:
    """Create a repository by kind.

    Args:
        kind: "filesystem" (default), "abeldent", "mock", or "auto".
              "auto" inspects env vars via should_use_mocks() and returns
              MockPmsRepository when mock toggle is ON, else FileSystem.
        **kwargs: forwarded to the concrete constructor (e.g. cases_dir, vm_path, mocks_dir)
    """
    if kind == "filesystem":
        return FileSystemPmsRepository(**kwargs)  # type: ignore[arg-type]
    if kind == "abeldent":
        return AbelDentPmsRepository(**kwargs)  # type: ignore[arg-type]
    if kind == "mock":
        return MockPmsRepository(**kwargs)  # type: ignore[arg-type]
    if kind == "auto":
        if should_use_mocks():
            return MockPmsRepository(**kwargs)  # type: ignore[arg-type]
        return FileSystemPmsRepository(**kwargs)  # type: ignore[arg-type]
    raise ValueError(f"Unknown repository kind: {kind!r} (expected 'filesystem', 'abeldent', 'mock', or 'auto')")


def create_auto_repository(**kwargs) -> PmsRepository:
    """Toggle-aware factory: returns MockPmsRepository if env var ON, else FileSystem."""
    return create_repository("auto", **kwargs)
