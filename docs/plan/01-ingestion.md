# Ingestion Layer Plan

v0.1 · 2026-09-17 · target: clinic-usable by 2026-12-15

## Three decisions that drive everything else

1. **Demand-driven extraction, not continuous replication.** The cloud never holds a clinic's chart
   database. It asks the on-prem agent for *one patient's scoped bundle* when a named human starts a
   preauth. Biggest single lever on breach blast radius, on SQL Express load, and on shipping speed.
2. **The schema map is a data artifact, not code.** Reverse-engineering output lands in versioned
   YAML + a signed query pack, gated at runtime by a schema fingerprint. When ABELDent v15.3 moves a
   column we fail closed with a precise diagnostic and ship a new pack — not a new binary.
3. **`IChartSource` is the product.** ABELDent is the first driver, not the architecture. If Sikka,
   ClearDent or Open Dental becomes the right answer in month 5, that is a 2–3 week driver, not a
   rewrite.

## 1. Schema discovery

**Rule zero: all discovery on the lab machine, against Fictional Data, on a restored copy.** Restore
`C:\ABELDent\Data\Backup\*.bak` into a second SQL Express instance (`.\COLOMBUSLAB`) so scans and
lock experiments cannot degrade the app's working database. Keep the original for "run the app,
observe what it does" work. All probe artifacts live in a separate `ColombusProbe` database.
**We never create an object inside the vendor database** — not a view, not a proc, not an index.

### Step 0 — Non-SQL recon (2 days). Highest yield per hour; most teams skip it.
- Inventory `C:\ABELDent\**` for `*.sql`, `*.rdl`, `*.rpt`, `*.xsd`, `*.edmx`, `*.dbml`, `*.config`,
  `*.chm`. Apps of this vintage routinely ship schema-creation scripts and report definitions.
  **Crystal `.rpt` / SSRS `.rdl` files embed the exact SQL the vendor uses** — a free, vendor-authored
  semantic layer over Treatment Ledger and Financial Ledger.
- Read `integrationsettings.ini` and imaging bridge config for filesystem paths.
- Extract connection strings from `*.config` (instance name, DB name, connection options).
- String-scan (not decompile) assemblies for SQL fragments and table names.
- **LEGAL FLAG:** full IL decompilation (ILSpy/dnSpy) of `ABELSoft.*.dll` would be high yield but
  likely violates the EULA's reverse-engineering clause. **Do not decompile until counsel signs off.**
  String-scanning files we lawfully possess is weaker exposure but still route past counsel. Plan
  assuming decompilation is unavailable.

### Step 1 — Catalog extraction (2 days)
`sys.tables/columns/types/indexes/index_columns/key_constraints/foreign_keys/check_constraints/
default_constraints`. **`sys.sql_modules` is the jackpot** — dump every view/proc/function. If the
R&A/Power BI add-on has a sanctioned read path it is almost certainly views or procs here; prefer
them over base tables forever (closest thing to a vendor contract). Also `sys.extended_properties`
for `MS_Description`. Look for a self-describing dictionary table (`SysFields`, `TableDefs`,
`CodeTable`).
Tooling: `mssql-scripter`, `dbatools` PowerShell, SchemaCrawler/SchemaSpy for a browsable FK graph.

### Step 2 — Profiling (2 days)
Row counts from `sys.dm_db_partition_stats` (instant, no scan). Per-column null ratio, distinct
count, min/max, top-20 values, sample. Output a ranked table list: **the 30–60 tables holding >=95%
of rows are the real schema**; the rest are lookups, config and dead weight. Date-column inventory
feeds both incremental sync and radiograph capture dates.

### Step 3 — Relationship inference (3 days)
Assume declared FKs are sparse. `probe infer-fks`: for every type-compatible column pair with name
similarity (`PatientID` / `PatID` / `PatientNo`), test inclusion dependency
(`SELECT TOP 1 a.col FROM A a WHERE NOT EXISTS (SELECT 1 FROM B b WHERE b.col = a.col)`). Empty
result + reasonable cardinality = candidate FK. Rank by coverage, distinctness, name similarity.

### Step 4 — Value hunt (2 days). Fastest screen-to-column mapping.
`probe find-value "<literal>"` — generated UNION over every text/int/date column, returning
`(table, column, pk)`. Feed it values visible in the UI on Fictional Data: a surname, a policy
number, procedure code `21221`, a tooth number, a note phrase. Locates the patient table, treatment
ledger, note store and coverage records within an hour.

### Step 5 — Capture the app's own queries with Extended Events (3 days). Highest fidelity.
Identify the app's connection signature via `sys.dm_exec_sessions`. Create an XEvent session (file
target) on `rpc_completed` + `sql_batch_completed`, filtered on `client_app_name`, collecting
`sql_text`, `statement`, `duration`, `logical_reads`, `session_id`. **Use Extended Events, not SQL
Profiler** (deprecated, higher overhead; XEvents fully supported on Express).
**Screen-walk protocol:** one engineer drives the UI through a scripted screen list (patient -> chart
-> treatment plan -> perio -> notes -> imaging -> ledger), marking timestamps. Correlate to captured
batches. Output: **screen -> exact vendor SQL** — including the joins and filter predicates that
encode business rules we would otherwise get wrong (voided entries, status flags, provider vs
responsible provider, Summarized vs Production Totals).

