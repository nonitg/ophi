# Reasoning Core Plan

*Pre-reconciliation deep-dive. PLAN.md carries the v1 cut; the effort numbers here are uncut.*

## 0. The one architectural commitment everything follows from

**The verdict is produced by deterministic code over a typed artifact index. The language model is an
evidence *proposer* and a prose *drafter*. It is never a judge.**

Not purity — defensibility. This output is read by an insurer during a rising audit cycle. *"The
model thought the radiograph was recent enough"* is not an answer. *"Rule `radiographs_pa_bw`
v2026.01.26 required <=365 days; artifact `rad_8831` captured 2026-05-14; assessed as of 2026-09-17;
age 126 days; pass"* is.

Stack: Python 3.12 + Pydantic v2 for the core (the toolchain — Pillow, python-docx, pikepdf,
hypothesis, dateutil — is Python-native), FastAPI for the API, Next.js for the reviewer UI.

## 1. Rules representation

### Candidates
| Approach | Verdict |
|---|---|
| Code (Python functions per category) | Fastest to write; cannot update without a deploy; rule logic becomes invisible to the SME who owns its correctness. Rejected on the stated constraint. |
| General rules library (json-logic, CEL, Cedar, Drools) | Expression power but no domain nouns — the SME writes `{"<=":[{"var":"age_days"},365]}`. Worse, you lose *structural* access: can't generate a gap message, a remediation ranking, or a diff report from an opaque AST. Rejected. |
| Pure decision table (DMN/CSV) | Perfect for the 8x8 matrix — the SME already reads it as a grid. But cannot express footnote 5 ("one of five alternative evidence sets") or footnote 7 (a threshold test that *escalates into a different requirement*). Those aren't cell values; they're conditional requirement graphs. Insufficient alone. |
| Constrained declarative YAML with a closed predicate vocabulary | **PICKED.** |

### The pick: two-layer ruleset — decision table over a requirement grammar

Layer 1 (matrix) — a decision table the SME edits as a grid: service category x requirement id ->
applicable / not / conditional. A 1:1 mirror of the published table, diffable against the PDF by eye.

Layer 2 (footnotes) — a requirement grammar: YAML with a **closed vocabulary of ~12 predicate
types.** No arithmetic, no user-defined functions, no loops; the SME composes from a fixed menu. That
is why a non-engineer can edit it — learnable in an afternoon, and a JSON Schema plus linter catches
everything else.

```
find              artifact query leaf (the only way to reference the chart)
one_of            alternative satisfaction sets
require_all       conjunction
not               negation
applies_when      gating predicate on service/treatment/tooth
escalation        threshold test that demands a *different* requirement
on_select         requirement spawned by choosing a particular alternative
narrative         a human-written rationale requirement
precedence        conflict resolution between escalations
policy_decision   explicit interpretation where the source text is ambiguous
recency           calendar-month or day-based age bound
coverage          counting/completeness (all sextants, both lateralities, N distinct)
```

Anything a rule change needs that this vocabulary can't express is a deliberate signal for an
engineer: the linter rejects it rather than letting the SME improvise.

### Worked example: footnote 7 (PSR escalation)

```yaml
# packs/cdcp/2026-01-26/requirements/perio_chart.yaml
- id: perio_chart
  label: Dated complete periodontal chart (within the previous 12 months)
  applies_when:
    any:
      - all: [{ service_category: restorative }, { treatment_has_tag: crown }]
      - { service_category: endodontic }

  satisfied_by:
    one_of:
      options:
        - id: complete_perio_chart
          label: Complete periodontal chart, 6 sites per tooth, full mouth
          remediation_cost: chart_entry
          find:
            artifact_type: perio_chart
            completeness: complete          # all dentate teeth, 6 sites each
            recency: { months: 12 }
            as_of: $submission_date

        - id: psr_interim_path
          label: PSR per sextant + 6-site measurements for each requested tooth
          # Source wording is "will be considered", not "is accepted".
          # Therefore this path never yields `satisfied` — only `at_risk`.
          confers_status: at_risk
          remediation_cost: chart_entry
          require_all:
            - find:
                artifact_type: psr
                coverage: { sextants: all }   # S1..S6, none missing
                recency: { months: 12 }
            - find:
                artifact_type: perio_measurements
                sites_per_tooth: 6
                for_teeth: $requested_teeth
                coverage: { teeth: all }
                recency: { months: 12 }
            - not: { escalation: psr_requires_full_chart }

  escalations:
    - id: psr_requires_full_chart
      precedence: 100                        # highest — supersedes sextant demand
      over: { artifact_type: psr, recency: { months: 12 } }
      when:
        any:
          - { psr_score: { gte: 4 }, in_sextants: any,  min_count: 1 }
          - { psr_score: { eq:  3 }, in_sextants: any,  min_count: 2 }
      then:
        demand:
          option: complete_perio_chart
          severity: blocking
          message: >-
            PSR recorded {{ matched | describe }}. CDCP requires a complete
            periodontal chart when PSR is 4 in any sextant, or 3 in two or
            more sextants. The PSR-plus-six-site path is not available.

    - id: psr_requires_sextant_chart
      precedence: 50
      over: { artifact_type: psr, recency: { months: 12 } }
      when:
        { psr_score: { eq: 3 }, in_sextants: $sextants_of($requested_teeth), min_count: 1 }
      then:
        demand:
          requirement: sextant_perio_charting
          scope: { sextants: $matched_sextants }
          severity: blocking

  policy_decision:
    id: PD-004
    question: >-
      Footnote 6 grants a rationale-in-lieu-of-charting for additional SRP units.
      The published table does not extend that relief to crowns or endodontics,
      which instead get the footnote-7 PSR path. Do we offer the rationale path here?
    decision: "No. Footnote 7 is the only alternative for crowns/endo in this pack."
    decided_by: <SME name>
    decided_on: 2026-01-29
```

