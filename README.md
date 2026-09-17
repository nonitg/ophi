# Colombus

CDCP preauthorization copilot for Canadian dental clinics. It reads the proposed crown and the
patient's chart, checks them against the CDCP documentation rules, finds the evidence already in the
chart, names what is missing or stale with the clause that requires it, and assembles the submission
packet. **Staff review and submit. Colombus never transmits.**

Crowns (27xxx) only in v1. Runs entirely on fictional data. No patient information anywhere in this repo.

## Run the demo

```bash
make setup        # python venv + deps (Python 3.12+)
make demo         # http://127.0.0.1:8765
```

Screens: **Queue** (what needs attention this week) → **Case Review** (per-rule verdict, gap
checklist, evidence, Clinician Assertions) → **Packet preview & sign-off** (PDF preview, editable
rationale, attestation, download) → **Look-Back** (last 12 months of denials, re-derived from the
chart) → **Settings & audit**. The demo script is `docs/demo-script.md`.

Other entry points:

```bash
make test                                   # unit, property and golden-corpus tests
make eval                                   # every case in cases/ against its golden verdict; false-ready gate
make assess CASE=cases/demo/singh.yaml      # one case, on the terminal
make packet CASE=cases/demo/whitfield.yaml  # build a packet into out/ and run the independent verifier
make reset                                  # wipe demo state (assertions, sign-offs, audit log)
```

## How it is put together

```
packs/cdcp/2026-01-26/pack.yaml   the rule pack: which codes need preauth, 14 crown requirements, each citing its CDCP clause
cases/demo/                        six casegen cases used by the demo (Friday Five + one "source can't see imaging" case)
cases/adversarial/                 boundary and trap cases with reviewed golden expectations
cases/lookback/                    fictional 12-month submission history for the Look-Back screen
evals/expected/<pack version>/     golden verdicts; `make eval` fails on any change
colombus/cdm                       canonical data model (FDI teeth, Provenance, SourceAssurance)
colombus/rules                     rule pack schema (closed predicate vocabulary), linter, loader
colombus/engine                    deterministic evaluator: leaves, facts, solver, escalations, recency, verdict, ranked actions
colombus/extract                   note proposer (verbatim-quote filter); proposes, never judges
colombus/service                   human inputs (assertions, confirmations, sign-off) + audit log; re-runs the engine
colombus/packet                    packet assembler: index, treatment form, plates, perio render, narrative, manifest
colombus/verify                    independent verifier — shares no code with the assembler
colombus/lookback                  re-derives documentation gaps for past submissions
colombus/web                       FastAPI + Jinja2 app, five screens
```

`docs/architecture.md` explains the decisions. `PLAN.md` is the master plan; `docs/research/` is the
verified rule source and market work.

## The three rules the code enforces

1. **The verdict is deterministic.** Dates, tooth numbers, coverage and thresholds are computed by
   code over a typed artifact index. A proposer may read free text and *propose* evidence; it can only
   ever produce `satisfied_pending_confirmation` until a human confirms.
2. **Prefer `indeterminate` to `satisfied`.** No capture date, undeclared tooth notation, or a source
   that reports a section as `Unknown` never yields a pass. A false "ready" is the one unforgivable error
   and `make eval` tracks it separately.
3. **Copy law.** Colombus never says approved, eligible or covered. It says *"CDCP crown criteria
   require a periapical within 12 months. The most recent periapical of #46 is dated 2023-11-14."*
