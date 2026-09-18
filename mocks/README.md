# Mocks — PMS API Mock Fixtures

Fictional data for local dev/test without a live ABELDent instance. All schemas mirror the real PMS API as emitted by `lab/tools/chart_dump.py` and typed in `colombus/cdm/models.py`.

> No real PHI. Names/dates/fees are synthetic.

## Source of truth

| Mock file | Real source | Schema reference |
|---|---|---|
| `patients.json` | `pat` table (`pid, plname, pfname, pbirth, pgender, pdentist, pinactive, pnonpatient`) | `colombus/cdm/models.py:228 Patient` |
| `appointments.json` | `Transactions.Appt` grouping + `PlanNum` | `ProposedTreatment.appointment_date` |
| `treatments.json` | `Transactions` (Type `P`=planned, ` `=completed) + `tdi` financial mirror, `Plans` | `ProposedTreatment`, `ProcedureHistoryItem`, `chart_dump.py:ledger_sections()` |
| `dentists.json` | `pat.pdentist`, `Transactions.ProvID/RespProvID` | `Practitioner` |
| `clinics.json` | App-level `Case.clinic` (single-site PMS has one; multi-site added for mock) | `Case.clinic` |
| `billing.json` | `tdi` (`itrid, idate, ijcode, jdesc1, jneedsxrays, itooth, isurf, idid, iresppvdr, iefee, ilabfee, itype`) | `chart_dump.py:proc_row()` |
| `coverage.json` | `ixi` + `nsp` + `ins` joined | `Coverage`, `chart_dump.py:cov_row()` |
| `perio_exams.json` | `Perio` positional byte arrays (192 pocket sites, 6 per tooth) | `PerioChartPayload`, `SiteDepths`, `chart_dump.py:decode_exam()` |
| `clinical_notes.json` | `Notes` + `Charts` (`KeyType, NoteType, ToothNumber, OperatorID, Note`) | `NotePayload` |
| `radiographs.json` | `ChartArtifact` / `RadiographPayload` + `Transactions` ChartCode 242 procedure_events | `RadiographPayload`, `RadiographView`, `FileRef` |
| `pms/chart_dump_101.json` | Full `chart_dump.py:build()` output for one patient | All above combined, matches `fixtures/abeldent/fictional/*.json` shape |
| `pms/chart_dump_102.json` | Full chart for bridge case | Same, with `bridge_group` 1..n |

## Key conventions (match ABELDent)

- **Tooth numbering**: FDI (ISO 3950) throughout. `tooth_universal` provided where relevant. Conversion in `colombus/dental/notation.py`.
- **Fees**: dollars in mocks (DB stores cents; `Billed/100`, `iefee/100`).
- **Ledger duality**: `Transactions` is clinical ledger; `tdi` is financial ledger. Planned rows mirrored with sentinel `itrid=99999998` (`itype P`), completed rows matched by `code+tooth+date` then `code+tooth+fee`.
- **Bridge grouping**: `bridge_group` (`Transactions.Grp`) is position 1..n within bridge, not a shared bridge ID.
- **Source assurance**: every section carries `source_assurance: {status, detail}` — `present` / `none_recorded` / `indeterminate` distinguishes "absent confirmed" from "not visible to driver".
- **Dates**: ISO `YYYY-MM-DD`. Perio `DateCertified` null in fictional data; mocks include certified dates for dev.

## Usage

```python
import json, pathlib
patients = json.loads(pathlib.Path("mocks/patients.json").read_text())["patients"]
chart = json.loads(pathlib.Path("mocks/pms/chart_dump_101.json").read_text())
```

Validate against CDM:

```python
from colombus.cdm.models import Patient
# adapt pid->patient_id, etc., or load via casegen DSL in colombus/casegen/dsl.py
```

## Toggle — mock vs real PMS

Env-var switch (primary `USE_MOCK_PMS_API`, aliases `USE_MOCK_DATA`, `PMS_USE_MOCKS`):

```bash
# use mocks (no VM needed)
USE_MOCK_PMS_API=true python -m colombus.web.app
USE_MOCK_PMS_API=true pytest
USE_MOCK_PMS_API=1 python -c "from colombus.service import CaseService; print(CaseService().case_ids())"

# use real filesystem cases (default)
unset USE_MOCK_PMS_API
python -m colombus.web.app
```

Truthy (case-insensitive): `true`, `1`, `yes`, `on`, `y`. Everything else = off.

Programmatic:

```python
from colombus.sources.pms_repository import should_use_mocks, create_repository, MockPmsRepository
from colombus.service import CaseService

# toggle-aware factory
repo = create_repository("auto")          # -> Mock if env ON else FileSystem
repo = create_repository("mock")          # always mock
repo = create_repository("filesystem")    # always filesystem

# CaseService respects toggle when no explicit repo
svc = CaseService()                        # auto: Mock when USE_MOCK_PMS_API=true
svc = CaseService(repository=MockPmsRepository(mocks_dir="mocks"))
```

## Full chart fixtures

`pms/chart_dump_101.json` — single crown (16, 27211) with bitewing history, perio full-mouth, one PA.
`pms/chart_dump_102.json` — 3-unit bridge (22-25, 67211+62502) with missing teeth, no perio.

Compare to real dumps: `fixtures/abeldent/fictional/5.json`, `33.json`, etc.
