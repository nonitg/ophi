# ABELDent Schema — Lab Findings

First-hand, from a live install. 2026-09-17. `[M]` = measured on the lab machine this session.

Lab: ABELDent **15.1.0** Freemium, Windows 11 Pro **ARM64** in UTM/QEMU on Apple silicon,
database `Abel_FictionalCA_20260917_013921` (the bundled Fictional Data set, `productRegion=CA`,
`PROVINCE=Ontario`). Host tooling in `lab/vm/`.

## Five findings that change the plan

1. **The database is SQL Server 2022 *LocalDB*, not SQL Express.** `[M]`
   `C:\ABELDent\localConfiguration.config` →
   `Data Source=(LOCALDB)\MSSQLLOCALDB;Initial Catalog=Abel_FictionalCA_...;Integrated Security=True`.
   `environ.ini` → `SQLSERVER=(LOCALDB)\MSSQLLOCALDB`. There is **no SQL Server service and no
   instance registry key** — LocalDB is a per-user, on-demand child process reachable only over a
   named pipe whose name is regenerated on every restart. `docs/research/integration-and-compliance.md`
   records ABELDent's published claim that "MS SQL Server Express 2022 (or 2019) is the only database
   supported"; that is true of Local/Local Plus, **not of the Freemium install**.
   **Consequences for the local agent:** no TCP/1433, no `Server=.\INSTANCE`, and the instance is
   owned by the interactive Windows user — a `LocalSystem` Windows service **cannot see it at all**.
   ABELDent ships `C:\ABELDent\Data\Tasks\installSQLExpress_SSMS.ps1`, so the supported upgrade path
   to a real Express instance exists and is vendor-authored. **Decide deliberately which the agent
   targets; the plan currently assumes Express.**

2. **There is a vendor-authored data dictionary in plaintext on disk: `C:\ABELDent\Fdats\*.fda`.** `[M]`
   For legacy table `xyz`, `xyznames.fda` is an ordered list of human field labels and
   `xyzhelps.fda` is per-field help text plus the vendor's own field identifier
   (`"Patient's surname$PATFLDS:PLNAME"`).
   **The labels map positionally onto `sys.columns` ordered by `column_id`.** Verified on `pat`
   (53 labels → columns 1–53, then 4 modern columns appended), `tdi` (17 → 1–17 + `iidentifier`),
   and `jcf` (label 23 "Needs Xrays?" → column 23 `jneedsxrays`).
   These are data files we lawfully possess. **No decompilation, so no EULA reverse-engineering
   exposure** — this is the cheap, clean substitute for the `ILSpy` path `01-ingestion.md` correctly
   refuses to take. It does **not** replace Step 5 (Extended Events): the dictionary gives names, not
   the join and filter predicates that encode business rules.

3. **Perio is a positional binary encoding, not rows.** `[M]`
   `Perio(patID, ExamNum, Date, ProvID, MAG char(64), Mobility char(32), Furcation char(96),
   Recession char(192), Pocket char(192), Bleeding_Suppuration char(192), Attachment char(192),
   DateCertified)`.
   **192 bytes = 32 teeth × 6 sites, one byte per site, value = millimetres, `0xFF` = tooth absent /
   not measured.** `Mobility` is 32 × 1, `Furcation` 32 × 3, `MAG` 32 × 2.
   Read them as `CAST(Pocket AS varbinary(192))` — as `char` they are mojibake.
   **`point_count` for the M0 exit criterion = count of bytes ≠ `0xFF`.** Decoded examples:
   patient 154 exam 1 → 174/192 sites, 1–3 mm, teeth 1/16/32 absent; patient 155 exam 1 → 144/192
   sites, 2–7 mm, three sites ≥5 mm. Decoder: `lab/tools/perio_decode.py`.

4. **Two tooth notations inside one vendor database.** `[M]`
   `Perio` byte arrays are indexed in **Universal 1–32** order (position 0 = upper right third molar;
   the absent teeth in real exams are 1/16/17/32, the four third molars). `tdi.itooth` is **FDI** —
   observed values 11, 12, 13, 16, 21, 24, 26, 36, and 36 is not a valid Universal number.
   **The evidence matcher must convert before it can join a planned crown to its perio evidence.**
   This is the notation trap `PLAN.md` names, and it is not cross-vendor — it is intra-vendor.

