"""PMS repository abstraction — Repository/Service pattern over PMS data fetching.

Wraps all data-fetching paths that previously lived scattered across
`lab/tools/chart_dump.py` (ABELDent live SQL), `ophi/casegen/dsl.py`
(YAML case files), and `ophi/service.py` (`CaseService.base_case`).

No behaviour change: every method delegates to the original implementation.
The interface is intentionally toggleable — a future flag/factory can swap
the concrete implementation (live PMS vs. filesystem fixtures vs. mocks)
without touching call sites.

Toggle (env var, primary: USE_MOCK_PMS_API):
    USE_MOCK_PMS_API=true  -> MockPmsRepository (mocks/*.json)
    USE_MOCK_PMS_API=false -> FileSystemPmsRepository (cases/demo/*.yaml)
    Aliases: USE_MOCK_DATA, PMS_USE_MOCKS (same truthy parsing).
    USE_ABELDENT_PMS=true  -> AbelDentPmsRepository (live lab VM; wins over the mock toggle)
    Truthy (case-insensitive): "true", "1", "yes", "on", "y"
    Falsy: "false", "0", "no", "off", "n", ""
    Helpers: should_use_mocks() / is_mock_enabled(), create_repository("auto"), create_auto_repository()

Usage:
    from ophi.sources.pms_repository import FileSystemPmsRepository, AbelDentPmsRepository, MockPmsRepository

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
import logging
import os
import time
from datetime import date, datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

import yaml

from ophi.casegen.dsl import build_case, load_case
from ophi.cdm.models import Case
from ophi.sources.chart_case import chart_to_case

# ---------------------------------------------------------------------------
# Protocol — the abstraction boundary
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES_DIR = ROOT / "cases" / "demo"
DEFAULT_LOOKBACK_DIR = ROOT / "cases" / "lookback"
DEFAULT_MOCKS_DIR = ROOT / "mocks"
log = logging.getLogger("uvicorn.error")

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


def should_use_abeldent() -> bool:
    """True if USE_ABELDENT_PMS asks for the live ABELDent VM."""
    return _parse_bool_env(os.environ.get("USE_ABELDENT_PMS")) is True


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

# Each patient's next booked visit whose scheduled work names a crown ("crn #46"): the appointment the request races.
NEXT_CROWN_APPOINTMENTS = """
SELECT apid AS pid, CONVERT(varchar(10), MIN(adate), 23) AS day FROM apt
WHERE apid > 0 AND adate >= CAST(GETDATE() AS date) AND (apwork LIKE '%crn%' OR apwork LIKE '%crown%')
GROUP BY apid"""


class AbelDentPmsRepository:
    """Live ABELDent PMS repository. Delegates to chart_dump fetch logic.

    Preserves original SQL/fetch/build logic verbatim; adds no new
    behaviour. Requires the VM bridge at lab/vm/vm.
    """

    CHECK_SECONDS = 15
    # Tables charts are built from. SQL Server records each table's last write, so one cheap query tells whether
    # staff edited anything in ABELDent since the last pull.
    _CHANGED_SQL = ("SELECT CONVERT(varchar(23), MAX(last_user_update), 126) AS u FROM sys.dm_db_index_usage_stats "
                    "WHERE database_id = DB_ID() AND object_id IN (" + ", ".join(
                        f"OBJECT_ID('{t}')" for t in ("pat", "Transactions", "Plans", "tdi", "Perio", "Notes", "Charts", "dnt", "apt", "ixi", "nsp")) + ")")

    def __init__(self, vm_path: Path | None = None) -> None:
        self.vm_path = Path(vm_path) if vm_path else ROOT / "lab" / "vm" / "vm"
        # Lazy import to avoid hard dependency on VM at import time
        self._chart_dump = None
        self._cache: tuple[float, dict[str, Case]] | None = None
        self._stamp: str | None = None  # ABELDent's last chart write as of the cached pull

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

    # -- low-level SQL --------------------------------------------------------

    def sql(self, query: str, params: dict | None = None) -> list[dict]:
        """Run one SELECT against ABELDent and return rows as dicts; `@name` binds from params.
        Raises chart_dump.VmSqlError (a RuntimeError) when the VM or database rejects it."""
        return self._load_chart_dump().sql(query, params, vm=self.vm_path)

    # -- PmsRepository interface --------------------------------------------

    def _cases(self) -> dict[str, Case]:
        """One case per patient with a planned crown, judged as of today. A pull is nine queries over SSH (about 7 s)
        and every page asks for its cases, so re-pull only when ABELDent's charts changed, checked every CHECK_SECONDS."""
        if self._cache is not None and time.monotonic() - self._cache[0] < self.CHECK_SECONDS:
            return self._cache[1]
        try:
            stamp = self.sql(self._CHANGED_SQL)[0]["u"]
        except RuntimeError as e:  # chart_dump.VmSqlError: VM unreachable; staff keep the last pull
            if self._cache is None:
                raise
            log.warning(f"ABELDent change check skipped: {e}")
            return self._cache[1]
        cases = self._pull() if self._cache is None or stamp != self._stamp else self._cache[1]
        self._cache, self._stamp = (time.monotonic(), cases), stamp
        return cases

    def _pull(self) -> dict[str, Case]:
        charts = self.fetch_patient_charts(self.planned_patient_ids())
        providers = {r["id"]: r["name"] for r in self.sql("SELECT RTRIM(did) AS id, RTRIM(dname) AS name FROM dnt", None)}
        appointments = {r["pid"]: date.fromisoformat(r["day"]) for r in self.sql(NEXT_CROWN_APPOINTMENTS, None)}
        cases = {}
        for pid, chart in sorted(charts.items()):
            crowns = [p for p in chart["planned_procedures"]["items"] if p["code"].startswith("27") and p["tooth_fdi"]]
            if crowns:  # an open plan item before one ABELDent already marked applied
                first = next((p for p in crowns if p["status"] == "planned"), crowns[0])
                cases[f"abeldent_{pid}"] = chart_to_case(chart, first, case_id=f"abeldent_{pid}", as_of=date.today(),
                                                         providers=providers, appointment=appointments.get(pid),
                                                         clinic="ABELDent lab (Fictional Data)")
        return cases

    def list_case_ids(self) -> list[str]:
        return list(self._cases())

    def get_case(self, case_id: str) -> Case:
        try:
            return self._cases()[case_id]
        except KeyError:
            raise FileNotFoundError(f"No case '{case_id}' among the VM's planned crowns") from None

    def get_cases(self, case_ids: list[str] | None = None) -> list[Case]:
        cases = self._cases()
        return [self.get_case(cid) for cid in (case_ids if case_ids is not None else cases)]

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
# Recorded implementation — replays a snapshot of the live PMS
# ---------------------------------------------------------------------------