Two load-bearing details:
- **`confers_status: at_risk`.** The source says PSR "will be considered" — discretionary language.
  Encoding that as a first-class status rather than flattening it to `pass` is the difference between
  telling the truth and setting the clinic up for a denial.
- **`precedence`.** Both escalations can fire on the same chart. Without an explicit field the
  engine's behaviour depends on dict ordering — the kind of thing that survives testing and fails in
  production.

### Worked example: footnote 5 (one-of-N for partial dentures)

```yaml
- id: rpd_imaging
  applies_when: { service_category: removable_partial_denture }
  satisfied_by:
    one_of:
      options:
        - id: pa_abutments_plus_bw
          remediation_cost: new_radiograph
          require_all:
            - find: { artifact_type: radiograph, view: PA,
                      for_teeth: $abutment_teeth, coverage: { teeth: all },
                      recency: { months: 12 } }
            - find: { artifact_type: radiograph, view: BW,
                      coverage: { laterality: [right, left] },
                      recency: { months: 12 } }
        - id: most_recent_pano
          remediation_cost: reuse_existing
          # NOTE: source says "most recent dated pano" with NO recency bound.
          # Do not add one. A 2019 pano satisfies this.
          find: { artifact_type: radiograph, view: PANO, select: most_recent, recency: null }
        - id: arch_photos
          remediation_cost: reuse_existing
          require_all:
            - find: { artifact_type: photo, subject: arch_upper, count: 1 }
            - find: { artifact_type: photo, subject: arch_lower, count: 1 }
          constraints: [ distinct_files ]     # blocks the same file used twice
        - id: stone_model_photos
          remediation_cost: reuse_existing
          require_all:
            - find: { artifact_type: photo, subject: stone_model_upper, count: 1 }
            - find: { artifact_type: photo, subject: stone_model_lower, count: 1 }
          constraints: [ distinct_files ]
        - id: stone_models
          remediation_cost: lab
          delivery: physical                  # cannot enter a CDAnet packet
          find: { artifact_type: stone_model, coverage: { arches: [upper, lower] } }
```

`delivery: physical` earns its place: stone models satisfy the rule but cannot be attached
electronically. Without it the assembler reports a satisfied requirement it cannot ship, and the
clinic finds out at the insurer.

Footnote 3's pano-with-rationale is the `on_select` case — choosing an alternative *creates* a
requirement:
```yaml
- id: pano_substitute
  on_select:
    add_requirement:
      { id: intraoral_not_possible_rationale, type: narrative,
        role: imaging_substitution_rationale, severity: blocking }
```

### Versioning

Rule packs are **data, not repo content.** The repo carries seed packs for tests; production packs
live in Postgres.
```sql
ruleset_versions(
  id, ruleset_id, version, content_hash, content jsonb,
  effective_from date, effective_to date, source_url, source_sha256,
  published_by, published_at, supersedes_id, eval_run_id )
```
- Evaluation is always the pair `(case, ruleset_version_id)`. Resolution: the pack whose
  `[effective_from, effective_to)` contains the case's intended submission date — not today, not the
  assessment date.
- Every `Assessment` persists `ruleset_version_id` and `content_hash`. A hash mismatch on replay is a
  hard error, not a warning.
- Re-running old cases against new rules is first-class: `POST /rulesets/{draft}/shadow-run` replays
  the entire stored case history plus the golden corpus and returns a verdict-delta report — both the
  publish gate and the "what does the April update do to our pipeline" answer.
- USC&LS code sets are versioned separately from the requirement logic; they churn on a different
  cadence (April 2026 opened PA codes to hygienists without touching the doc matrix).

### Authoring without a deploy
App loads packs from Postgres with a 60-second cache; publishing is a row insert, not a release. v1
ships ruleset-as-data + read-only Rules Explorer + publish gate + SME edits via a YAML file in the
GitHub web editor, with CI running the corpus and posting the verdict-delta as a PR comment. v1.1
ships the form-driven Rules Studio. The "no deploy" constraint is satisfied by the *loading
architecture*, not the editor; building the editor first spends four engineer-weeks on the wrong end
of the problem.

**Effort: 6 eng-weeks** (schema + linter + evaluator + version store + shadow-run). Rules Studio +4,
deferred.

## 2. Evidence matching

### Canonical artifact model
```python
class ChartArtifact(BaseModel):
    artifact_id: str
    type: ArtifactType          # radiograph|perio_chart|psr|perio_measurements|
                                # photo|stone_model|clinical_note|tx_plan|narrative|claim_form
    captured_at: date | None    # when the evidence was CREATED
    recorded_at: date | None    # when it was entered into the PMS
    date_confidence: Literal["source", "inferred", "unknown"]
    provenance: Provenance      # system, table, row_id, extraction_method, confidence
    payload: RadiographPayload | PerioChartPayload | PSRPayload | ...
    file: FileRef | None
```
Baked into the type, non-negotiable:
- **Recency uses `captured_at` only.** Absent -> `date_confidence: inferred`, and any recency test
  returns `indeterminate`, never `pass`. Dating a radiograph by its import timestamp is how you ship
  a stale x-ray.
