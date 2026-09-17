# Architecture — MVP

What was built, how the pieces fit, and where this MVP deliberately differs from `PLAN.md`.

## One sentence

A rule pack (data) is evaluated by a deterministic engine over a typed artifact index built from a
patient's chart; humans add assertions and confirmations; the engine re-runs; a packet is assembled
and independently verified; the dentist signs; staff submit.

## Data flow

```
casegen YAML ──► Case (CDM) ──► proposer adds unconfirmed TX_PLAN_DETAILS ──► + user assertions/confirmations
                                                                                      │
                                                    RulePack (YAML, hashed) ──► engine.assess ──► Assessment
                                                                                      │
                     web screens ◄── service.CaseView ◄───────────────────────────────┘
                          │
                          ├── packet.build ──► out dir (index, form, plates, perio, narrative, manifest, preview.pdf)
                          └── verify.verify_packet (separate code) ──► VerifyReport
```

## The pieces

**CDM (`colombus/cdm`).** FHIR names where they exist, dental-first where FHIR is weak (`PerioExam`,
`DentitionState`). Every artifact carries `Provenance`; every section carries `SourceAssurance`
(`Present | AbsentConfirmed | Unknown | Degraded`). Tooth numbers are FDI internally; the number as
written and the declared notation are kept so nothing is inferred from "16".

**Rule pack (`packs/cdcp/<version>/pack.yaml`, `colombus/rules`).** Two layers. `schedule` mirrors
the grid: which codes always need preauth, the code family, exclusions, frequency limits, retired
codes. `requirements` encode the documentation matrix and the Guide's crown criteria using a closed
vocabulary: `find` (artifact query), `fact` (deterministic predicate over case fields), `one_of`,
`require_all`, `not_escalated`, `provided_by_packet`, plus `escalations` (PSR thresholds that demand a
different requirement) and `applies_when`. Every requirement and every assertion criterion cites its
clause. The loader hashes the YAML; every assessment records the hash.

**Engine (`colombus/engine`).**
- `leaves.py` resolves `find` queries: radiograph by view/tooth/laterality, complete perio chart (6
  sites on every present tooth), PSR coverage, 6-site measurements for the requested tooth (and any
  sextant an escalation demanded), clinician assertions. Absent evidence is `unsatisfied` only when
  the source vouches for the section; `Unknown`/`Degraded` yields `indeterminate`.
- `recency.py` evaluates 12 calendar months and 365 days; disagreement yields `at_risk`. Every match
  carries `expires_on`.
- `facts.py`: age, tooth class, adjacent molars missing, per-tooth and per-client frequency, pending
  basic treatment, retired lab codes.
- `evaluate.py`: escalations first (precedence order), then the boolean tree. `require_all` takes the
  worst status; `one_of` takes the best, and when nothing passes reports the cheapest, closest
  near-miss with its shortfall.
- `assess.py`: schedule gate → verdict enum → ranked actions → deadlines → completeness counter.
  Action order is `(blocking desc, status severity: unsatisfied before indeterminate/pending/at_risk,
  unblock count desc, effort asc, requirement id asc)` — the plan's key plus one tier so that evidence
  that is actually missing outranks things a human only has to confirm. When no preauthorization rule
  applies (code outside the pack, or a listed exclusion) the crown requirements are marked
  `not_applicable` rather than evaluated, so the engine never invents gaps for a filling.

**Proposer (`colombus/extract`).** Heuristic sentence matcher for plan language in signed-off notes.
Every proposal carries a verbatim quote checked as an exact substring; otherwise it is dropped.
Proposals produce `satisfied_pending_confirmation` until confirmed. `DeidentifiedNote` is the only
input type a model-backed proposer may accept.

**Service (`colombus/service.py`).** Loads a case via `PmsRepository`, applies stored human inputs as artifacts, re-runs
the engine. Assertions and confirmations invalidate any prior sign-off. Sign-off is refused unless the
verdict is READY. Append-only audit log.

