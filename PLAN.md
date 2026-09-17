# Colombus — Master Plan

CDCP preauthorization copilot for Canadian dental clinics.
3 engineers + 1 founder. Sequenced by task, not by calendar.

| Doc | What it is |
|---|---|
| `docs/research/cdcp-rules.md` | The product specification. Verified CDCP rules, codes, frequency limits, source URLs |
| `docs/research/market.md` | Sizing, competitors, pricing anchors, what won't stick, existential risk |
| `docs/research/integration-and-compliance.md` | ABELDent internals, CDAnet, privacy law, integration options ranked |
| `docs/plan/01-ingestion.md` | Schema discovery, local agent, canonical model, minimization |
| `docs/plan/02-reasoning.md` | Rules DSL, evidence matcher, LLM boundary, eval harness, packet spec |
| `docs/plan/03-product.md` | Demo, screens, milestones, pilot, pricing, kill criteria |

---

## Status — 2026-09-17

Research and plan complete. Lab sandbox live (`lab/vm/`), with a UI driver (`scripts/ui`) and a
whole-database diff-probe (`scripts/probe-step`) that turn one click in ABELDent into a per-column
list of what changed. Findings in `docs/research/abeldent-schema.md`.

**M0 "Read the chart" scorecard** (`lab/tools/chart_dump.py` → `fixtures/abeldent/fictional/`):

| Exit criterion | State |
|---|---|
| ≥20 patients, zero manual steps | **24**, one command, ~20 s. Source is the clinical ledger `Transactions`, not `tdi` — the financial ledger under-reads planned work by half |
| Planned procedure + tooth | Yes. FDI and Universal. Planned-and-not-done = `Type='P' AND Applied=0`, established by a completion probe |
| Perio exam with point count | Yes. Decoder verified byte-for-byte against the on-screen chart |
| Clinical note text | Yes. Current-version filter established by a note probe; modern notes are RTF and are converted |
| Radiograph metadata (type/tooth/date) | **Open.** Schema has it (`AImage`, `AImageVersion`, `AImageToothNumber`); Fictional Data ships images stripped and the Freemium Imaging view acquires via TWAIN only. Radiograph *events* (taken, billed, dated) do come from the ledger. K7 narrows to "see one `AImage` row on a live install"; manual upload is primary for pixels |

**Other M0 body items:**

| Item | State |
|---|---|
| Read-only service account | Not applicable to Freemium: LocalDB is per-user and invisible to a service account. Read-only is enforced in the lab tooling instead (keyword rail + always-rolled-back transaction in `q.ps1`). Decision on Express vs LocalDB for the shipped agent still open |
| Rule DSL with payer-adapter seam | Done in the reasoning core (below) |
| Repo, CI, Canadian infra, auth | Repo yes. No CI, no cloud infra, no auth yet |

Not resolved in the lab: `Type` values `I`/`T`, the planning-time `Type=' '` companion rows,
perio data entry by automation, the ABELDent EULA (founder item).

**Reasoning core is under way** (commit 78c1c5f): ~2,500 lines of Python in `colombus/` — deterministic engine
(1,024), CDM models (348), rule pack schema + loader (295), casegen DSL (184), notation/sextants (134),
LLM extraction proposer (86) — plus `packs/cdcp/2026-01-26/pack.yaml`, 6 demo cases with golden expectations,
and a `Makefile`. Still empty stubs: `packet/`, `verify/`, `web/`, `assertions/`, `sources/`.

## Context

Canadian dental clinics submit preauthorizations to Sun Life for CDCP treatment. Today it is manual: staff recall
which codes need preauth, hunt the chart for radiographs and perio charting, judge recency, write the narrative by
hand, assemble attachments. **46% get approved. Crowns get 37%.** ~20% of submissions arrive incomplete, and Health
Canada and Sun Life both name the cause: missing radiographs, insufficient clinical notes, absent periodontal
charting. Every resubmission goes to the back of the queue as a brand-new request.

Colombus reads the proposed treatment and patient record from the practice management system, checks it against
CDCP documentation rules, locates the supporting evidence already in the chart, flags what is missing or stale, and
assembles a submission packet with a drafted rationale. **Staff review and submit. We never transmit.**

## Decisions locked