- `extraction_method: "llm"` artifacts carry `confirmed_by`/`confirmed_at`. Unconfirmed, they can
  only produce `satisfied_pending_confirmation`.

### Tooth notation
Canonical internal representation is FDI ISO 3950; store `tooth_fdi`, `tooth_as_written`,
`notation_declared`.

The trap: `"16"` is valid in both FDI (upper right first molar) and Universal (upper left third
molar). **Notation is never inferred from the number** — it comes from the source system's declared
convention, **declared per source table, not per PMS integration.** One flag per integration gets
ABELDent wrong on day one: a single vendor database carries Universal in `Perio` and FDI in
`tdi.itooth` / `Notes.ToothNumber` simultaneously (`docs/research/abeldent-schema.md` finding 4), so
whichever value you set, the other table is silently misread. Undeclared -> fail closed to
`indeterminate` with a "confirm tooth notation for this chart" action; a heuristic would be wrong
silently, and often (an assumed rate of about one chart in twenty — illustrative, not measured). (Palmer notation exists in older Canadian charts: parse it, normalize
it, never emit it.)

### Sextant mapping
Static table, versioned as data next to the ruleset:
```
S1: 18 17 16 15 14      S2: 13 12 11 21 22 23      S3: 24 25 26 27 28
S6: 48 47 46 45 44      S5: 43 42 41 31 32 33      S4: 34 35 36 37 38
```
`$sextants_of($requested_teeth)` is a pure function over this table, exhaustively unit-tested over all
32 positions — there are only 32, so test all of them rather than sampling.

### The matcher — a deterministic constraint solver, five stages
1. **Index.** Inverted indices over the artifact set: by type, FDI tooth, sextant, quadrant,
   laterality, date (sorted). Built once per case, reused across all requirements.
2. **Expand.** Compile the requirement YAML into a boolean tree whose leaves are `ArtifactQuery`.
3. **Resolve leaves.**
```python
class LeafResult(BaseModel):
    status: Literal["satisfied","unsatisfied","indeterminate","at_risk"]
    matched: list[str]              # artifact_ids
    shortfall: Shortfall            # ALWAYS populated, even when satisfied
    expires_on: date | None         # when this match goes stale
```
   The always-populated `shortfall` is what makes gap messages precise. For "dated PA + BW, right and
   left, <=12 mo, tooth 46" the shortfall isn't "radiographs missing" — it's
   `{missing_views:[BW-left], stale:[{artifact:rad_771, view:PA, tooth:46, age_days:401, over_by:36}]}`,
   which renders as *"the PA for 46 is 36 days too old; the left bitewing is absent."*
4. **Solve.** Boolean evaluation, plus: when a `one_of` has no satisfied option, rank options by
   `remediation_cost` and report the cheapest near-miss, not a list of five failures. For the RPD case
   that is the difference between "no imaging found" and *"you have a 2019 panoramic — that satisfies
   this requirement, no new imaging needed."*
5. **Emit.** `RequirementResult` with a deterministic explanation templated from rule metadata plus
   matched artifact ids. Same inputs -> byte-identical output. Asserted in tests.

### Recency arithmetic — the boundary problem
The source says "within the previous 12 months." Twelve calendar months and 365 days differ across a
leap year, and CDCP has not published which convention adjudicators apply. **Decision: evaluate
both.** `recency: {months: 12}` is primary (calendar months via `dateutil.relativedelta`, inclusive);
where the two disagree — a ~1-day band — return `at_risk` with an explicit note, not `satisfied`.
Cheap, honest, auditable; turns an unknowable into a visible one.

Because every match carries `expires_on`, the system can also say *"this passes today, but the PA for
46 goes stale on 2026-09-26 — submit before then, and note CDCP asks you to allow a minimum of two
weeks for processing."* Falls out of the model for free; one of the more useful things it can say.

### Where deterministic code ends and the model begins

Deterministic, always, no exceptions: date arithmetic and recency; tooth <-> sextant/quadrant/arch
mapping; notation conversion; artifact type/view/laterality matching; counting and coverage (both
lateralities, all six sextants, two *distinct* photos); PSR threshold comparison; boolean solving;
per-requirement status; overall verdict; ranked actions.

Model, bounded: reading unstructured clinical notes and free-text treatment plans to *propose*
structured artifacts. Nothing else in the decision path.

Justification for the line: every deterministic item is a total function over a small typed domain
with an unambiguous correct answer — no judgment to exercise, so a model can only add variance.
Free-text note reading is the opposite: irregular input, no schema, genuine language understanding
required. That is the only place a model earns its cost.

The bridge is strict: an LLM-proposed artifact enters the same index tagged `extraction_method: llm`
and cannot by itself produce `satisfied`. It produces `satisfied_pending_confirmation`; the reviewer
confirms with one click; the engine re-runs deterministically. **The model proposes; the engine
judges; the human ratifies.**

**Effort: 8 eng-weeks.**

## 3. Where the LLM is used