### Step 6 — Diff-after-action probes (5 days, ongoing)
`probe snapshot`: per table, `SELECT <pk>, HASHBYTES('SHA2_256', CONCAT_WS('|', <all cols>))` into
`ColombusProbe`. Fast pre-pass: row count + `CHECKSUM_AGG(BINARY_CHECKSUM(*))` per table to find
changed tables, then row-level hash only on those.
Protocol: write a YAML describing the action -> `probe snapshot A` -> perform the action in the UI ->
`probe snapshot B` -> `probe diff A B` -> record mapping with the probe ID as evidence.
**Probe catalogue (minimum):** add patient; add CDCP coverage; plan a procedure with tooth+surface;
complete it; void it; enter a full-mouth 6-site perio chart; enter a partial perio chart; enter PSR;
write a clinical note; mark a tooth missing; attach a document; acquire/link a radiograph via the
imaging bridge; create a referral letter.
**This catalogue is also the fixture-authoring workstream** — Fictional Data may be sparse, so every
probe both maps schema and manufactures test data.

### Step 7 — Consolidate (3 days)
- `/schema-map/abeldent/v14/entities.yaml` — CDM entity -> table/column mappings, per-field
  provenance (`evidence: [xe-0042, probe-0117]`), confidence
- `/agent/.../QueryPacks/abeldent-v14.yaml` — named, parameterized SELECTs
- `/fixtures/abeldent/fictional/*.json` — raw rows + expected CDM output, the CI golden set
- `schema-fingerprint.json` — SHA-256 over sorted `(schema, table, column, type, nullability)` of
  **only the mapped objects**, plus vendor version string

**Effort: 4.5 eng-weeks to a mapped core** (patient, coverage, planned/completed procedures, notes,
odontogram); **+2.5 eng-weeks for perio and imaging** — the hard ones.

**Tooling:** SSMS 21 + Azure Data Studio, `dbatools`, `mssql-scripter`, SchemaCrawler/SchemaSpy,
Extended Events, `sp_WhoIsActive` (in `ColombusProbe`, never the vendor DB), our own `probe` CLI
(C#, same solution as the agent — reuses `ReadOnlySqlExecutor` so the safety rails get tested in the
lab first), `fo-dicom`, git-versioned YAML.

## 2. Local agent

### Runtime: C# / .NET 10 LTS, single-file self-contained `win-x64`
1. **Windows auth is the only supported SQL auth.** `Microsoft.Data.SqlClient` with
   `Integrated Security=SSPI` is first-class; SSPI/Kerberos/NTLM edge cases (workgroup vs domain,
   SPN, delegation) are best documented here. Other stacks can do it, but you burn days at the exact
   moment a clinic's IT is on the phone.
2. **Shipping to non-technical clinics.** Windows Service hosting, MSI via **WiX v5**, Authenticode
   signing, Windows Event Log, DPAPI/CNG key storage, service-account provisioning — all native.
   Self-contained publish means zero "install a runtime" support calls.
3. **Same ecosystem as the PMS** if we ever need COM/interop.

Rejected: Python + pyodbc (packaging a service + installer + self-update for non-technical Windows
sites is the whole job); Go (great binary, weaker DPAPI/CNG/MSI/service story). **Cloud stays
Python/TypeScript — the contract between them is JSON over HTTPS, not a shared runtime.**

Libraries: `Microsoft.Data.SqlClient`, **Dapper** (hand-written SQL against a foreign schema — never
EF Core), `Polly`, `Serilog` + `OpenTelemetry`, `Microsoft.Data.Sqlite`,
`System.Threading.Channels`, `fo-dicom`, `SixLabors.ImageSharp`, `QuestPDF`, WiX v5.

### SQL authentication
Service runs as a **dedicated Windows account** (`svc_colombus`), never LocalSystem, never a human's
account. Installer supports: (a) local machine account with a 32-char random password handed to
SCM's LSA secret store — never written to config or log; (b) existing domain account; (c) **gMSA** on
domain-joined servers (best; no password at all).

SQL side, via a human-readable `grant-colombus.sql` the clinic's IT runs under sysadmin (**we never
demand sysadmin ourselves**):
```sql
CREATE LOGIN [DOMAIN\svc_colombus] FROM WINDOWS;
CREATE USER ...; CREATE ROLE colombus_reader;
-- GRANT SELECT on an ENUMERATED object list only, never db_datareader.
-- The object list is generated from the query pack, so privilege == the footprint of shipped queries.
DENY INSERT, UPDATE, DELETE, ALTER, EXECUTE, CREATE TABLE ... TO [DOMAIN\svc_colombus];
```
Connection string: `Encrypt=True; TrustServerCertificate=<configurable>; ApplicationName=Colombus
Agent; ApplicationIntent=ReadOnly`.