| | Decision | Why |
|---|---|---|
| **Scope** | Gap-check + packet assembly. **Human submits.** | CDAnet Prohibited Practices: *"Only the treating dentist can send the claim"* and non-certified software may not submit. Not transmitting sidesteps the entire certification gate. |
| **Beachhead procedure** | **Crowns (27xxx) only in v1.** Endodontics v1.1. | Crowns are 37% approval with the heaviest documentation burden. Partial dentures are >76% — that workflow already works, there is no pain to sell. *"We do the procedure that gets denied."* |
| **Dev data** | ABELDent Freemium + its bundled **Fictional Data** set, on our own machine. Zero PHI during the build. | Free, real SQL Server schema, no clinic required, no privacy exposure during build. |
| **First paid segment** | **NOT ABELDent Freemium clinics.** ClearDent (partner program + API + write-back) or Open Dental (best public API). | Freemium is a lead-gen funnel for startup/hygiene practices: no support contract, no updates, no API, lowest CDCP volume, least money. Worst possible first customer. Sandbox and beachhead are different roles — keep them separate. |
| **Deployment** | **Local read-only agent on the practice Windows server + Canadian-hosted cloud.** Outbound HTTPS 443 only, no inbound listener. | The measured Freemium install ships SQL Server 2022 **LocalDB** (`(LOCALDB)\MSSQLLOCALDB`), reachable only over a named pipe whose name regenerates on every restart and owned by the interactive Windows user — a LocalSystem service cannot see it at all (`docs/research/abeldent-schema.md` finding 1). ABELDent ships a vendor-authored `installSQLExpress_SSMS.ps1` upgrade path to a real Express instance, so which one the agent targets is a live decision. Outbound-only is both the security posture and the answer to ABELDent's published objection to third-party DB integrations. |
| **Stack** | **C#/.NET 10** agent (Windows auth to SQL, MSI, service hosting are all first-class). **Python 3.12 + Pydantic v2** reasoning core (Pillow, python-docx, pikepdf, dateutil are Python-native). **Next.js** web. Contract between them is JSON over HTTPS. | Each layer picks the ecosystem that owns its problem. |
| **Build vs buy** | **Build the reader. Do not buy Sikka.** Diligence spike in parallel; decide before the agent's data layer is committed. | US-hosted with no SOC 2/HIPAA claim in their own FAQ; 2:00 AM refresh is architecturally wrong for an in-appointment workflow; perio/notes/radiograph coverage unknown; ~US$385+/mo floor. Keep `SikkaChartSource` as a named un-built driver for PMS #4–10. |

## The one architectural commitment

**The verdict is produced by deterministic code over a typed artifact index. The language model is an evidence
proposer and a prose drafter. It is never a judge.**

This output is read by an insurer during a rising audit cycle. *"The model thought the radiograph was recent
enough"* is not a defensible answer. *"Rule `radiographs_pa_bw` v2026.01.26 required <=365 days; artifact
`rad_8831` captured 2026-05-14; age 126 days; pass"* is.

Corollary: **an LLM-proposed artifact can never by itself produce `satisfied`.** It produces
`satisfied_pending_confirmation`; a human confirms; the engine re-runs deterministically.

## The insight that makes v1 buildable

**CDCP crown criteria require measurements that exist in no chart.** Crown-to-root ratio <= 1:1, absence of
furcation involvement, restoration margin >= 3 mm from the alveolar crest, ferrule >= 1.5 mm. Three of the four
are measurements a human makes by looking at the film and are not fields in ABELDent at all; extracting them needs
image analysis, which is correctly out of scope. Furcation is the exception — ABELDent does record it
(`Perio.Furcation`, decoded and populated in our fixtures) — but a probed furcation reading and CDCP's
radiographic "absence of furcation involvement" are not the same assertion. **SME to confirm whether the charted
value can stand in; until then it is an assertion, not an extraction.**

**The resolution: a Clinician Assertions block.** The dentist confirms each criterion with one tap and the packet
renders it as attributed clinical judgment — *"Dr. Lau assessed ferrule height at #16 as >=1.5 mm on 2026-11-16."*

This one feature (a) removes image AI from scope, (b) puts liability exactly where it legally sits, (c) produces a
defensible audit artifact in a market where insurer audits are surging, and (d) is precisely what Smilepass and
Cleer do not have, because they are verification tools and this is a clinical-documentation tool. Build it in M1.

---

## Scope reconciliation — the hard part

The three deep-dive plans total **98 engineer-weeks**, roughly three times what v1 can carry with three engineers.
Effort figures are relative sizing for ordering, not a calendar.

### Cut from v1 — with what it costs