**PMS abstraction (`colombus/sources/pms_repository.py`).** Repository pattern over all PMS reads.
`PmsRepository` is the protocol; `FileSystemPmsRepository` wraps `casegen/dsl` (YAML cases, the
default), `AbelDentPmsRepository` wraps `lab/tools/chart_dump.py` (live ABELDent VM), and
`MockPmsRepository` reads `mocks/*.json` + `mocks/pms/*.json`. `CaseService` accepts an injected
`repository` or picks one via the env toggle `USE_MOCK_PMS_API` (aliases `USE_MOCK_DATA`,
`PMS_USE_MOCKS`; truthy `true/1/yes/on/y`). Factory: `create_repository("auto"|"mock"|"filesystem"|"abeldent")`.
See `mocks/README.md` and `docs/pms-basics.md` — Toggling real vs mock.

**Packet (`colombus/packet`) and verifier (`colombus/verify`).** Assembler writes an ASCII index,
the treatment form (the one file that carries patient identity), image plates (8-bit greyscale PNG,
150–300 DPI, never upsampled), a perio table, the rationale as DOCX + ASCII TXT, and `manifest.json`
with sha256/bytes/spec checks per file. The verifier reopens every file with no shared code and
re-checks the CDAnet limits (≤30 files, ≤7 MB), image spec, hashes, ASCII, attestation hash.

**Look-Back (`colombus/lookback.py`).** For each past submission, judges the chart as it stood on the
submission date and reports: submitted, denied, denied with a documentation gap, never resubmitted.
Denial text is displayed verbatim but never trusted for classification.

## Statuses and verdicts

Per requirement: `satisfied · at_risk · satisfied_pending_confirmation · unsatisfied · indeterminate ·
not_applicable`. Overall: `PREAUTH_NOT_REQUIRED · EXCLUDED_AS_CODED · BLOCKED · NEEDS_INPUT ·
READY_WITH_RISKS · READY_TO_SUBMIT`. No score, no probability.

## Deviations from PLAN.md, on purpose

| Plan | MVP | Why |
|---|---|---|
| Next.js web app | FastAPI + Jinja2 server-rendered HTML, hand-written CSS | One process, zero build step, offline-capable demo. The screens are the plan's five; the front end can be replaced without touching the engine. |
| Python 3.12 | Python 3.13 (what the machine has) | No 3.12-only dependency. |
| Postgres rule store, 60 s cache | Rule pack loaded from the repo, content-hashed | One pack, one clinic, no deploy pipeline yet. The loading seam (`rules/loader.py`) is where Postgres goes. |
| LLM extraction (Haiku) + Sonnet escalation | Heuristic proposer | Same contract, same verbatim-quote filter, no API key needed for the demo. `Proposer` protocol is the seam. |
| ABELDent driver → CDM | casegen YAML → CDM | The Fictional Data fixture shape is still changing in the lab session (see PLAN.md status). `PmsRepository` (`colombus/sources`) is the seam; `USE_MOCK_PMS_API=true` serves `mocks/` without a VM. The casegen cases are the golden corpus the plan asked for anyway. |
| Verdict `EXCLUDED_AS_CODED` not in the plan's enum | Added | Appendix E exclusions are the highest-value early exit; the plan lists it under "encode with high confidence". |

## Open rule questions for the SME

Surfaced by the adversarial corpus; each is encoded in the safe direction until answered.

1. **Frequency counts any completed 27xxx**, not only CDCP-paid crowns. Over-blocks a pre-CDCP
   private crown. Needs a payer flag on procedure history.
2. **Appendix E exclusions** are encoded only for fixed prosthodontics (6xxxx). 3/4 crowns, veneers,
   inlays/onlays need verified USC&LS code numbers; a 27xxx 3/4-crown code currently lands in
   "confirm the code against the grid".
3. **PSR supersession.** Escalations read the newest PSR within 12 months; the PSR-path leaf may match
   an older complete PSR when the newest lacks a sextant. Does a newer partial PSR supersede?
4. **Recency convention.** 12 calendar months vs 365 days: the one-day disagreement band across a
   leap year yields `at_risk`. Unpublished by CDCP.
5. **Footnote 6 relief** (rationale in lieu of charting) is not extended to crowns — policy decision
   PD-004 in the pack.

## Things the MVP does not do

Transmit to any payer. Read a live PMS. Analyse images. Predict approval. Generate prose with a
language model. Endodontics or any non-crown category. Multi-clinic tenancy or authentication (the
actor dropdown is a demo device).
