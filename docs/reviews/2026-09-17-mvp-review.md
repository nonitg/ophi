# MVP review — 2026-09-17

Fresh-context review of the MVP against `PLAN.md`, `docs/plan/02-reasoning.md`, `docs/plan/03-product.md`
and `docs/research/cdcp-rules.md`, run read-only by a separate agent before the slice-closing commit.
Full findings were 24 items plus nits; this records what was found, what changed, and what stands.

## Verdicts by question

| Question | Verdict | Notes |
|---|---|---|
| Architectural commitment (deterministic verdict, indeterminate over satisfied) | pass with notes | No path to a false READY found; corpus false-ready gate is 0/45 |
| Rules fidelity vs `cdcp-rules.md` | pass with notes | All 14 requirements and the schedule block match; open SME questions listed in `architecture.md` |
| Copy law | pass with notes | Two own-voice phrasings fixed (see below) |
| Human-review contract | **fail → fixed** | Four majors, all addressed |
| Verifier independence | pass with notes | Copy-law scan extended to the narrative |
| PHI hygiene | pass with notes | Demo case ids are surnames (URLs, zip names); production ids are opaque PMS keys |
| Demo readiness | pass with notes | Singh beat did not render as scripted → fixed |
| Code standards / duplication | **fail → fixed** | Endo detection and variant selection now single-sourced |
| Tests | pass with notes | Service-layer tests added |
| Docs | pass with notes | Ranking key and open questions recorded |

## Majors and what changed

1. **Singh's key sentence never rendered.** The fixture carried a 2023 periapical, so the engine took the
   stale-PA branch and the bitewing near-miss sentence never fired. Fixture now has bitewings only; the
   sentence is the top action's explanation; the demo script's case table was corrected.
2. **Packets could be built and downloaded unsigned for a blocked case.** Manifest now carries
   `status: draft|signed` and `verdict`; the index header says DRAFT until signed; the verifier has a
   `status_consistent` check and a `shippable` flag; the download route refuses until the treating
   dentist has signed this exact assessment.
3. **The grounding / copy-law validator was never run in the product path.** `save_narrative` and
   `sign_off` now run `validate_narrative` and refuse with the violations listed; the verifier scans the
   narrative outside quotation marks for copy-law tokens.
4. **Endo-treated detection written four times; variant selection three times.** Now `Case.tooth_is_endo_treated()`
   and `assertions.criteria.extensively_restored_variant()`; evaluate, narrative and the web presenter call them.
5. **Dentist-only sign-off enforced only in the web layer.** The service takes a `role` and refuses
   non-dentists for assertions and sign-off.
6. **A sign-off survived a chart change.** `CaseView.signed` now requires the stored assessment id to
   equal the current one; the packet screen explains a voided sign-off.

## Minors addressed

Explicit crown code list for frequency facts (not prefix 27); cores/posts excluded from "pending basic
treatment"; claim form requires CDCP client ID and date of birth on file; the 6.1.2 quote attributed to
the Guide; "Cannot verify: …" and "Establish the capture date …" titles for indeterminate facts;
"Check the imaging software" titles no longer say "take"; at-risk explanations use the recency detail;
Look-Back counts only confirmed gaps and reports unverifiable sections separately; payer-behaviour notes
attributed; "not open to reconsideration"; the bitewing near-miss sentence moved from Python into the
pack (`gap.near_miss_why`); severity ordering reused from one table; dead `expiry_of`, empty `sources/`
package and ImportError fallbacks removed; packet page reuses the packet on disk when nothing changed.

## Left standing, on purpose

- Demo case ids are surnames for URL readability. Nothing else carries identity; production ids come
  from the PMS.
- `Workload.elapsed_ms` is wall-clock and excluded from the determinism test.
- Stale radiograph in a `Degraded` imaging section reads `unsatisfied` (take a PA) rather than
  `indeterminate`; the action is right either way.
- `PLAN.md` status block still says "No product code yet" — owned by the lab session.
- The "extensively restored" surface counts and "active periodontal disease" remain clinician assertions;
  the plan puts them there deliberately.