| Cut | Saves | What it costs | Why it's the right cut |
|---|---|---|---|
| **LLM-generated narrative.** Ship template + verbatim chart quotes + Clinician Assertions instead. | **5 ew** | Less impressive demo beat 4 | Kills the K9 one-strike hallucination risk, the cross-clinic templating audit exposure, and the grounding-validator complexity — all at once. The Assertions block carries the clinical weight anyway. **Build generation + grounding validator together in v1.1, never generation alone.** |
| **Endodontics rules** (32xxx/33xxx) -> v1.1 | 1 ew | Narrower demo | Crowns are the denial mass. Prove one procedure. |
| **All non-crown service categories** (dentures, oral surgery, sedation, SRP, specialist exams) | 4 ew | — | >76% approval on dentures = no pain. Others are lower volume. |
| **`HashSweep` reconciliation + Tier A change feed.** Pure on-demand extraction only. | 3 ew | No proactive worklist; the queue populates when a user opens it | Named as the ingestion plan's own first cut. |
| **Agent installer, self-update, staged rings** | 3 ew | Pilot #1 is hand-installed by us | The first pilot clinic does not need an MSI and a canary ring. |
| **Rules Studio editor.** SME edits YAML in the GitHub web editor; CI posts the verdict-delta. | 4 ew | SME needs GitHub | **The "no deploy" constraint is satisfied by the loading architecture, not the editor.** Packs load from Postgres with a 60s cache; publishing is a row insert. |
| **Look-Back as software** -> founder-run spreadsheet until M4 | 2 ew | Manual, 30 min/clinic | It is a sales instrument first. Manual is fine at 8 clinics and gets the recoverability answer sooner. |
| **Full FHIR alignment ceremony.** Keep the resource shapes, `Provenance`, `SourceAssurance`. Drop profiles/Bundle/extensions. | 2 ew | No FHIR facade yet | Zero interoperability benefit in Canada today. |
| Corpus 120 -> **60 cases** (40 crown + 20 adversarial) | 2 ew | Thinner coverage | Grows continuously after launch; `casegen` DSL is what makes that cheap. |

### Must not be cut, under any circumstances

1. **The eval harness.** With no clinic and no outcomes, it *is* the correctness argument.
2. **`ReadOnlySqlExecutor` + signed query pack.** The cloud can invoke a query ID with typed parameters; it can
   never send SQL. Full cloud compromise yields "read patient 4711's perio exams," not `SELECT * FROM everything`.
3. **`SchemaGuard` fingerprinting.** Converts silent-wrong-answer on a PMS update into a loud, diagnosable failure.
   Directly answers ABELDent's "these break on every update" objection.
4. **`SourceAssurance` on every bundle section.** *"This patient has no perio chart"* and *"this driver cannot see
   perio charts"* are opposite clinical conclusions. Without it the rules engine fabricates gaps.
5. **The independent packet verifier**, written by a different engineer than the assembler.
6. **Zero false `satisfied`.** Costs are wildly asymmetric: a false `unsatisfied` costs five minutes; a false
   `satisfied` costs a denial, a resubmission against explicit "avoid duplicates" guidance, and our credibility.
   Prefer `indeterminate` over `satisfied` under uncertainty, structurally.
7. **The attestation step.** Non-skippable, non-bulk. One case, one human, one action.
8. **`DeidentifiedCaseView` as the only type the LLM client accepts.** See residency below.

### Reconciled v1 budget

| Workstream | ew | Owner |
|---|---|---|
| Schema discovery — crowns-scoped entities (patient, coverage, planned/completed procedures, notes, perio, imaging metadata) | 5.0 | Eng A |
| `ReadOnlySqlExecutor`, signed query pack, `SchemaGuard` | 2.0 | Eng A |
| CDM schemas + mappers + `Provenance` + `SourceAssurance` | 3.0 | Eng A |
| Local agent: service, enrolment, transport, state store, access journal | 3.0 | Eng A |
| Document/image retrieval + `IImagingSource` + manual-upload fallback | 2.5 | Eng A |
| Rules: schema, linter, evaluator, version store | 4.0 | Eng B |
| Crown rule pack (~12 rules, hand-transcribed from image-only PDFs) | 1.5 | Eng B + SME |
| Evidence matcher (index, leaves, `Shortfall`, recency, sextants, notation) | 5.0 | Eng B |
| LLM extraction + substring-literalness validator | 2.5 | Eng B |
| Eval harness + `casegen` DSL + 60-case corpus | 4.0 | Eng B |
| Packet assembly + image spec normalization + independent verifier | 3.5 | Eng C |
| Web app, 4 screens + email digest | 6.0 | Eng C |
| Clinician Assertions | 1.0 | Eng C |
| Observability, redaction CI, audit log | 1.5 | Eng C |
| **Total** | **34.5** | |

**Next cut if v1 runs over:** the `IImagingSource` abstraction (hard-code the one imaging vendor we find), and Screen 5.

---

## Milestones

Each milestone is a stage with a falsifiable exit. Do them in order.