5. **ABELDent v15 ships an OData client and an HL7 v2 service.** `[M]`
   In `C:\ABELDent\`: `ABELSoft.Dental.ODataClient.dll`, `ABELSoft.Dental.ODataClientProxy.dll`,
   `Microsoft.Data.OData.dll`, `Microsoft.Data.Services.Client.dll`, **`HL7v2MessagingService.exe`**,
   `ABELSoft.DataSyncTransactionInsertTrigger.dll`. The database has an HL7-RIM-shaped layer:
   `ClinicalAct`, `ClinicalEntity`, `ClinicalRole`, `ClinicalParticipation`, `ClinicalPerson`,
   `ClinicalSessionData`.
   The research doc's "no public API / no HL7, no CDA, no FHIR" remains true of *published, supported,
   documented* interfaces — but an internal service interface exists. **Worth one question to
   ABELDent (800-267-ABEL) before committing to direct table reads**: an OData endpoint under a
   partner agreement would answer their own published objection to third-party DB integration.
   Unverified: whether it is reachable, versioned, or anything but Cloud-internal plumbing.

## Entity map for v1 (crowns)

| CDM entity | ABELDent | Rows in Fictional Data | Notes |
|---|---|---|---|
| Patient | `pat` | 166 | `pid`, `plname`, `pfname`, `pbirth`, `pdentist`, `pinactive`, `pnonpatient` |
| Coverage | `ixi` | 179 | `ixipid`, `ixiplanid`, `ixicertno`, `ixisubpid`, `ixireltosub`, `ixigroupno`, `ixiIsActive`, `ixiExpiryDate`, `ixileft` |
| Carrier | `ins` | — | includes **"Supports Multipage Predeterminations?"** |
| Plan coverage rules | `nsj` | 134 | `From code`/`To code`/`Percent coverage`/`Coverage Class` |
| **Planned procedure** | `tdi` where `itype IN ('P','T')` | 39 | **32 `P` + 7 `T`** |
| **Completed procedure** | `tdi` where `itype = ''` | 598 | |
| Procedure code master | `jcf` | 1354 | `jcode`, `jdesc1`, `jtoorq`, `jsurfrq`, **`jneedsxrays`** |
| Fee schedule | `xxj` | 17725 | `(Sched Year/Type, Jobcode, Fee)` |
| Perio exam | `Perio` | 55 | see finding 3 |
| Clinical notes | `Charts` (203) + `Notes` (171) | | `Notes.IsDeleted`, `IsLatest`, `IsSignedOff`, `ToothNumber` |
| Treatment plans | `Plans` | 58 | `PatID`, `PlanNum`, `Date`, `Descr`, `State` |
| **Imaging** | `AImage`, `AImageVersion`, `Imaging`, `TDIImageLink`, `Document` | **0, all of them** | see below |

### `tdi` — the Treatment Ledger, the single most important table

`tdi(ipid, itrid, idate, iitem, ijcode, itooth, isurf, idid, iresppvdr, itime, iefee, ilabfee,
iinschg, itype, iinsprt, itypecodes, imodifier, iidentifier)`

`ijcode char(5)` is the procedure code. `itooth tinyint` is FDI. `idid` vs `iresppvdr` is the
Provider / Responsible Provider split Sikka's public docs hinted at. Fees are **integer cents**
(`iefee = 58100` → $581.00).

**`itype` is the planned-vs-completed discriminator** and getting it wrong is the classic
integration bug: `''` = posted/completed, `P` = planned, `T` = 7 rows, `I` = 3 rows.
**`T` and `I` are not yet identified — resolve by diff-probe (Step 6) before any rule depends on
`itype`.** Do not assume `P` is the only planned state: patient 33's planned crown is `itype='T'`.

## Fictional Data as a fixture corpus — what it can and cannot support

**Seven patients have a planned crown (`ijcode LIKE '27%'`), with useful natural variation:** `[M]`

| pid | Patient | Planned crowns | Completed | Coverages | Perio exams | Last perio | Charts | Notes |
|---|---|---|---|---|---|---|---|---|
| 5 | WATSON, NORMA | **6** (#11,12,13,16,21,26) | 4 | 1 | 1 | 2002-04-08 | 2 | 3 |
| 6 | WATSON, CHARLES | 1 (#16) | 1 | 1 | 1 | 2004-07-13 | 2 | **0** |
| 33 | ROSCO, PATRICA | 1 (#11, `itype='T'`) | 3 | 2 | **0** | — | 2 | 2 |
| 56 | PROVOST, JOHN | 1 (#26) | 22 | 1 | 2 | 2005-12-14 | 7 | 11 |
| 158 | YOKOYAMA, SUMI | 1 (#24) | 26 | 1 | 2 | 2005-12-14 | 7 | 13 |
| 162 | RANDAL, KRIS | 1 (#26) | 26 | 1 | 2 | 2006-12-14 | 6 | 9 |
| 165 | MILLER, BOB | 1 (#36) | 31 | 1 | 3 | 2006-12-14 | 6 | 8 |

Codes present: `27211` (porcelain/ceramic fused to metal crown) and `27215`.
Ready-made cases: **33** = crown planned with *no perio chart at all*; **6** = perio but *zero notes*;
**5** = six crowns against a 2002 perio exam; **56/158/162/165** = the rich "complete" cases.

**Three limits to plan around:**

- **Zero radiographs, zero documents, zero image links.** `AImage`, `AImageVersion`, `AImageChartAssociation`,
  `Imaging`, `TDIImageLink`, `Document` are all empty. `[M]` This is **PLAN.md risk #6 and #7
  landing at once**. Note the distinction this forces: *"this patient has no radiograph"* and *"this
  driver cannot see radiographs"* are different conclusions, and `SourceAssurance` exists precisely
  for this. **Open question for M0:** is the table empty because Fictional Data ships no image files,
  or because pixel data and its metadata live entirely with the imaging vendor? Until that is
  answered, the imaging spike cannot be called done, and **the manual-upload fallback is load-bearing,
  not a fallback.**
- **`jneedsxrays` exists but is unpopulated for crown codes** (`27201/27205/27211/27215` all blank). `[M]`
  A vendor-supplied "this code needs radiographs" flag would have been useful. It is not usable
  as-is; do not build a rule on it without checking a maintained install.
- **Every date is 2002–2007.** CDCP began in 2024, so every recency rule (`<= 365 days`) fails against
  today for structural reasons, not clinical ones. The corpus tests *plumbing*, not *verdicts*.
  Either shift dates in `casegen` or make the eval harness evaluate relative to a per-case `as_of`
  date. **Prefer `as_of` — mutating vendor data in the lab breaks the "we never write" rule.**

## Access notes for the local agent

- LocalDB is reachable only as the owning interactive user, over
  `np:\\.\pipe\LOCALDB#XXXXXXXX\tsql\query`, resolved per-call via
  `"%ProgramFiles%\Microsoft SQL Server\160\Tools\Binn\SqlLocalDB.exe" info MSSQLLocalDB`.
  The pipe name changes on every instance restart, so it must never be cached.