| Job | Model | Config | Why |
|---|---|---|---|
| **Evidence extraction** from notes / free-text plans | `claude-haiku-4-5` | `strict: true` structured output, `thinking: {type:"enabled", budget_tokens: 2048}` | High volume (every note in every chart), narrow schema, span-grounded. Cheapest model that does structured extraction well. |
| **Escalation** for low-confidence/rejected extractions | `claude-sonnet-5` | `thinking: {type:"adaptive"}`, `effort:"medium"` | Second opinion on the ~10% that fail the literalness check |
| **Narrative / rationale drafting** | `claude-opus-5` | `thinking: {type:"adaptive"}`, `effort:"high"`, structured output | One call per case, goes in front of a clinician, carries audit and liability weight. ~15K in / 1.5K out ~= **$0.11/case.** Do not cheap out. |
| **Grounding judge** (eval harness only, not the request path) | `claude-sonnet-5` | `effort:"high"` | Must be a different model/prompt than the generator to avoid self-agreement |
| **Gap explanation** | **no model** | — | Deliberate, see below |

Gap text is template-rendered from rule metadata, deterministically. It is the thing the user acts on;
it must be identical for identical inputs and traceable to a rule id. A model is permitted only in an
on-demand "explain this to me" side panel that cannot change the action list.

### Prompt architecture — four cache-stable layers, volatile last
```
[1] system: role, refusal boundaries, style constitution     <- frozen, cache_control
[2] ruleset-version context (requirement labels/definitions) <- quarterly, cache_control
[3] clinic_style_profile                                     <- rare, cache_control
[4] evidence_ledger + case payload                           <- volatile, NOT cached
```
Three `cache_control` breakpoints (max 4). Verify with `usage.cache_read_input_tokens` in CI — a zero
read rate across repeated requests means a silent invalidator (a timestamp, unsorted JSON) crept in.
Prompt files are content-hashed and pinned (`prompts/narrative/v3.md`, sha256 stored on every
generated narrative): you cannot audit an output whose prompt you can't reproduce.

### Grounding and citation
The drafting call receives an evidence ledger — *only* the artifacts the deterministic engine matched.
Nothing else from the chart reaches it.
```json
{"ref":"E1","artifact_id":"rad_8831","type":"radiograph","view":"PA",
 "tooth_fdi":46,"captured_at":"2026-05-14"},
{"ref":"E4","artifact_id":"note_2210","type":"clinical_note","captured_at":"2026-05-14",
 "confirmed":true,
 "quote":"46 MOD amalgam fractured, distolingual cusp missing, tooth vital to cold"}
```
Output is structured, not prose:
```json
{"sections":[{"heading":"Clinical findings",
              "sentences":[{"text":"...","evidence_refs":["E1","E4"]}]}]}
```
A deterministic validator runs before the draft is ever shown:
1. Every `evidence_refs` id resolves to a ledger entry. **Hard gate, 100%.**
2. Every date and numeric token in the text appears in the ledger.
3. Every tooth number mentioned is in `ledger_teeth ∪ requested_teeth`.
4. No sentence has an empty `evidence_refs`.

Violations -> one regeneration with the violations listed -> second failure -> draft surfaced with
offending sentences struck through and flagged. Never silently shipped.

The same trick secures extraction, more cheaply: every extracted claim must include a verbatim
`quote`, checked to be an exact substring of the source note; non-matching extractions are discarded.
A free, fully deterministic hallucination filter that also neutralizes prompt injection from chart
free text — an injected instruction cannot produce a valid quote for a fact that isn't in the note.

### Preventing templated sameness (the audit risk)
Raising temperature is the wrong answer: it produces varied phrasing of identical content, which is
what an auditor actually notices. Five measures:
1. **Content variation, enforced structurally.** Require >=3 distinct evidence refs and >=1
   verbatim-derived clinical finding per narrative. Below that the system refuses to draft and reports
   that the chart is too thin to support a rationale — the honest answer, and arguably the most
   valuable thing it can say.
2. **Per-clinic style profile.** Captured at onboarding from 3–5 of the clinic's own historical
   narratives (with consent): terminology, sentence length, person, abbreviation habits. Layer [3].
3. **Cross-clinic similarity monitor.** SimHash + 5-gram fingerprint of every *shipped* (post-edit)
   narrative; alert when a new draft exceeds a threshold against narratives shipped to other clinics.
   Tracked metric, target: max cross-clinic 5-gram Jaccard on non-boilerplate spans < 0.35.
4. **Edit-rate telemetry.** Median edit distance trending to zero is the audit signature regardless of
   what the prompt says. Internal alert.
5. **No phrase bank, ever.** A library of approved justification sentences is the fastest possible
   path to the exact failure mode we're avoiding.

### Human-review UX contract — a non-skippable state machine
```
assessed -> narrative_drafted -> [clinician opens editor]
         -> EDIT or ATTEST -> attested -> packet_assembled -> exported
```
- Attestation text: *"I have reviewed this narrative and it reflects my clinical judgment and the
  contents of this patient's record."* Recorded with user id, timestamp, sha256 of the attested text.
- **No bulk attest. No "attest all."** One case, one human, one action.
- Packet assembly is blocked until every narrative is attested and every
  `satisfied_pending_confirmation` artifact is confirmed or rejected.
- The exported document is the dentist's statement, not labelled AI-generated to the insurer; our
  internal record carries full provenance (prompt hash, model id, ledger, validator results, diff).

### Canadian data residency — verified, and not what the brief implies
Verified: Anthropic's first-party `inference_geo` accepts only `"us"` and `"global"`, and workspace
geo is US-only and immutable after creation — no Canadian value exists. Vertex AI multi-region
endpoints are `us` and `eu` only, and specific regional endpoints (which would include
`northamerica-northeast1`) support Claude Sonnet 4.6 and earlier only; current-generation models
require global or multi-region endpoints. Bedrock `ca-central-1` serves current-gen Claude via
cross-region inference profiles, which by design span regions.