**M0 — "Read the chart"**
Schema mapped from Fictional Data; read-only service account; 6 entities extracted. Rule DSL designed **with the
payer-adapter seam** (2 days — the Alberta hedge, near-free now, a rewrite later). Repo, CI, Canadian infra.
**Exit:** for >=20 Fictional Data patients (counted from `Transactions`, which holds 24 patients with
planned work against `tdi`'s 14; any shortfall is filled by UI-entered probe fixtures, not a blocker),
extract planned procedure + tooth + all radiograph metadata
(type/tooth/date) + perio exam with point-count + clinical note text, **zero manual steps.** If imaging metadata or
perio point-count cannot be read, this is kill-level (K7) — escalate immediately.

**M1 — "First verdict"**
12 crown rules encoded, each citing its source clause. Evidence matcher for structured fields. Clinician Assertions
model. Screen 2 (Case Review), ugly but real. SME contracted. First manual Look-Back on 2 friendly clinics' denial
exports.
**Exit:** SME reviews 20 crown cases; >=16 verdicts correct; **0 cases where Colombus says "ready" and the SME says
"would be denied."**

**M2 — "The packet"**
Packet PDF renderer + independent verifier. Template rationale with verbatim chart quotes. Image retrieval and spec
normalization. Agent skeleton as a Windows service. PHIPA agent/ESP template drafted.
**Exit:** 3 external billing coordinators (paid $100 each) score 10 packets. **Median >=3/4 on Completeness and
Correctness, 0 hallucinated clinical claims across all 30 scorings.**

**M3 — "The Friday Five"**
Screens 1, 3, 5. Email digest. Sign-off record with diff capture. Agent hardened, outbound-only TLS, tray UI. Demo
rehearsed; first 10 prospect demos booked.
**Exit:** 3 cold-open tests (people who did not build it, 15 min, no instructions, recorded) reach a signed packet
unaided. Playwright visual regression green on 12 canonical cases.

**M4 — "Look-Back + lockdown"**
Look-Back productized. Pen-test of the agent. Canadian residency posture confirmed with a signed DPA. One
**non-CDCP adapter stub** (Canada Life) to prove the seam is real.
**Exit:** Look-Back runs unattended on 12 months of Fictional Data history and reproduces the SME's manual
spreadsheet within +/-10% on "denials with a documentation gap."

**M5 — "First install"**
Pilot clinic #1, hand-installed. Shadow mode on 40% of cases. Instrumentation live.
**Exit:** agent runs 7 days on a real practice server with **zero unplanned restarts and zero inbound firewall
changes required.**

**M6 — "Pilot running"**
2 clinics live. Weekly Outcome Sweep in use.
**Exit:** >=10 real cases through Case Review -> sign-off, >=1 outcome recorded.

### Explicitly not in v1
SOC 2 Type 2 (needs a 3–12 month observation window after Type 1, so **no DSO deal until well after the pilot**). A
second PMS. CDAnet transmission. PMS write-back. Approval prediction. Image analysis. Non-crown categories.
**Quebec (Law 25 PIA) and Alberta (statutory Information Manager Agreement) — pilot clinics must be Ontario, BC as
fallback.** Self-serve signup. Mobile.

---

## Data residency — verified, and not what you'd assume

**There is no path to in-Canada inference for current-generation Claude today.** Anthropic's first-party
`inference_geo` accepts only `"us"` and `"global"`, workspace geo is US-only and immutable. Vertex regional
endpoints support Sonnet 4.6 and earlier only. Bedrock `ca-central-1` serves current Claude via cross-region
profiles by design.

**De-identifying at the type level is a stronger control than geo-pinning anyway.** The reasoning core never needs
a name, DOB, health number or address — it needs dates, tooth numbers, codes and findings. Build
`DeidentifiedCaseView` and make it **the only type the LLM client module accepts**: a `Patient` cannot be passed to
it; the type checker refuses. Free, and it is the control a privacy officer actually wants to see.

Alongside it: `inference_geo: "us"` with `allowed_inference_geos: ["us"]`, zero data retention, contractual
no-training, **Canadian residency for storage at rest** (Azure Canada Central / AWS ca-central-1 — which we fully
control), documented PIA, and the provider abstraction kept clean so a Canadian endpoint drops in when one exists.

Sequencing relief: development runs entirely on Fictional Data with no PHI, so this is a pre-pilot blocker, not a
day-one one.

---

## The $0 actions — before any code, in order

1. **Email `uscls@cda-adc.ca`** for the USC&LS procedure-code licence. Longest calendar lead time in the plan,
   lowest cost. Without it the product is unshippable as designed (K8).
2. **Call 10 office managers** (officemanagers.ca, ODAA): *"How many CDCP predeterminations did your office submit
   last month?"* This is K1 and the cheapest kill in the plan. Published sources support both ~2.4 and ~75 preauths
   per dentist per year. **Nothing else matters if the answer is "two."**
3. **Read the ABELDent EULA** on our own Freemium install (installer -> View Terms, or the ABELDent folder). 5
   minutes. Determines whether direct DB reads are viable at all. ABELDent has published in writing that
   unauthorized third-party DB integrations "may present a privacy and security risk" and that they will disclaim
   responsibility.
4. **File an ATIP request** with Health Canada on CDCP administration vendor contracts and any planned
   intake-validation capability. Free, ~30-day turnaround. Directly tests the Olive scenario (K4).
5. **Book a Smilepass demo through an advisor**, not from a Colombus address. Map exactly what they do on
   predeterminations. They already integrate ABELDent, are explicitly CDCP-aware, and track submitted
   predeterminations. Our gap over them is narrow and closing (K6).

Also, lower urgency: email `cdanet@cda-adc.ca` for ITRANS vendor docs (all three published PDF links are dead) and
whether a third party may transmit under dentist credentials; email Sikka the eight diligence questions; call
ABELDent 800-267-ABEL press 1 about a non-imaging partner path — **they built a bespoke integration for Diagnocat,
so a partner path exists informally, and even a partial yes converts our largest risk from existential to managed.**

---

## Top risks

| # | Risk | Cheapest next action |
|---|---|---|
| 1 | **Per-clinic preauth volume 30x lower than modelled** | 10 phone calls. Zero cost. |
| 2 | **Recoverability <8%** — the pricing thesis collapses | Manual spreadsheet Look-Back on 2 clinics' denial exports. No product needed. |
| 3 | **No distribution at $4.2k ACV.** No salesperson, no self-serve motion in this plan. Breakeven is ~200 clinics. | 20 discovery calls + the ABELDent partnership conversation. **Largest non-technical gap.** |
| 4 | **Payer fixes it at intake** (Olive scenario). Health Canada spends $472.9M+ on admin partly absorbing resubmission churn; the cheapest fix available to *them* is structured intake validation, not 18,000 clinic-side copilots. | ATIP request; subscribe to CDCP provider bulletins; call Sun Life provider relations. |
| 5 | **ABELDent read access blocked or fragile** | 2-day DB spike; EULA read; email their integration team; design a report-export fallback. |
| 6 | **Radiographs not in the ABELDent DB at all** — the imaging bridge is outbound launch-with-context, so pixel data is likely a third party's | 1 eng-week imaging spike, early. **Manual upload fallback ships in v1 regardless.** |
| 7 | **Fictional Data has zero images and every date is 2002–2007** — it tests plumbing, not verdicts. Perio, notes and planned crowns turned out to be present, so this is narrower than first feared | Evaluate against a per-case `as_of` date rather than today. The schema-probe catalogue doubles as fixture authoring for the cases the corpus lacks. |
| 8 | **CDCP political fragmentation.** Alberta formally notified intent to opt out (306k+ enrolled); the Act has explicit opt-out provisions; Quebec may follow. | **Build the payer-adapter seam in M0 (2 engineer-days).** Eight carriers already accept CDAnet attachments — the packet problem exists across all of them. |

**Kill criteria, dates, and the full risk register are in `docs/plan/03-product.md`.**

---

## Pricing

**$349/clinic/month flat. Unlimited users, unlimited cases, one location.** Founding pilots: free 90 days, then
**$249/mo locked for 12 months, signed at pilot start** so there is no second sales cycle.

**Never lead with time saved.** Displaced labour is ~$1,180/clinic/yr against a $4,188/yr price — a losing
argument, and the documented churn case is a single-doctor practice that dropped AI verification because it cost
more than a part-time coordinator. Lead with denied revenue recovered ($5,500–$10,300/clinic/yr on current
modelling), then patient-promise risk, then case acceptance. **Never price per-claim** — DentalXChange anchored
that at $0.25 and $25/mo unlimited attachments.

---

## The copy law

Colombus never says **approved, will be approved, eligible,** or **covered.** It says: *"CDCP crown criteria
require a periapical within 12 months. The most recent periapical of #46 is dated 2023-11-14."*

Every statement is about **documentation completeness against a cited rule**, never about payer behaviour. This is
the single line that separates us from Olive AI ($902M raised, $4B valuation, dead) and from the #1 documented
complaint about AI insurance verification: *"the benefits verified before treatment do not match what the
insurance company actually paid."* In the style guide, and enforced in code review.