- **ARM64 caveat, lab-only:** LocalDB ships only an x64 `SQLUserInstance.dll`, so an ARM64-native
  process cannot resolve the `(localdb)\X` moniker at all —
  *"error: 56 - Unable to load the SQLUserInstance.dll"*. Connecting to the named pipe bypasses the
  shim. **This is an artifact of the ARM lab VM and must not shape the shipped `win-x64` agent.**
- `Perio` and `Charts` both carry `DateCertified`; `Notes` carries `IsSignedOff`, `IsLatest`,
  `IsDeleted`. **Any evidence query must filter on these** or it will cite retracted or superseded
  chart entries as evidence — an audit problem, not a cosmetic one.
- No `MS_Description` extended properties anywhere (0 rows) — the `.fda` files are the only
  documentation that exists.
- 454 tables, 93 views, 248 procedures, 19 functions, 147 declared FKs, 5927 columns. `[M]`
  `sys.sql_modules` (341 modules) is unexamined and is the next highest-yield target — per
  `01-ingestion.md` Step 1, a vendor view or proc is the closest thing to a supported contract.

## M0 artifact — `lab/tools/chart_dump.py` `[M]`

One command, zero manual steps, ~25 s: every patient with planned work → `fixtures/abeldent/fictional/<pid>.json`
with patient, coverage, planned/completed procedures, decoded perio, clinical notes, imaging, each
section carrying a `source_assurance` (`present` / `none_recorded` / `indeterminate`).
**14 patients have planned work, not the ≥20 the M0 exit asks for.** The other 6 come from the
Step 6 probe catalogue (enter plans through the UI); that is fixture authoring, not a blocker.

