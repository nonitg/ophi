# Internal app redesign — 2026-09-24

Full redesign of `ophi/web`, the app a dentist and a treatment coordinator use and the MVP we demo.
The public site (`site/`, `DESIGN.md`) is untouched.

The owner's brief: the app was "messy, inconsistent and unclear", "a bunch of lists, messages, errors and
so much text everywhere", and it did not "show the sense of the scale of what we're doing". Wanted: a clean
UI in Moxo's design language (`docs/plan/04-app-restyle-moxo.md`), where it is easy to see what is going
on, what needs approval and the overall status, balancing looks with function and data.

## What changed

| Screen | Before | After |
|---|---|---|
| Chrome | Black demo band, blue links, "Acting as" select with the full role and licence | Stone demo band, the ophi wordmark, underlined current tab, a person menu with a monogram |
| Queue | Headline, then a list; each row had a pill, one action and a mini bar | Headline, then five stages with counts and dollars (Blocked, Needs input, Ready to sign, Signed, Submitted). A **Waiting on you** line changes with the person acting. Rows show the next step, who the case waits on (monograms), the appointment countdown, the requirement strip grouped Chart / Limits / Clinical, and the fee |
| Case Review | Verdict card, a numbered gap list with paragraphs, three folds | Verdict panel with the grouped strip. **Next steps** splits open work by who acts, with the acting person's lane first: the coordinator's chart items, the dentist's clinical steps and criteria (as chips). The first item is the hero with its "why" and clause; every other item keeps its rule detail and fired escalations in **Details**. **Hands off to** ends every case: the dentist signs, the clinic submits, Ophi never transmits. The **Documented** fold lists each settled requirement with its evidence, date, age and source, behind a one-line count. The aside holds **What Ophi did** (entries, subsystems, requirements, clauses) and a **chart timeline** of every dated entry against the 12-month window |
| Clinical criteria | Disabled form for the coordinator; for the dentist, a fold at the bottom of the page | For the dentist, the form opens right under Next steps, with segmented Met / Not met / N/A controls and in-place validation instead of `alert()`. The coordinator gets a read-only list and one-click **Switch to Dr. Priya Lau** |
| Packet | Verdict card, PDF, a long narrative textarea, sign-off card | One sentence (draft, ready, blocked or signed), then a four-step rail: assembled by Ophi, checked by the verifier, sign-off by the dentist, submission by the clinic (past tense only once done). The sign-off card leads, then files with a spec check each; the narrative editor and evidence currency sit in folds |
| Look-back | Four numbers, a 34-row table | The same four numbers as a chain, a month chart with one square per request (denied with a missing document, denied with no gap, never resubmitted), bars ranking the missing documents, and a compact table |
| Settings | Dense cards and an audit table | Connection, who can act (and what each role does), the rule pack with every requirement's clause, and the audit log as an actor trail |
| Errors | A plain card | Same message, with **Go back** and **Open the queue** |

## Design language

Tokens live in `:root` in `ophi/web/static/app.css`; `scripts/app-contrast.py` checks every pair below.

| Token | Value | Use | Contrast |
|---|---|---|---|
| `--paper` | `#ffffff` | page, cards | — |
| `--linen` | `#f7f6f3` | quiet fills: inbox line, chips, hover, hand-off band | — |
| `--stone` | `#efebe3` | frames: the verdict panel, the PDF frame | — |
| `--ink` | `#3e3c3a` | text, primary buttons | 10.98 paper, 9.24 stone |
| `--ink-strong` | `#22201f` | names, titles | 13.65 stone |
| `--muted` | `#6b6862` | secondary text | 5.55 paper, 4.67 stone |
| `--faint` | `#8d8984` | zero counts only, set at 30 px | 3.47 paper |
| `--ok` / `--bad` / `--ask` | `#2c7549` / `#b3261e` / `#8f5a00` | status only: documented, missing or stale, awaiting a person | ≥ 4.8 on their tints and on paper |

- **Type:** Geist and Geist Mono, variable, self-hosted in `ophi/web/static/fonts/` (OFL, licence file next to them) so a practice server with no CDN access renders the same. Display sizes use light weights (320–380), body 14 px at 400. Mono carries dates, codes, counts and hashes.
- **Colour means status.** Everything else is ink, muted ink, paper, linen or stone. Status headlines are ink; the pill and the strip carry the colour.
- **One vocabulary:** Blocked, Needs input, Ready to sign, Signed, Submitted, on the stage rail, the row pills and the verdict pill. One task table (`present.TASK_KINDS`) names who owes what (chart gap, item Ophi cannot verify, chart finding to confirm, clinical step, clinical criterion) for the headline, the lanes, the queue chips and the inbox.
- **Families:** Chart, Limits (age, tooth, frequency) and Clinical. Not "Eligibility": four green ticks under that word read as "eligible", which the copy law bans.
- **Shape encodes rank:** frames 18 px, cards 12 px, controls 9 px, chips 6 px, pills round. The only shadow is on cards that sit on stone.
- **Small caps are data, not decoration:** status pills, counts and the hand-off label only. Headings are sentence case with no eyebrows. A heading's second half, in muted ink, gives context ("Crown preauthorizations Week of Sep 14–18").
- **Shape carries status too:** large strip cells carry a check, a cross or a question mark; "cannot verify" is an outlined cell and "awaiting confirmation" is hatched, so the strip reads without colour.