**There is no path to in-Canada inference for current-generation Claude today.** PLAN.md and
`docs/research/integration-and-compliance.md` §7 carry the general posture; for the reasoning core:
1. `inference_geo: "us"` with workspace `allowed_inference_geos: ["us"]` — accept the 1.1x multiplier
   — plus zero data retention.
2. **De-identify before every model call, enforced at the type level.** The reasoning core never needs
   a name, DOB, health number or address — it needs dates, tooth numbers, codes and findings. Build
   `DeidentifiedCaseView` and make it **the only type the LLM client module accepts.** A `Patient`
   cannot be passed to it; the type checker refuses. Strongest available control, and it is free.
3. Document the cross-border transfer in the privacy notice and PIA. PIPEDA and the provincial health
   privacy statutes permit cross-border processing with comparable protection and transparency — they
   do not mandate in-Canada storage. Whether a specific provincial health authority contract requires
   in-Canada processing is a legal question: escalate before the first clinic, not after.
4. Keep the provider abstraction clean so a Canadian endpoint can be swapped in when one exists.

Sequencing relief: development runs entirely on fictional data with no PHI, so this is a pre-pilot
blocker, not a day-one one.

**Effort: 4 ew (extraction + validators) + 5 ew (narrative + review UX) = 9 eng-weeks.**

## 4. Readiness scoring

**No probability.** We have no outcome data, and inventing a percentage would be wrong and — given the
audit environment — arguably a misrepresentation.

| Per-requirement status | Meaning |
|---|---|
| `satisfied` | Deterministically matched, confirmed artifacts, comfortably inside bounds |
| `at_risk` | Matched, but inside the recency warning band; or via a discretionary path the source calls "will be considered"; or a borderline escalation |
| `satisfied_pending_confirmation` | Matched only via an unconfirmed LLM-proposed artifact |
| `unsatisfied` | Deterministically not matched |
| `indeterminate` | Cannot be decided — missing capture date, undeclared notation, unclassified artifacts |
| `not_applicable` | Rule doesn't apply to this service category |

Overall verdict is an enum, not a score: `PREAUTH_NOT_REQUIRED` · `BLOCKED` (any `unsatisfied`) ·
`NEEDS_INPUT` (any `indeterminate` or unconfirmed) · `READY_WITH_RISKS` (any `at_risk`) ·
`READY_TO_SUBMIT`.

Instead of a fake probability, a completeness counter: *"8 of 9 CDCP requirements satisfied."*
Factual, defensible, directly connected to the published ~20%-incomplete finding. Published base rates
appear in a separate, clearly attributed context panel — *"Health Canada reports approximately 37%
approval for crowns; the most commonly cited denial reasons are missing radiographs, insufficient
clinical notes, and absent periodontal charting"* — **never blended into a per-case number.**

```json
{
  "assessment_id": "asm_01J...", "case_id": "case_01J...",
  "ruleset": { "id":"cdcp-preauth","version":"2026.01.26",
               "content_hash":"sha256:...","effective_from":"2026-01-26" },
  "assessed_at": "2026-09-17T14:02:11Z",
  "submission_date_assumed": "2026-09-17",
  "engine_version": "1.4.2",
  "preauth_required": true,
  "service_categories": ["restorative"],
  "verdict": "READY_WITH_RISKS",
  "completeness": { "satisfied": 3, "applicable": 4 },
  "requirements": [
    { "requirement_id":"perio_chart",
      "status":"at_risk", "satisfied_via":"psr_interim_path",
      "evidence":[
        {"artifact_id":"psr_4420","type":"psr","captured_at":"2026-03-02",
         "age_days":199,"expires_on":"2027-03-02","extraction_method":"db_field"},
        {"artifact_id":"perio_6s_991","type":"perio_measurements","teeth_fdi":[46],
         "captured_at":"2026-03-02","expires_on":"2027-03-02"} ],
      "escalations_evaluated":[
        {"id":"psr_requires_full_chart","fired":false,
         "detail":"Max PSR 3 in 1 sextant (S6). Threshold is 4 in any, or 3 in 2+."},
        {"id":"psr_requires_sextant_chart","fired":true,
         "detail":"PSR 3 in S6, the sextant of requested tooth 46.",
         "demanded":"sextant_perio_charting","scope":{"sextants":["S6"]}} ],
      "risk_reason":"PSR path is discretionary: CDCP wording is 'will be considered'." } ],
  "actions": [
    {"rank":1,"blocking":true,"effort":"chart_entry",
     "action_type":"complete_sextant_charting",
     "title":"Chart sextant S6 (teeth 44-48), 6 sites per tooth",
     "why":"PSR score of 3 in S6 requires that sextant's charting for tooth 46.",
     "unblocks":["perio_chart"]},
    {"rank":2,"blocking":false,"effort":"confirm_in_app",
     "action_type":"confirm_extraction",
     "title":"Confirm treatment plan details found in the 2026-05-14 note",
     "unblocks":["tx_plan_details"]} ],
  "deadlines":[{"artifact_id":"rad_8831","expires_on":"2027-05-14",
                "requirement_id":"radiographs_pa_bw"}],
  "notes":["CDCP asks providers to allow a minimum of two weeks for processing.",
           "Avoid duplicate submissions for the same case."]
}
```
Action ranking is deterministic: `(blocking desc, unblocks_count desc, effort_ordinal asc,
requirement_id asc)`. The trailing tiebreak matters — without it the action list reorders between
identical runs and the UI looks broken.

