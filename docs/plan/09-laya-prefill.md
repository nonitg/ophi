# Laya in plain sight, and pre-filled criteria

Status: built on `main`, 2026-09-26. Builds on `08-chair-first.md` and the fix plan in `../fix-chart-walkthrough.md`.

## Why

Two gaps. The fine-tuned model was nearly invisible: one grey line of version hashes under the denial risk. And
the dentist's review was the slowest step left: 9 or 10 Met / Not met / N/A answers typed by hand on every crown,
with a "Set the rest to Met" button that ticked rows without weighing the chart.

## What changed

| Before | Now |
|---|---|
| Dentist answers every criterion from scratch | Ophi **pre-fills** a criterion when the chart and Laya's reading of the note back it and nothing contradicts it. Rows group into **Your call**, **Pre-filled from the chart and note**, **Pre-filled from the note** (with "Look at the PA of #24 (May 14), then confirm these"), then **Recorded**. One **Confirm N answers** records them |
| "Set the rest to Met" | Removed. Pre-fills are evidence-backed, and a contradiction always goes to Your call |
| "The note supports it" on some rows | Each row lists its evidence, tagged **Chart** or **✦ Laya** |
| Model = `Models: laya-cdcp … risk-tree …` footnote | A **✦ Laya** chip on every model output: denial risk, fix ranking, pre-fills, board cards. It links to the new **Laya** page (nav), which lists the model's four tasks with live counts, what it can't do, how it learns, and how it was tested |

## Decisions

1. **Pre-fill, never record.** Clinical criteria are the dentist's attestation under their licence
   (`AssertionPayload`: "Ophi never asserts these itself"). A pre-fill is a selected radio until the dentist
   confirms. Auto-recording would make Ophi the author of a clinical statement.
2. **Suggest only Met or N/A.** A contradiction (4 surfaces where 5 are required, pending fillings in the plan,
   a pocket of 5 mm or more, a note that says the root canal is recent) goes to Your call with the reason in amber.
   Ophi never pre-fills Not met: that's a clinical conclusion with consequences for the patient.
3. **Chart rules first, Laya second.** Deterministic checks read the odontogram against the pack's definition for the
   tooth type, the plan for other pending work, the perio chart at the tooth (2017 World Workshop: stable when no
   pocket is over 4 mm and no 4 mm site bleeds), the RCT date against the latest PA, and the odontogram for third
   molars. Laya's 7 calibrated note answers add support at 0.7 and contradict above 0.5 (the fixer's own flag).
4. **Films are named, not read.** Crown-to-root ratio, margin, ferrule, adjunctive work, mesio-distal space and
   endo healing are judged on the radiograph. Ophi can't see images, so those rows sit under "Look at the PA
   of #N" and are pre-filled from the note only. Mesio-distal space has no chart or note signal and is always the
   dentist's call.
5. **Laya's note answers outlive a new film.** The fix plan is keyed to the whole request text, so a new PA voids it.
   The note answers are also keyed to the note alone (`ScoredPlan.note_sha256`), so after Teresa's chair captures her
   criteria are still pre-filled. Laya read the whole request when scoring; reusing its answers for an unchanged note
   is an approximation, acceptable because the dentist checks the film-judged rows on the new film anyway.
6. **Every confirmation is a label.** The store keeps what Ophi pre-filled next to the dentist's answer, and the
   audit log says "as Laya pre-filled" or "Laya pre-filled met". The Laya page shows how many pre-fills the dentist
   kept. That agreement is the label real data would train on (`../outcomes-explainer.md` §6.2).
7. **A suggestion looks like one.** A pre-filled answer has a dashed outline and "Suggested by Laya" until the dentist
   touches or confirms it. The confirm bar sticks to the bottom of the screen and counts what it will record and what's
   still open. (From a fresh-eyes critique of the first build.)
8. **One ink spark, no new colour.** Colour still means status. The spark is the widely used AI mark, and the chip
   links to the page that explains it, so nothing needs a legend.

## Verified

- `make test` (552) and `make eval` pass. New: `tests/test_preread.py`; pre-fills confirmed in one submit, with the
  audit wording, in `tests/test_web.py`.
- `scripts/app-flow.py` checks Teresa's criteria are pre-filled after the chair captures, then confirms Tremblay's.
- `scripts/app-qa.py` and `scripts/app-overflow.py`, now including `/model`: no sideways scroll at 390 px, visible
  focus, every token pair at 4.5:1 or better.
- `scripts/preread-check.py` prints every demo case's pre-reads: 7 to 9 of 9 or 10 pre-filled per case.
