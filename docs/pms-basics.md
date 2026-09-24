# How a PMS works — the mental model

A dental PMS is four systems that share a patient ID and pretend to be one app. Learn the four and ABELDent stops being mysterious.

1. The schedule. Chairs × time. Appointments carry a patient, a provider, a duration, and a planned procedure. This drives the front desk, not the clinical record.

2. The chart (clinical). Three separate stores that people lump together:
- Odontogram — per-tooth, per-surface state. Tooth #46, mesial-occlusal, existing amalgam. Teeth are numbered; Canada uses FDI (11–48), US notation (1–32) leaks in, and the mismatch is a top-5 source of silent wrong answers. It is not only a cross-vendor problem: ABELDent carries both notations inside one database — `Perio` byte arrays are Universal 1–32 while `tdi.itooth` and `Notes.ToothNumber` are FDI (`docs/research/abeldent-schema.md` finding 4).
- Perio chart — 6 measurements per tooth (pocket depth at 6 sites), plus recession, bleeding, furcation, mobility. 32 teeth × 6 = 192 points for a full-mouth exam. "Point count" in the M0 exit criterion means exactly this: did the hygienist record 192 points or 12? ABELDent encodes each of those arrays positionally, one byte per site, `0xFF` for absent — so point count is the number of non-`0xFF` bytes. A CDCP crown rule that wants perio evidence needs to know the difference between a full exam and a spot check.
- Clinical notes — free text, sometimes templated. This is where the justification for a crown actually lives, in prose, unstructured.

3. The ledger. Every procedure has two lives: planned (treatment plan, not done, no money) and completed (done, billable, dated). Same procedure code, different table or different status flag. Getting this wrong is the classic integration bug — you report a crown as completed when it's only proposed. ABELDent calls these the Treatment Ledger and the Financial Ledger, and it distinguishes Provider from Responsible Provider — a second trap: who did it vs. who owns the patient. The split is not planned-vs-completed: both lives appear in the clinical chart ledger (`Transactions`), and only some planned items are mirrored into the financial ledger (`tdi`) for the fee estimate. Reading planned work from `tdi` alone under-reads it by half.

4. Insurance. A patient has one or more coverages (carrier, policy, group, certificate, relationship to subscriber). A claim says "this was done, pay me." A predetermination (= preauthorization) says "I intend to do this, will you pay?" — same message format, different transaction code, no money moves. That is the entire product surface: the predetermination path.

Why preauth is painful, concretely. The procedure code (27xxx = crown) is structured. The tooth is structured. But the evidence CDCP wants — a periapical radiograph from within 12 months, a perio chart, a note explaining why a filling won't hold — lives in three different subsystems, in three different formats, one of which is prose and one of which is a JPEG owned by a separate imaging vendor. A human opens four screens and eyeballs dates. That manual cross-subsystem join is what Ophi automates.

Three of the CDCP crown criteria — crown-to-root ratio, margin-to-crest distance, ferrule height — are not fields in any PMS. They're measurements a dentist makes by looking at the film, and no amount of database reading produces them. A fourth, furcation involvement, *is* charted (ABELDent keeps `Perio.Furcation`, 32 teeth x 3 roots), but CDCP asks for it radiographically, so the probed value may not be the same assertion. Hence the Clinician Assertions block.

## Toggling real vs mock PMS data

The app reads through `PmsRepository` (`ophi/sources/pms_repository.py`). `CaseService`
uses it for `case_ids()` / `base_case()`; pass a `repository` explicitly or let the env toggle
decide:

```bash
# Real / filesystem (default) — reads cases/demo/*.yaml
make demo              # or: scripts/demo-real.sh
unset USE_MOCK_PMS_API; make demo

# Mock / dummy — reads mocks/*.json + mocks/pms/*.json, no VM
USE_MOCK_PMS_API=true make demo   # or: scripts/demo-mock.sh
```

Env var: `USE_MOCK_PMS_API` (primary), aliases `USE_MOCK_DATA` / `PMS_USE_MOCKS`.
Truthy (case-insensitive): `true`, `1`, `yes`, `on`, `y`; anything else = off.
Programmatic: `create_repository("auto")` (env-aware), `create_repository("mock")`,
`create_repository("filesystem")`, and `should_use_mocks()` / `is_mock_enabled()`.
Fixtures: `mocks/README.md` maps each JSON file to its PMS table and CDM type.