## 5. Packet assembly

Target: **<=30 files, <=7 MB.** Radiographs/B&W: 8 or 16-bit greyscale, 150–300 DPI inclusive.
Intraoral/colour: 16/24/32-bit colour, 300–600 DPI inclusive. Documents: ASCII text or Microsoft Word.
Accepted in practice: TXT, DOC, DOCX, JPG, PNG, PDF, TIF.

### Image rendering
Pillow for raster; `pikepdf`/`pypdf` for PDF; `img2pdf` where a PDF wrapper is needed without
recompression.
- **DPI is metadata plus pixel dimensions — you cannot create it.** If native pixels / physical sensor
  dimensions falls below 150 DPI it fails spec and we say so. We do not upsample to fake compliance:
  resampling a diagnostic image to satisfy a metadata check is useless and arguably misrepresentation.
- Above 300 DPI: downsample with Lanczos into the band. Write the DPI tag correctly
  (`save(..., dpi=(x,y))`; for TIFF also set `resolution_unit`).
- Bit depth: radiographs -> Pillow mode `L` (8-bit) or `I;16`. The common real-world failure is a
  greyscale x-ray stored as a 24-bit colour JPEG by the imaging bridge — detect it (all channels
  equal), convert to `L`, and record the conversion in the manifest.
- Colour intraorals -> RGB/RGBA, 300–600 DPI. **Never re-encode a radiograph lossily** (PNG, or JPEG
  q>=95).

### Documents
The written spec says ASCII text or Microsoft Word, so the narrative ships as DOCX (`python-docx`)
with a TXT fallback — not PDF, even though PDF is accepted in practice. If the spec says Word, ship
Word. **"ASCII text" is literal:** the TXT renderer must transliterate `é`, em-dashes and curly quotes
rather than emit UTF-8 — use `unidecode` and assert `text.isascii()` before writing. This will bite on
the first Québécois patient name if you skip it.

### The 30-file / 7 MB budget
Greedy solver over candidates tagged `{required, priority, requirement_ids, min_acceptable_spec}`.
Over budget, in order:
1. Recompress colour photos only, q95 -> q85. **Never radiographs.**
2. Drop *optional* and duplicate-hash evidence, lowest priority first.
3. Merge multiple text documents into a single DOCX (saves file slots).
4. **Stop. Do not drop a required artifact.** Fail with an explicit blocking error listing every file
   and its size; let the human decide. Splitting across submissions is not an option — CDCP explicitly
   asks providers to avoid duplicate submissions.

### File naming
```
{seq:02d}_{requirement_id}_{artifact_type}_{descriptor}_{captured_at}.{ext}
03_radiographs_pa_bw_radiograph_PA-46_2026-05-14.png
07_perio_chart_psr_sextants-S1-S6_2026-03-02.pdf
```
**No PHI in filenames.** Filenames get logged, appear in email subjects, show up in screenshots.
Patient identity belongs in the claim form, which is where the insurer looks for it.

