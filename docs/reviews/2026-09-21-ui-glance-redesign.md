# UI glance redesign review — 2026-09-21

Fresh-context review of the web UI redesign against the brief ("a dentist or investor must get it from a
15-second screenshot or recording; aesthetics second"), the copy law, the five-screen contract in
`docs/plan/03-product.md`, and CLAUDE.md standards. Run read-only by a separate agent before the
slice-closing commit; 20 findings, all majors and minors addressed.

## What changed and why

| Before | After |
|---|---|
| Case Review: 1,047 words, 2,800 px, three equal-weight columns; the bitewing sentence was one of four same-size gap items and repeated in the requirements column | 403 words; one viewport at 1440×900 for the coordinator view. One verdict sentence, a 13-segment bar of the rule check, the rank-1 chart action as a hero with its "why" and a **Required by** clause chip; dentist confirmations grouped into one item; requirements, chart evidence and assertions in `<details>` folds (assertions open for the dentist) |
| Queue: two action bullets per row, "7 of 12" as text | One sentence headline (cases needing something, dollars at risk); one lead action per row with "+N more"; mini segment bar; code and description kept |
| Packet: verifier line under the PDF; files table and evidence currency as cards | Verdict sentence (draft / ready / signed) with the verifier result in the header facts; files and evidence currency in folds |
| Look-Back: four separate tiles | Same four numbers as one chain; table unchanged (beat 1 depends on it) |
| Unicode glyph status icons, all-caps table headers, eyebrows, 4 px coloured gap bars | Inline SVG marks, sentence-case headers, breadcrumb nav, rank numerals |

Static links now carry `?v=<mtime>`: the first screenshot round showed the old stylesheet because the
browser had cached `app.css` across a code change.

## Review findings and what changed

Major:
1. Signed packet screen said "Verified as a signed packet" even when the verifier failed → the sentence is now gated on the verifier report; the failing branch says so and names the download refusal.
2. Case screen's signed headline claimed "verified and ready to download" though the case view never runs the verifier → now "Download the packet from the packet screen and submit it yourself."
3. The linked segment bar was `role="img"`, which hides its 13 links from screen readers while leaving them tabbable → the linked bar is a `<nav aria-label>`; only the inert mini bar is an image.
4. The case header had dropped procedure code, surfaces, provider licence, planned date and lab codes → code, surfaces and licence back in the facts line; planned date and lab codes on the schedule line inside the requirements fold. The packet header got the code back too.
5. Two `outputs/ui-after` screenshots were stale (pre-cache-buster, grey bar) → every screenshot regenerated from a fresh state after the last code change.

Minor: files-fold wording now describes the actual checks (plate resolution, bit depth, format; packet file-count and size budget); "in under a second" restored on the queue and added under the bar on the case screen; `gap_groups` builds confirmation rows once (no repeated requirement lookups); a test asserts the "(7 criteria)" line; legend entries carry colour swatches and no longer wrap mid-phrase; the amber source note uses the darker amber ink (4.24:1 → passes); the inlined N/A SVG uses the shared macro; the queue shows the procedure code as text; chip focus no longer suppresses the focus ring; placeholder contrast raised; dead capitalisation removed; `.link` renamed `.chain-step`.

Considered and not adopted: inverting the hero so the dental insight ("Bitewings do not image the
periapical region") is the title and the action is the body. Engine `why` prose is not reliably
splittable into a punchy first sentence (Kowalchuk's is a date arithmetic sentence), and the
coordinator's first question is what to do. Instead the hero body is set at 17 px so the insight reads
at near-title weight, and the machine's work ("Colombus read 9 chart entries across 7 subsystems in
under a second") sits under the bar where the eye already is.

## Constraint verdicts

| Constraint | Verdict |
|---|---|
| Copy law (no approved / eligible / covered / likely in Colombus's voice) | pass — test_copy_law_in_colombus_voice green; the two accuracy-of-claim sentences above fixed |
| Nothing functional lost | fail → fixed (facts restored; every control and panel present in folds) |
| CLAUDE.md standards | pass with notes → duplication and test gap fixed |
| Accessibility floor | pass with notes → nav bar, swatches, contrast fixed |
| Out of scope respected (typeface, Look-Back numbers, Settings) | pass |

Tests: full suite green (`make test`), `make eval` 45/45, impeccable detector 0 findings on the changed
files. Browser flow verified with Playwright on a throwaway state: confirm proposal → bulk-record ten
assertions → verdict flips to ready → sign off → download offered → queue shows Signed.
Screenshots: `outputs/ui-before/` and `outputs/ui-after/` (untracked).