Findings from building it:

- **Clinical notes live in `Notes`, not `Charts`.** `Charts(patID, ChartNum, Date, DateClosed,
  DateCertified, ChartDesc)` is a per-visit header; `Notes.KeyType=1` + `KeyNumber` joins to
  `Charts.ChartNum` (163/171 rows). `NoteType 1` = free-text visit note, `NoteType 3` = procedure
  note carrying `ToothNumber` (78 rows), `NoteType 2` (`KeyType 2`) = treatment-plan note (2 rows).
  `RefNumber` does **not** join `tdi.itrid` (1/88 coincidental). `IsSignedOff` is NULL throughout;
  `IsDeleted`/`IsLatest` are populated and must be filtered.
- **`Notes.ToothNumber` is FDI**, like `tdi.itooth`: patient 56 has core+post on #14 (2005-06-08)
  and "Insert Notes … Margins very good" on #14 two weeks later. Only `Perio` is Universal.
- **Perio position→tooth mapping cross-checked against the ledger.** Patient 5's `0xFF` teeth decode
  to FDI 23 and 24; her plan has pontics (62502) at exactly 23 and 24. The Universal-order inference
  in finding 4 is now corroborated, not just inferred.
- **`Perio` is not always a full exam.** Patient 6's only exam has **1 point of 192**. The dump
  classifies `extent` as `full_mouth` (≥150) / `partial` (≥24) / `spot_check`; thresholds are
  placeholders for the SME to set.
- **Planned rows use sentinel transaction ids**: `itype='P'` → `itrid=99999998`, `itype='T'` →
  `99999999`. `I` rows (3, patient 9) have real itrids on same-day exam/scale/polish. `T` and `I`
  still unresolved; the dump labels them `planned_unverified_T` / `unverified_I`.
- **Insurance chain:** `ixi.ixiplanid` → `nsp.nid` (plan: `nplanname`, `nplnno`, `ninscoid`) →
  `ins.inscoid` (carrier). **Dependants have a blank `ixiplanid` and point at the subscriber via
  `ixisubpid`**; the plan is on the subscriber's own `ixi` row. The dump resolves and flags this as
  `inherited_from_subscriber`. Sun Life is `ins.inscoid='SUNLIFE'`, plan `SU254221`.
- **Imaging: Fictional Data *had* images.** `AImageToothNumber` holds 9 rows (FDI teeth) pointing at
  `ImageID`s that no longer exist in `AImage`. `AImageType` vocabulary: Radiographic, Panoramic,
  Cephalametric, Intraoral, CR, Template, Portrait, Digital Camera — no periapical/bitewing split at
  the type level. Images were stripped from the dataset; this does not settle whether a live install
  keeps pixel metadata in `AImage`/`AImageVersion.FileName` (the schema says yes). Imaging spike still
  open; dump reports `indeterminate`.
- Every `Perio.DateCertified` and `Charts.DateCertified` (bar one) is NULL in Fictional Data, so
  certification filters cannot be tested against this corpus.

## Still unverified

- `tdi.itype` values `T` and `I`.
- Whether `Perio` position 0 is tooth 1 in Universal order or a fixed slot that happens to align.
  The third-molar inference is strong but is inference; confirm by entering a known exam through
  the UI and diffing (Step 6).
- Whether the OData/HL7 surfaces are reachable, and on which editions.
- Whether a live install populates `AImage`/`AImageVersion` (Fictional Data ships images stripped).
- The EULA text. `C:\ABELDent\abeladvantage.chm` (48 MB) is on the box and unread.
  **This is still week-1 action #3 and it is still open.**