### Manifest
`manifest.json` (machine, retained with the case forever) plus `00_index.txt` (ASCII, shipped as file
1 of 30). Spending a file slot on an index is worth it: it directly addresses the "insufficient
documentation" denial reason by telling the adjudicator what they're looking at. Per file: `{seq,
filename, sha256, bytes, requirement_ids, artifact_id, captured_at,
spec_checks:{dpi,bit_depth,format,pass}, transformations_applied:[...]}`, plus packet-level ruleset
version, engine version, narrative prompt hash, attestation record.

### The independent verifier
**A separate program, written by a different engineer than the assembler,** that opens every file in a
finished packet from scratch and re-checks DPI, bit depth, format, per-file integrity, file count and
total bytes. It shares no code with the assembler — deliberate redundancy, because the assembler
asserting its own output is compliant is not evidence.

**Effort: 4 eng-weeks** including the verifier.

## 6. Evaluation harness — first class

With no clinic and no submission outcomes, **the eval harness IS the correctness argument.** Build it
in parallel with the engine, not after.

### 6.1 Golden corpus — 120 cases at v1
`evals/corpus/cases/`, built on ABELDent Freemium fictional data as substrate, labelled by the dental
billing SME. Each case: `case.yaml` (canonical chart + proposed treatment) and
`expected/{ruleset_version}.yaml` (per-requirement status, overall verdict, top-3 ranked actions,
expected packet file count). Expectations are keyed by ruleset version — old cases keep old
expectations when a new pack lands. Distribution: >=8 per service category (64) + 56 adversarial.

**Reconciled v1 budget: PLAN.md cuts this to 60 cases (40 crown + 20 adversarial)**, growing
continuously after launch. The 120-case distribution above is the shape it grows back toward.

Build a `casegen` DSL first. The SME writes `radiograph: {view: PA, tooth: 46, age: 364d}`, not raw
JSON. This is the difference between a corpus built in days and one built in weeks, and it determines
whether the corpus keeps growing after launch. Worth 1 eng-week, pays back in month two.

Operational note: ABELDent Freemium is Windows-only with no official API. Budget a one-time ODBC/SQL
extraction into fixtures rather than a live integration — the golden corpus should be static files in
the repo, not a live dependency on a Windows VM.

### 6.2 Per-requirement unit tests (`hypothesis` property tests)
- Recency: for random `(captured_at, as_of, bound)`, the predicate is monotone in age and
  boundary-exact.
- Sextant mapping: exhaustive over all 32 FDI positions.
- Notation conversion: round-trip FDI <-> Universal <-> Palmer is lossless; ambiguous inputs raise
  rather than guess.
- Boolean solver: `one_of` with all options failing returns the lowest-`remediation_cost` near-miss.

### 6.3 Adversarial set (56 cases at v1 design; PLAN.md cuts v1 to 20)
The list below enumerates roughly 20 scenarios — the v1 cut, not the full 56. The rest get written
against the same axes as the corpus grows.
Radiograph at exactly 364 / 365 / 366 days · the leap-year calendar-months-vs-365-days disagreement
band (must yield `at_risk`) · PSR exactly 4 in one sextant; exactly 3 in exactly one; exactly 3 in
exactly two; 3 in the requested tooth's sextant only; **both escalations firing together (precedence)**
· perio chart covering 28 of 32 teeth, missing the requested tooth, and missing a non-requested tooth
· BW right present, left absent · **pano from 2019 for RPD must PASS** (footnote 5 has no recency
bound) vs pano from 2019 for oral surgery must spawn the footnote-3 rationale requirement · two
"separate" arch photos that are the same file by hash · source declares Universal notation, tooth
written as "16" · artifact with `recorded_at` but no `captured_at` -> `indeterminate`, never pass ·
treatment plan info embedded in a clinical note rather than a labelled document (footnote 1) · stone
models: satisfies the rule, cannot be packed · a case where preauth is **not** required at all · a
plan straddling two categories (endo + crown on the same tooth) · 31 candidate files; 7.2 MB packet ·
x-ray stored as 24-bit colour JPEG · chart with >10% unclassified artifacts -> `NEEDS_INPUT`, not
`BLOCKED`.

### 6.4 Rule-version regression
`ruleset shadow-run` replays the full corpus plus all stored historical cases against a draft pack and
emits a verdict-delta report. **Publishing is blocked until every changed verdict is explicitly
acknowledged by the SME with a written reason.** Highest-value, lowest-cost safety mechanism in the
system: it converts "we changed a rule and silently broke 40 cases" into a reviewed diff. The April
2026 update is exactly the shape of change this catches.

### 6.5 LLM output evaluation
| Metric | Method | Gate |
|---|---|---|
| Citation validity | Deterministic — every `evidence_refs` id resolves | **100%, hard** |
| Quote literalness | Deterministic — exact substring of source note | **100%, enforced at runtime** |
| Unsupported-claim rate | `claude-sonnet-5` judge, sentence-level, sees narrative + ledger only | **< 2%** of sentences by SME label on a 200-sentence sample |
| Judge trustworthiness | Cohen's kappa vs 100 SME-labelled sentences | **kappa >= 0.7** before the judge is believed |
| Extraction precision / recall | vs SME-labelled notes, per claim type | **precision >= 0.95, recall >= 0.90** |
| Cross-clinic templating | max 5-gram Jaccard on non-boilerplate spans | **< 0.35**; report the full distribution, not just the max |
| Clinical-claim refusal | ~40-prompt red-team set attempting to elicit diagnosis / prognosis / medical-necessity assertions | **0 leaks** |

Precision gated higher than recall deliberately: a false positive that a busy clinician rubber-stamps
produces a wrong submission; a false negative produces a manual check.

### 6.6 "Good enough to put in front of a clinic" — the numbers
1. **Deterministic layer, golden corpus:** per-requirement status exact-match **>= 99.0%**; overall
   verdict exact-match **= 100% on the adversarial set.** The deterministic layer is code — anything
   under 100% on adversarials is a bug, not a metric. The 99% band exists only for genuinely ambiguous
   cases correctly marked `indeterminate`.
2. **Zero false `satisfied`.** Costs are wildly asymmetric: a false `unsatisfied` costs a clinic five
   minutes; a false `satisfied` costs a denial, a resubmission against explicit "avoid duplicates"
   guidance, and our credibility. Tracked separately; gate is 0 in the corpus, and the engine must
   structurally prefer `indeterminate` over `satisfied` under uncertainty.
3. Citation validity 100%; unsupported-claim rate < 2%.
4. Packet spec compliance 100% per the independent verifier.
5. Latency: p95 assessment < 20 s excluding narrative; narrative < 60 s.
6. **The real gate — SME dry run.** 30 unseen cases, pre-registered rubric: **>= 27/30 the SME agrees
   both the verdict and the top-ranked action are what they would have done.** Metrics 1–5 are
   necessary; this one decides whether we ship.
7. First clinic runs in shadow mode for two weeks — real charts, nothing shown to the user, SME
   reviews every divergence. Then reveal.

**Effort: 6 eng-weeks** (harness + casegen + corpus v1 + LLM eval), run in parallel from M1.

## 7. Failure modes and guardrails

### What the system must refuse to assert
- **Any probability or likelihood of approval.** No outcome data exists. Not "likely approved," not a
  confidence bar, not a traffic light that implies odds.
- **Any diagnosis, prognosis, or statement of clinical necessity in its own voice.** Never *"Tooth 46
  requires a crown."* Always *"The record dated 2026-05-14 documents [quoted finding]. The treatment
  plan dated 2026-05-14 proposes [code]."*
- That anything is approved, covered, or eligible. Only: *"CDCP requires document X for this service
  category under the ruleset in force on [date]."*
- That a document exists when only a model proposed it.
- Clinical advice to a patient. Ever.
- Anything about a ruleset version other than the one it evaluated against.

### Staying out of medical-device territory
Health Canada's SaMD framing turns on whether software is intended to diagnose, treat, prevent or
mitigate disease, or to support clinical decision-making in a way the clinician cannot independently
review. **Ophi's defensible position:** an administrative/billing documentation-completeness tool
operating on a payer's published documentation requirements, making no clinical determination, where
every clinical statement surfaced is a restatement of the clinician's own chart entry with a pointer
to it, reviewed and attested by that clinician.

Enforced in code:
- **The grounding validator is a safety control, not a quality control.** It is why no ungrounded
  clinical statement can leave the system. Regressions in it are SEV-1.
- Never rank or recommend treatment. Never suggest adding a finding to the chart. The action list may
  say *"a complete periodontal chart is required"*; it may never say *"chart a 5 mm pocket on 46."*
  Enforceable because actions are template-rendered from rule metadata, not generated.
- Read-only against the PMS. The system never writes to a chart.
- Attestation is non-skippable and non-bulk.
- Product copy discipline: "documentation completeness," not "approval likelihood." "Copilot," not
  "clinical decision support." This matters as much as the code.
- **Get a written legal opinion before the first paying clinic.** Start it in month one.

### Other failure modes
| Failure | Guardrail |
|---|---|
| **Stale ruleset** — CDCP updates, we don't notice | Weekly job fetches the canada.ca source, diffs its hash, alerts the SME. If the pack's source hasn't been re-verified in N days, degrade to a banner and **refuse to emit `READY_TO_SUBMIT`.** (~0.5 ew; converts "found out late" into an alert.) |
| **Silent ingestion drift** — PMS schema change makes artifacts vanish; we report "missing radiograph" when one exists | Per-chart artifact-count sanity check plus an always-visible "unclassified artifacts" bucket. If >10% of a chart's artifacts are unclassified, the verdict is `NEEDS_INPUT`, not `BLOCKED`. **Never let an ingestion gap masquerade as a clinical gap.** |
| **Duplicate submissions** | Track `case_id -> submitted_at`; hard warning on re-assembly for a case already marked submitted. Surface the two-week processing expectation as a follow-up date. |
| **Prompt injection from chart free text** | Note text never reaches the system prompt. Delimited, `strict` output schema, plus the substring-verification filter — **a structural defence, not a prompt defence.** |
| **PHI leakage into logs or the repo** | `DeidentifiedCaseView` type boundary at the LLM client; pre-commit PHI/secret scanner; dev environment gated to refuse non-fictional data sources; structured logging that cannot serialize a `Patient`. |
| **Model/API drift** | Pin model IDs in config, not code. Every assessment records model id, prompt hash, engine version, ruleset hash. Full eval suite runs against any model change before it ships. |
| **USC&LS licensing** | Licensed from CDA (`uscls@cda-adc.ca`), **must not be redistributed in a public repo.** Code sets live in a private package seeded from the licensed file; open code references codes by id only. **Procurement lead time — start first.** |

## Sequencing and effort

| Phase | Workstream | Eng-weeks |
|---|---|---|
| 0 | Canonical model, notation + sextant libraries, ruleset schema + linter | 5 |
| 1 | Rule engine, matcher, version store, shadow-run job | 8 |
| 2 (parallel with 1) | **Eval harness, casegen DSL, golden corpus v1, adversarial set** | 6 |
| 3 | LLM extraction + substring validator + escalation path | 4 |
| 4 | Narrative drafting, grounding validator, review/attestation UX | 5 |
| 5 | Packet assembly, image spec normalization, independent verifier | 4 |
| 6 | Publish gate, Rules Explorer (read-only), drift watcher, anti-template monitor | 4 |
| | **Total** | **36** |

Cut list if over scope (in order): the full Rules Studio editor (already deferred), expiry
forecasting, physical-delivery/stone-model handling, the LLM "explain this" panel, Palmer parsing.

**Must not be cut under any circumstances:** the eval harness, the grounding validator, the
independent packet verifier, the attestation step, zero-false-`satisfied`.

## Unverifiable assumptions
1. **The April 2026 rule-change claims** are not reflected on the current canada.ca preauthorization
   page, which shows a January 2026 date and the same eight service categories. Those changes likely
   live in the Dental Benefits Guide rather than the supporting-documentation matrix. Have the SME
   confirm which document governs before pack 1 is published — determines whether the ruleset needs
   one source or two.
2. **Calendar-months vs 365-days recency.** Unpublished. Handled by returning `at_risk` in the band.
3. **Whether footnote 6's rationale-in-lieu-of-charting extends to crowns/endo.** The table does not
   say. Encoded as explicit `policy_decision` PD-004 (decision: no) so it is visible and revisable
   rather than buried.
4. **The CDAnet DPI/bit-depth bands are what the standard says; adjudicator tolerance is unknown.**
   Build to spec, record every transformation.
5. **Canadian inference residency is currently impossible** (verified). Legal sufficiency of US
   processing under the relevant provincial regime is a legal question, not an engineering one.
6. **ABELDent Freemium** is Windows-only with no official API. Extract fixtures once; no live
   dependency.
7. **Published approval rates** (46% overall, 37% crowns) are attributed context only and never enter
   a computation.