## Where this departs from plan 04

- Structure changed, not only the skin: open work is grouped by who acts, and documented requirements get their own card instead of the old fold of all 13.
- Added what the plan did not have: the stage rail with dollars, the Waiting on you line, the chart timeline, the What Ophi did tally, the packet rail, and the look-back month chart and gap bars.
- The verdict headline is ink, not status-coloured. The pill and the strip carry the colour.
- Time-in-state is still not tracked. Rows show the appointment countdown instead (the plan's option a).
- No stone texture, as the plan recommended.

## Accuracy fixes the redesign surfaced

- **Unseen is not missing.** Rosco's periapical, bitewings and claim form are `indeterminate` because the source cannot see imaging or the CDCP client ID is missing. The old bar and legend labelled every `indeterminate` requirement "Awaiting dentist". `present.status_of` now reads "Cannot verify" when the action that settles it is not a dentist's assertion; the timeline says "Not visible to the source", and empty evidence lists say "Not visible to the connected source (Unknown)" instead of "None in the chart" (`evidence_panel(...)["empty"]`).
- **Who owes the work.** Clinical steps (a pending filling, a criterion recorded as not met) are the dentist's, not the coordinator's. The dentist's criteria are counted from the engine's shortfall, so one "Not met" answer no longer hides the criteria still unanswered.
- **The 12-month window** on the timeline comes from the engine's recency rule (calendar months and 365 days), so an at-risk entry such as `pa_leap_band`'s periapical draws inside it with an amber ring.

## Verification

- `make test`: 477 passed. `make eval`: 45 cases, PASS, false-ready 0. The copy-law test now reads only Ophi's own voice (it skips chart quotes, clause chips and rule ids), matches `eligib*` and `coverage` as well, and runs every screen for both roles.
- `scripts/app-flow.py`: a click-through of the demo passes. It resets the state, confirms Tremblay's proposed finding as the coordinator, switches to the dentist from the case page, gets the in-place message on an incomplete record, records every criterion, signs, downloads the zip, marks it submitted, and sees Submitted on the queue and in the audit log.
- `scripts/app-overflow.py`: no sideways scroll at 390 px or 320 px, on every screen and for both roles.
- `scripts/app-contrast.py`: all 22 text and mark pairs pass (4.5:1 for text, 3:1 for large text and marks).
- `test_every_strip_cell_links_to_one_row_on_the_page`: every strip cell on all six cases links to exactly one row.
- Words a viewer sees, from `scripts/app-words.py` (1440 × 900, closed folds left closed). The count above the fold is about the same on Queue and Case Review, but it is now labelled data in rows rather than paragraphs:

| Page | Above the fold, before → after | Whole page, before → after |
|---|---|---|
| Queue | 230 → 264 | 230 → 289 |
| Case Review (Singh) | 249 → 235 | 295 → 349 |
| Packet (Whitfield) | 682 → 182 | 717 → 232 |
| Look-back | 288 → 234 | 652 → 747 |

## Tools added

`scripts/app-serve.sh` restarts a throwaway-state preview on :8799. The other tools are
`app-shot.py` (one page), `app-shots.py` (every screen, both widths, through sign-off), `app-flow.py`,
`app-overflow.py`, `app-contrast.py` and `app-words.py`.

## Not done

- No layout variants were offered. The owner asked for the redesign to be finished without further approvals; variants of the queue board can follow if wanted.
- The packet preview is still the browser's PDF viewer. Headless Chromium draws it blank in screenshots, but Chrome and Safari render it.
- Dark mode stays out of scope.

## Review

A fresh-context agent reviewed the redesign before commit against the brief, plan 04, the copy law, the
glance record and CLAUDE.md. It ran the suite, the eval, the flow, the contrast and overflow checks, and
rendered all 44 cases (demo and adversarial) for both roles. It made 15 findings. All were fixed:

| Severity | Finding | Fix |
|---|---|---|
| Blocker | The family label "Eligibility" reads as "eligible"; the copy-law regex missed it | Renamed to "Limits"; the test now matches `eligib*` and `coverage` in Ophi's own voice |
| Major | Unseen sections still said "None in the chart" | Empty lists name the source's availability |
| Major | Clinical steps counted as coordinator chart gaps; a "Not met" answer hid the unanswered criteria | One task table for every screen; criteria counted from the shortfall; test on the Not-met state |
| Major | The packet rail said "Signed by" before signing, and the packet lost its opening sentence | Present tense until done; one sentence under the title |
| Major | Fired escalations and requirement detail were no longer shown | Kept in each open item's **Details** |
| Major | Case Review ran over the glance budget | Documented folded behind a count; the acting person's lane leads |
| Minor | Weak focus ring on checkboxes; the segmented control needed `:has()`; the timeline redrew the 12-month rule; anchors hid under the sticky header; route-level logic and orphans; the Waiting-on column was hidden from screen readers and phones; a submitted case still said "submit it" | Scoped the soft ring to text fields; radio + span markup; window from `recency.check`; `scroll-margin-top`; `stage_rail` and `handoff` in the presenter with tests; screen-reader text and a phone slot; a submitted headline |
| Nit | Dead or split CSS; copy slips in the machine line, the Next steps count, the target highlight, the role ternaries and the audit timestamps | Removed or merged; fixed |