### Read-only enforcement — three independent layers
1. **SQL permissions.** The database itself refuses writes.
2. **`ReadOnlySqlExecutor`** — the only class allowed to touch `SqlConnection`. Accepts a `QueryId` +
   typed parameters, **never a SQL string from any caller.** Sets per connection
   `SET TRANSACTION ISOLATION LEVEL READ COMMITTED; SET LOCK_TIMEOUT 5000; SET DEADLOCK_PRIORITY LOW;`
   plus `CommandTimeout`, `MAXDOP 1`, row cap. A unit test asserts no other type in the solution
   references `SqlCommand`.
3. **Signed QueryPack.** All SQL ships as a version-pinned, signed YAML. Loaded queries validated at
   startup (single statement, starts with `SELECT`/`WITH`, no `;`, no forbidden tokens) and
   hash-checked. **The cloud can only invoke a query ID with typed parameters — it can never send
   SQL.** If the cloud is fully compromised the attacker gets "read patient 4711's perio exams,"
   rate-limited and journaled, not `SELECT * FROM everything`.

Default **READ COMMITTED** with short, keyset-paginated, index-aligned queries and a low lock timeout
so we yield rather than block the clinic's app. `READ UNCOMMITTED` permitted **only** for the backfill
sweep, explicitly flagged, never for a fact that appears in a submitted packet.

### Incremental sync + change detection without triggers

We do **not** enable Change Tracking or CDC. CT requires `ALTER DATABASE` on the vendor DB (modifies
vendor state, voids our "we only read" claim); **CDC is unusable on Express anyway — it depends on
SQL Server Agent, which Express does not ship.** Keep CT as an ask in the ABELDent partnership talk.

Per-table strategy, recorded in `entities.yaml`:

| Strategy | When | Mechanism |
|---|---|---|
| `RowVersion` | has a `rowversion`/`timestamp` column | watermark on `MIN_ACTIVE_ROWVERSION()`; exact, cheap, no missed rows |
| `ModifiedTimestamp` | has a maintained `DateChanged` column | watermark with a 48h overlap window for clock skew |
| `IdentityHighWater` | append-only ledgers | `WHERE Id > @cursor` |
| `HashSweep` | mutable, no usable marker | rolling per-key-range row-hash comparison, fully swept every 24h in slices |
| `SnapshotSmall` | lookup/config tables (<50k rows) | full re-read nightly |

**Deletes are invisible without triggers.** Handle by: `HashSweep` detects disappearances within one
cycle; every CDM bundle carries `asOf` and a `freshness` budget — a bundle past budget is refetched
before packet assembly, never reused. **We never claim "this is current" from cache.**

**Two sync tiers:**
- **Tier A — hot index** (continuous, tiny, non-clinical): patient key + local chart number and
  nothing else identifying stored in the cloud, plus a change feed of "treatment plans touched in the
  last N days" for the worklist. Default 15 min poll.
- **Tier B — on-demand bundle** (the real ingestion): cloud dispatches
  `BuildBundle(patientRef, proposedTreatmentRef, reason, requestedByUserId)`; agent runs ~12
  query-pack queries, maps to CDM, returns one signed JSON bundle. **Target p95 < 8 s on SQL Express.**

**Throttling for SQL Express** (1410 MB buffer pool, 4 cores, shared with the PMS): global
concurrency 1 for Tier B and 1 for sweeps; sweeps pause when instance CPU > 60% or when an ABELDent
session has been blocked by us (via `sys.dm_exec_requests` blocking chain); configurable quiet hours,
default sweeps only 19:00–06:00 local.

### Images and documents
The DB almost certainly stores *references*, not pixels. `DocumentLocator` resolves a DB row to a
path (local, UNC, or imaging-vendor-managed) and returns **metadata only** by default: existence,
byte size, SHA-256, MIME/format, dimensions, filesystem times, and the **capture date** —
cross-checked from DB column vs DICOM `StudyDate (0008,0020)`/`ContentDate` vs file mtime, **with the
source of the date recorded.** The 12-month recency test is the core of the product, so the date's
provenance must be auditable and we must **report disagreement rather than silently pick one.**