DEFAULT_SNAPSHOT = DEFAULT_MOCKS_DIR / "pms" / "snapshot.json"


def sql_key(query: str, params: dict | None) -> str:
    """One key per distinct query+binding, so a recording can be looked up on replay."""
    return json.dumps([" ".join(query.split()), params], sort_keys=True, default=str)


class RecordedPmsRepository(AbelDentPmsRepository):
    """The live repository with the VM replaced by a recording (scripts/record-pms-snapshot.py).

    Everything above the wire is the real code: cases, crown choice and the Look-Back are rebuilt from the
    recorded charts on each run, so the board is judged as of today, not as of the recording. Only queries the
    recording holds can be answered; anything else comes back empty, as a page whose data was never recorded.
    """

    def __init__(self, snapshot: Path | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.snapshot_path = Path(snapshot) if snapshot else DEFAULT_SNAPSHOT
        data = json.loads(self.snapshot_path.read_text())
        self.recorded_at = data.get("recorded_at")
        self._planned = [int(p) for p in data.get("planned_pids", [])]
        self._charts = {int(pid): chart for pid, chart in data.get("charts", {}).items()}
        self._sql = {sql_key(e["query"], e.get("params")): e["rows"] for e in data.get("sql", [])}

    def sql(self, query: str, params: dict | None = None) -> list[dict]:
        key = sql_key(query, params)
        if key not in self._sql:
            log.warning(f"Recorded PMS has no answer for this query; returning no rows: {' '.join(query.split())[:120]}")
            return []
        return self._sql[key]

    def planned_patient_ids(self) -> list[int]:
        return list(self._planned)

    def fetch_patient_charts(self, pids: list[int]) -> dict[int, dict]:
        return {pid: self._charts[pid] for pid in pids if pid in self._charts}

    def fetch_raw(self, pids: list[int]) -> dict:
        raise NotImplementedError("The recording holds built charts, not raw PMS rows")


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
        pid = chart.get("patient", {}).get("pid", 0)
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

        return chart_to_case(chart, first, case_id=f"mock_{pid}", as_of=date.fromisoformat(first["date"]) if first.get("date") else date.today(),
                             clinic="Mock Dental Centre", source="mocks")

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
        kind: "filesystem" (default), "abeldent", "mock", "recorded", or "auto".
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
    if kind == "recorded":
        return RecordedPmsRepository(**kwargs)  # type: ignore[arg-type]
    if kind == "auto":
        if should_use_abeldent():
            return AbelDentPmsRepository(**kwargs)  # type: ignore[arg-type]
        if should_use_mocks():
            if DEFAULT_SNAPSHOT.exists():  # the clinic's own PMS, recorded: the demo board without the VM
                return RecordedPmsRepository(**kwargs)  # type: ignore[arg-type]
            return MockPmsRepository(**kwargs)  # type: ignore[arg-type]
        return FileSystemPmsRepository(**kwargs)  # type: ignore[arg-type]
    raise ValueError(f"Unknown repository kind: {kind!r} (expected 'filesystem', 'abeldent', 'mock', 'recorded', or 'auto')")


def create_auto_repository(**kwargs) -> PmsRepository:
    """Toggle-aware factory: returns MockPmsRepository if env var ON, else FileSystem."""
    return create_repository("auto", **kwargs)