**TOP UNKNOWN:** radiographs may live entirely in a third-party imaging system (the ABELDent bridge
is outbound launch-with-context, so pixel data is likely not ABELDent's). Budget a dedicated
**imaging discovery spike (1 eng-week, week 2)**; design a second interface `IImagingSource` with
per-vendor drivers. **Manual upload via the cloud UI is the always-available fallback and must exist
in v1 regardless.**

Bytes move only on explicit user action. When they move: normalize locally (DICOM -> lossless PNG via
fo-dicom + ImageSharp, strip non-essential tags, retain modality/date/laterality), chunked resumable
upload, client-side encryption.

### Offline / retry
Local SQLite (`%ProgramData%\Colombus\agent.db`, ACL'd to the service account): `sync_cursor`, `job`,
`outbox`, `access_journal`, `schema_fingerprint`, `document_ref`, `config`. Durable job state machine
with idempotency keys. Polly exponential backoff with jitter, circuit breaker, max retention 7 days
then abandon with alert. Bounded disk (2 GB default), oldest-first eviction. **When offline the cloud
UI shows "clinic agent unreachable, last seen HH:MM" rather than stale data presented as fresh.**

### Transport and enrolment
**Outbound HTTPS 443 only. No inbound listener, no firewall rule, no port forward** — this is both
the security posture and the sales pitch, and it directly answers ABELDent's "third-party
integrations are a security risk" objection. Job dispatch via long-poll or SignalR-over-WebSocket.
Enrolment: one-time code -> agent generates a non-exportable key in **Windows CNG machine key store**
-> CSR -> per-device certificate; thereafter mTLS + short-lived JWT. Revocation server-side, instant.

### Self-update
Two components: `Colombus.Agent` (service) and `Colombus.Bootstrap` (tiny updater that owns swapping
the agent). Signed packages from a Canadian-hosted CDN; Authenticode via Azure Trusted Signing
(alternative: OV/EV cert on hardware token, ~$400–800/yr). Staged rings
`internal -> canary(1 clinic) -> 10% -> all`, per-clinic version pinning, automatic rollback on
post-update health-check failure. **Query packs and schema maps update independently of binaries** —
the common case (vendor moved a column) is a data push, not a deployment.

### Observability
- **`SchemaGuard`**: on startup and daily, recompute the fingerprint over mapped objects; on mismatch
  emit a diff (`column X removed`, `type changed`), **fail closed for affected entities only**, alert
  us, surface a specific banner in the clinic UI. Direct mitigation for "vulnerable to breaking
  anytime the PMS is updated" — converts a silent-wrong-answer failure into a loud, diagnosable one.
- Serilog -> rolling local file + Windows Event Log with a **mandatory redaction sink**. A CI test
  feeds known PHI patterns (Fictional Data names, DOB, policy-number shapes) through the logging
  pipeline and **fails the build if any survives.** Log row counts, query IDs, durations, opaque IDs
  — never PHI.
- OpenTelemetry -> Canadian-hosted collector. Metrics: `bundle_build_duration`,
  `query_duration{query_id}`, `rows_returned{query_id}`, `sql_blocked_events`, `sweep_lag_seconds`,
  `schema_fingerprint_status`, `outbox_depth`, `agent_heartbeat`.
- `colombusctl` on-site CLI: `status`, `test-sql`, `fingerprint`, `diag-bundle` (redacted),
  `replay-job <id>`.
- **`access_journal`**: every read the cloud causes, recorded locally with
  `(timestamp, cloud user id, patient ref, query ids, reason)`, exportable by the clinic.
  Clinic-readable audit is a PHIPA accountability asset and lives on **their** server where we cannot
  quietly alter it.

## 3. Canonical data model — CDM v1

**Source of truth: JSON Schema 2020-12 in `/contracts/cdm/v1/`.** Generate C# records
(NJsonSchema), Python Pydantic (datamodel-code-generator), TypeScript (json-schema-to-typescript) in
CI. JSON over Protobuf because the downstream consumer is an LLM reasoning pipeline plus a web UI —
human-readable payloads beat wire efficiency at our volumes, and JSON Schema doubles as validator and
prompt-shaping documentation.

**Take from FHIR R4:** resource names and shapes — `Patient`, `Coverage`, `Practitioner`,
`Organization`, `Condition`, `Procedure`, `ServiceRequest`, `Observation`, `DocumentReference`,
`ImagingStudy` — plus `Coding{system, code, display}`, `CodeableConcept`, `Reference`, `Period`,
`Identifier`, `Quantity`, and FHIR's `status` vocabularies. A future FHIR facade becomes a mapping
exercise, and new engineers arrive pre-trained on the vocabulary.

**Deliberately drop:** conformance, profiles, `Bundle`, search parameters, the REST API, XML,
contained resources, the extension mechanism. **Polymorphic `value[x]`** -> explicit typed fields
(`valueQuantity`, `valueCode`); LLM pipelines and generated types both hate it. **FHIR's
everything-is-optional cardinality** -> mark fields required and non-null where the domain requires
it; a preauth engine must not silently treat "absent" as "zero."

**FHIR's dental weakness is the deliberate divergence.** R4 has no first-class periodontal charting
resource and its tooth/surface value sets don't align with Canadian practice. **`PerioExam` and
`DentitionState` are first-class CDM entities, not piles of `Observation`s.** Perio
recency/completeness is a core CDCP test; modelling it as 192 loose Observations would make the rules
engine miserable.

| CDM entity | FHIR analogue | Notes |
|---|---|---|
| `Patient` | Patient | name, DOB, sex, identifiers; **`cdcp`: member/client identifier, eligibility dates** |
| `Coverage` | Coverage | payer=CDCP, member id, coverage period, co-pay tier if present |
| `Practitioner` / `Organization` | same | provider identifiers, CDA/provincial licence number |
| `PlannedProcedure` | ServiceRequest | **the proposed treatment**: USC&LS code, tooth (ISO 3950), surfaces, quadrant/sextant/arch, provider, planned date, status, fee |
| `CompletedProcedure` | Procedure | same + performed date, performer, void/reversal flags |
| `DentitionState` | Observation-ish | per-tooth: present / missing / unerupted / implant / pontic / restored surfaces — the odontogram |
| `PerioExam` | Observation-ish | date, examiner, `completeness: FullMouth \| Partial \| Screening`; per-tooth 6-site `ProbingDepth` + `RecessionGingivalMargin` + `BleedingOnProbing` + `Furcation` + `Mobility`; separate `PsrScores` by sextant |
| `ClinicalNote` | DocumentReference | date, author, type, plain text, source row ref |
| `ImagingRecord` | ImagingStudy + Media | `modality: Periapical \| Bitewing \| Panoramic \| CBCT \| Photo \| Other`, tooth/region, **`captureDate` + `captureDateSource`**, dimensions, hash, `bytesAvailable`, `bytesLocation` (never bytes inline) |
| `ReferralDocument` | DocumentReference | direction, date, correspondent, file ref |

### Two cross-cutting elements that matter more than the entity list

**1. `Provenance` on every record (required).**
```
provenance: { sourceSystem, sourceVersion, sourceTable, sourceRowKey,
              queryId, queryPackVersion, extractedAt, agentVersion }
```
A preauth is an assertion to a payer. Every fact we assert must be traceable to a row, an extraction
moment, and the exact query that produced it. Non-negotiable — it is what lets us defend an assembled
packet, debug a mis-mapping, and satisfy an auditor.

**2. `SourceAssurance` on every section (required).**
```
availability: Present | AbsentConfirmed | Unknown | Degraded
```
**"This patient has no perio chart" and "this driver cannot see perio charts" are opposite clinical
conclusions.** Open Dental exposes `perioexam`/`periomeasure`; ClearDent and Sikka may not; our
ABELDent driver may not on day one. Without this the rules engine will confidently fabricate a
"missing documentation" flag. Every driver declares capabilities; every bundle section reports which
of the four states applies, with a reason code.

**Code systems:** canonical tooth numbering **ISO 3950 / FDI two-digit** (Canadian practice) with
Universal Numbering translation retained; surfaces as enumerated `M|O|D|B|L|I|F`; procedure codes as
`Coding{system:"urn:colombus:codesystem:cda-uscls", code}`. **Always retain
`sourceCode`/`sourceSystem` alongside the normalized code — never discard the PMS's own value.**

**USC&LS licensing:** the code set loads from a runtime data file
(`/codesystems/uscls.<version>.csv`), never compiled in, behind a feature flag with a
`codes-only, no-descriptions` degraded mode. Until the licence lands we ship codes-only and the UI
renders the clinic's own description text from the PMS. **Gating risk for GA, not for the pilot.**

**Effort: 5 eng-weeks. This is the durable asset — do not under-fund it.**

## 4. Data minimization at the edge

Three tiers, enforced by architecture rather than policy.

**Tier 0 — never leaves the clinic.** The database connection, raw rows, unmapped tables, the
financial ledger, other patients' records, and **radiograph pixel data by default.** The agent's own
store holds cursors, hashes, job state and the access journal — **it does not persist clinical
payloads.** Bundles assemble in memory into an encrypted, TTL'd job workspace and are discarded.
**We refuse to make the agent a second PHI database.**

**Tier 1 — patient search stays local.** The cloud does **not** hold a patient roster. A user types a
name; the cloud relays the term to the agent; the agent returns matches for display; nothing is
persisted cloud-side. Cost: search requires the agent online (acceptable — so does everything else).
Benefit: **a cloud breach does not yield "every patient at every clinic."**

**Tier 2 — scoped bundle, on demand, TTL'd.** One patient + one proposed treatment, pulled only when
a named clinic user starts a preauth with a recorded reason. Field-level minimization at the driver:
**no financial ledger, no payment history, no SIN, no email/phone**, address only if CDCP identity
matching requires it, only procedure history relevant to the CDCP "relevant completed and pending
treatment needs" rule. Encrypted at rest with a per-clinic DEK under envelope encryption in a
Canadian-region KMS. Auto-purge **30 days after packet export** by default, configurable to 0.

**Radiographs.** Metadata-only by default — and **metadata alone answers the 12-month recency test,
which is the majority of the product's value.** Pixel bytes transfer only on explicit per-image user
action during packet assembly, normalized and tag-stripped locally, client-side encrypted, uploaded
to Canadian object storage, deleted on packet completion.
**v1.1 target: render the packet PDF on the agent (QuestPDF) so image bytes never leave the clinic at
all.** Design v1 so this is a renderer swap, not a re-architecture.

**The breach answer, stated plainly:**
> A full compromise of our Canadian cloud yields, at most, <=30 days of single-patient preauth
> bundles for patients a clinic user explicitly initiated, encrypted per-clinic. It does not yield any
> clinic's chart database, any patient roster, or any radiograph not manually attached. Our credential
> on the clinic's database is read-only, restricted to an enumerated list of tables, and cannot execute
> SQL we did not ship and sign. Every read is journaled on the clinic's own server where we cannot
> alter it. We have no inbound network path into any clinic.

**Legal:** under Ontario PHIPA we are most likely an agent/electronic service provider of the
custodian; requires a written agreement, breach-notification terms, and likely a PIA.
**Start the legal workstream in week 2, not week 10.**

## 5. Build vs buy: Sikka

**Call: BUILD the direct reader for v1. Do not buy Sikka.** Run a one-week time-boxed diligence
spike in parallel. **Decision deadline 2026-10-15.**

Why build wins today:
- **US data residency with no SOC 2 or HIPAA claim in their own FAQ** is close to disqualifying for a
  Canadian dental privacy conversation and contradicts our Canadian-hosting commitment. Probably
  decisive on its own.
- **2:00 AM refresh is architecturally wrong.** The workflow is "dentist proposes treatment now,
  clinic wants the packet now."
- **Unknown perio / notes / radiograph coverage, X-rays confirmed Platinum-tier only.** Four of our
  eight required data categories are at risk — and they are exactly the hard, differentiating ones.
- **We cannot develop against it today.** No pilot clinic; Freemium/v15 support unknown. Choosing
  Sikka blocks the whole team on an external dependency for the first month of a three-month runway.
- **Unit economics.** ~US$350/mo + $35–175/mo per location before writeback, against small Canadian
  clinics, is a margin problem at pilot scale and a pricing-page problem at sales scale.

**Where Sikka could still win:** a credible *breadth* play for PMS #4–#10 once we have a working
product and a customer pulling us there. Keep `SikkaChartSource` as a named, un-built driver.

**Diligence questions (send now):** Freemium and v15/Cloud support? Does the schema expose 6-site
perio measurements and PSR? Clinical note free text? Radiograph capture date and file retrieval, at
which tier and price? Any Canadian data-residency option, contractual or roadmapped? SOC 2 Type II
status/date? Minimum refresh interval and any on-demand pull? Contractual position on PHIPA/PIPEDA
and sub-processor terms?

**Decision criteria — any single fail means do not buy for the Canadian core product:**

| Criterion | Pass threshold |
|---|---|
| Data residency | Canadian region available contractually within 6 months |
| Clinical coverage | Perio 6-site + PSR + notes + radiograph capture date, all available |
| Freshness | On-demand or <=1h refresh |
| Tier support | Freemium/v14/v15 confirmed in writing |
| Security posture | SOC 2 Type II or equivalent attestation |
| Landed cost | < CAD $150/clinic/mo all-in at 20 clinics |

**Third track, arguably highest EV: talk to ABELDent.** R&A with Power BI support implies a
sanctioned SQL read path exists. The ask is narrow and reasonable: a documented read-only role, a
schema/view contract, and advance notice of schema changes — in exchange for a clinic-consented,
write-free, no-inbound-port integration that improves their customers' CDCP outcomes. **1 eng-week +
founder time.** Even a partial yes converts our largest risk from existential to managed. Go in with
the security design in hand: *"outbound-only, signed query pack, enumerated GRANTs, clinic-readable
audit journal"* is a much better opening than *"we read your database."*

## 6. The abstraction boundary

**The interface is `IChartSource`.** One driver per PMS. Drivers return CDM types exclusively; no
source-shaped type ever crosses the boundary.

```csharp
public interface IChartSource
{
    Task<SourceCapabilities> DescribeCapabilitiesAsync(CancellationToken ct);
    Task<HealthReport>       HealthCheckAsync(CancellationToken ct);

    IAsyncEnumerable<PatientMatch> SearchPatientsAsync(PatientQuery q, CancellationToken ct);
    Task<Patient>                  GetPatientAsync(SourceRef patient, CancellationToken ct);
    Task<IReadOnlyList<Coverage>>  GetCoveragesAsync(SourceRef patient, CancellationToken ct);

    Task<IReadOnlyList<PlannedProcedure>>   GetPlannedProceduresAsync(SourceRef patient, CancellationToken ct);
    Task<IReadOnlyList<CompletedProcedure>> GetProcedureHistoryAsync(SourceRef patient, DateRange window, CancellationToken ct);
    Task<DentitionState>                    GetDentitionAsync(SourceRef patient, CancellationToken ct);
    Task<IReadOnlyList<PerioExam>>          GetPerioExamsAsync(SourceRef patient, DateRange window, CancellationToken ct);
    Task<IReadOnlyList<ClinicalNote>>       GetClinicalNotesAsync(SourceRef patient, DateRange window, CancellationToken ct);
    Task<IReadOnlyList<ImagingRecord>>      GetImagingIndexAsync(SourceRef patient, DateRange window, CancellationToken ct);
    Task<IReadOnlyList<ReferralDocument>>   GetReferralsAsync(SourceRef patient, DateRange window, CancellationToken ct);

    Task<Stream> FetchDocumentAsync(DocumentRef doc, CancellationToken ct);   // bytes, only on explicit action
    Task<ChangeFeedPage> GetChangesSinceAsync(Cursor cursor, CancellationToken ct);
}
```
Plus a companion `IImagingSource` with the same capability negotiation, because pixel data will often
come from a different vendor than the chart.

**Three properties that make PMS #2 cheap:**
1. **Capability negotiation is mandatory.** `SourceCapabilities` declares, per section,
   `Supported | Partial | Unsupported` with a reason. **A driver is allowed to not support perio; it
   is not allowed to be silent about it.** Without this, adding a weaker PMS silently degrades
   clinical correctness.
2. **Host-agnostic placement.** `AbelDentChartSource` runs in the on-prem agent (SQL, filesystem).
   `OpenDentalChartSource` and `ClearDentChartSource` are REST clients that can run **in the cloud
   with no agent installed at all.** Same interface, different host. One remote transport
   (`RemoteChartSource`, the agent RPC) satisfies the same interface.
3. **A driver TCK.** `Colombus.ChartSource.Conformance` — a shared xUnit suite every driver must
   pass: CDM schema validity, provenance completeness, **capability honesty** (if you claim
   `Supported`, you must return `Present` or `AbsentConfirmed`, never `Unknown`), tooth/surface
   normalization, date/timezone handling, idempotency, cancellation, error taxonomy. Plus golden
   fixtures per PMS. **Writing the TCK during the ABELDent driver is what turns "3 months per PMS"
   into "2–3 weeks per PMS."**

Marginal cost once the TCK exists: Open Dental ~2 eng-weeks, ClearDent ~3, Tracker ~4–6 (assume
another reverse-engineering exercise).

```
/contracts/cdm/v1/*.schema.json               # source of truth, codegen'd 3 ways
/contracts/chartsource/chartsource.v1.json    # agent RPC wire contract
/agent/src/Colombus.ChartSource.Abstractions  # IChartSource, CDM records, SourceCapabilities
/agent/src/Colombus.ChartSource.AbelDent      # driver + QueryPacks/abeldent-v14.yaml
/agent/src/Colombus.Sql                       # ReadOnlySqlExecutor, QueryCatalog, SchemaGuard
/agent/src/Colombus.Agent                     # worker service, transport, outbox, journal
/agent/src/Colombus.Bootstrap                 # updater service
/agent/installer                              # WiX v5, grant-colombus.sql generator
/agent/tests/Colombus.ChartSource.Conformance # the TCK
/tools/probe                                  # discovery CLI
/schema-map/abeldent/v14/entities.yaml        # reverse-engineering output, versioned
/fixtures/abeldent/fictional/*.json           # golden raw->CDM pairs, CI-enforced
/codesystems/                                 # uscls.csv (licence-gated), iso3950 maps
```

## 7. Risk register

| # | Risk | L | I | Mitigation | Escalation trigger |
|---|---|---|---|---|---|
| R1 | ABELDent disclaims third-party DB integrations; may object or block | H | H | Clinic-consented architecture (clinic grants the account, clinic owns the journal); write-free; no inbound ports; open partnership track; CDM makes a pivot a 2–3 week move | Written objection from ABELDent, or a pilot clinic's IT refusing |
| R2 | Schema drift on PMS update breaks extraction silently | H | H | `SchemaGuard` daily + at startup; fail closed per-entity with a named diagnostic; golden fixtures in CI; query packs shipped independently of binaries; canary ring | Any fingerprint mismatch in the field |
| R3 | **Fictional Data is sparse** (no perio charts, no images, no CDCP fields) | H | H | Probe catalogue doubles as fixture authoring — we enter perio charts, plans, notes, referrals through the UI ourselves; arrange a 2-hour read-only "schema audit" with a friendly clinic exporting **schema metadata and row counts only, zero PHI** | Week 3: any required entity unproduceable in Freemium |
| R4 | **Radiographs not in the ABELDent DB at all** | H | H | 1 eng-week imaging spike in week 2; `IImagingSource`; per-vendor drivers later; **manual upload fallback ships in v1 regardless** | Spike concludes no capture date is reachable from ABELDent |
| R5 | Freemium schema != Local Plus v15 / Cloud v15 | M | H | Obtain a paid/NFR trial or reseller v15 instance by week 4; fingerprint both; query packs per major version | No v15 instance by 2026-10-15 |
| R6 | Legal exposure from reverse engineering (EULA) | M | H | Counsel review week 1; **no IL decompilation without sign-off**; rely on lawful-possession artifacts, catalog views, XEvents on our own instance, UI-driven diffing; document methodology defensively | Counsel flags any technique |
| R7 | SQL Express contention degrades the clinic's PMS | M | H | Concurrency 1, `LOCK_TIMEOUT 5000`, `DEADLOCK_PRIORITY LOW`, MAXDOP 1, keyset pagination, quiet hours, blocking-chain auto-pause; `BackupSnapshotSource` escape hatch | Any observed block of an ABELDent session > 2 s |
| R8 | Windows auth / service account friction in workgroup clinics | H | M | Installer handles all three modes; password to LSA secret store only; `colombusctl test-sql`; documented IT runbook | >30 min install in the first pilot |
| R9 | PHI leaks into logs, telemetry, or LLM prompts | M | VH | Redaction sink + CI test that **fails the build** on PHI patterns; minimized bundles; Canadian-region inference with no-training terms; access journal | Any PHI found in any log |
| R10 | Canadian-region LLM inference unavailable for target models | M | M | Verify Bedrock ca-central-1 / Azure Canada East / Vertex northamerica-northeast1 now; provider interface in the reasoning layer; worst case run smaller models in-region and reserve cross-border for de-identified content | Verification negative |
| R11 | USC&LS licence not granted in time | M | M | Runtime-loaded code set, codes-only degraded mode, render clinic's own descriptions; enquiry sent week 1 | No response by 2026-10-31 |
| R12 | Deletes/voids invisible -> we assert a reversed procedure | M | H | `HashSweep` reconciliation; XEvents capture of the vendor's own void/status predicates so our filters match theirs; `asOf` + freshness budget, refetch before assembly | Any fixture showing a voided row surviving our filter |
| R13 | Windows 10 EOL on clinic hardware; unpatched OS hosting PHI | M | M | Installer pre-flight check; report OS/patch state in health; Win11 or ESU as a documented prerequisite | Any pilot clinic on unsupported Win10 without ESU |
| R14 | **No pilot clinic -> we build against fiction and are wrong** | H | H | Recruit a design-partner clinic by **week 4** even for read-only schema validation. **Founder-owned, hard-dated milestone, not an engineering task** | No clinic conversation booked by 2026-10-10 |

## Effort and sequencing (2–4 engineers, 12 weeks)

| Workstream | Eng-weeks |
|---|---|
| Schema discovery: core entities | 4.5 |
| Schema discovery: perio + imaging | 2.5 |
| CDM schemas, codegen, mappers, validators | 5.0 |
| Agent skeleton, enrolment, transport, state store | 4.0 |
| Query pack, `ReadOnlySqlExecutor`, `SchemaGuard` | 2.0 |
| Documents/images + `IImagingSource` | 3.0 |
| Installer, service accounts, self-update | 3.0 |
| Observability, redaction, access journal | 1.5 |
| Conformance TCK + fixtures + CI | 2.0 |
| Sikka diligence + ABELDent partnership + USC&LS + legal | 1.5 |
| **Total** | **~29** |

At 2.5 engineers on ingestion, ~12 weeks — the full runway with no slack.
**Cut here first if needed: drop `HashSweep` reconciliation and the Tier A change feed, ship pure
on-demand extraction.** Removes ~3 eng-weeks; costs only the proactive worklist.

**Milestones:** W2 first end-to-end query from the probe CLI against Fictional Data. W4 `Patient` +
`PlannedProcedure` in CDM, TCK green, design-partner clinic booked, Sikka answers in. W6 perio +
imaging metadata mapped, imaging spike concluded. W8 agent installs from MSI on a clean Windows VM,
enrols, serves a bundle to a stub cloud. W10 SchemaGuard, redaction CI, access journal, self-update
ring. W12 full bundle for the CDCP demo scenario, end to end, zero PHI, on the lab machine.

## Open assumptions (all week-1 emails or week-2 lab experiments; none open past week 4)

Vendor-side: whether the DB contains views/procs we can rely on; whether any `rowversion` or
maintained modified-date columns exist; whether Fictional Data contains perio exams, radiograph links
or CDCP coverage fields; whether Freemium's schema matches v15; where radiograph pixels and capture
dates actually live; the EULA's reverse-engineering terms.
Ours: .NET 10 as current LTS; Azure Trusted Signing pricing/eligibility; Canadian-region availability
of our target model; Open Dental / ClearDent API coverage for perio and imaging; the exact CDCP scope
of "all relevant completed and pending treatment needs"; USC&LS licence timeline; Sikka's answers.
