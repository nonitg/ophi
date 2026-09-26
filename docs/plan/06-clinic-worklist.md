# From showpiece to clinic worklist

Status: built on branch `app-mvp-overhaul`, 2026-09-26. Scope: `ophi/web`, `ophi/service.py`, new
`ophi/workflow.py` and `ophi/demo.py`, five new demo cases. The engine, rule pack and packet are unchanged.

## Why

The five-screen app was built to read in a 15-second screenshot (`docs/reviews/2026-09-21-ui-glance-redesign.md`).
An MOA doesn't work that way. They work through a pile, every morning, to a deadline set by the appointment book.
The old app stopped at "Mark as submitted", so everything after it was left to a spreadsheet: waiting on Sun Life,
the decision, the resubmission, the call to book. It also sorted by verdict, not by who acts next or by when.

## What changed

| Before | Now |
|---|---|
| Queue sorted by verdict, one headline sentence, 13-square bar | **Worklist** grouped by step (fix chart gaps → dentist review → send → waiting on Sun Life → book / resubmit), each row with one next step, a send-by date and a shared four-week runway to the appointment |
| Case Review: verdict hero + folds | **Case**: seven numbered steps from chart check to booked, each tagged with who does it; the current step opens with its form |
| "Acting as" switch to find dentist work | The dentist's worklist is their own pile, plus cases where the criteria can be confirmed while chart work continues; after signing, the packet page offers the next case |
| Ends at "Mark as submitted" | Sent date, Sun Life's decision (verbatim reason), resubmission with the earlier attempt kept, reconsideration deadline, decision validity, booking |
| Look-Back table | **Recover** call list of denials never resubmitted, with follow-up status; **Results** report for the owner |

## Decisions

1. **The stage is derived, never stored** (`ophi/workflow.stage_of`). It comes from the assessment plus the
   recorded steps, so it can't drift from the chart. A chart change after signing voids the signature and the
   case falls back to the right step on its own.
2. **Send-by = appointment − 7 days.** Health Canada reports over 95% of requests processed within 7 days
   (Oral Health Group, 2026-06-18). It is planning guidance, labelled as such, never a Sun Life service level.
3. **Dates cited from the CDCP Dental Benefits Guide:** decisions are valid up to 12 months while the patient
   stays enrolled; reconsideration is within 60 days, needs new clinical information, and is one level only.
   The 21-day documentation deadline in `docs/research/cdcp-rules.md` belongs to post-payment claims
   verification, not preauthorization, so the app doesn't use it. "Back of the queue" has no source; the app
   says "a resubmission is a new request".
4. **Copy law.** Ophi's voice still never says approved, eligible or covered. Sun Life's recorded decisions
   render inside `data-voice="payer"` elements, in the slate status colour. The copy-law test parses the HTML
   and exempts only those elements. Results reports decisions as counts and dollars, never as a rate and never
   next to the published 37%.
5. **First check.** `CaseState.first_check` records the gaps found the first time Ophi read the chart, so a gap
   staff close still counts as caught before sending on the Results page.
6. **Demo clock.** The service has an injectable clock. By default "today" is the latest chart read date, so the
   frozen fixtures and a live PMS both work. `ophi/demo.py` replays five cases past sign-off through the real
   service calls, stamped on the day each step happened.

## Visual language

The committed Moxo direction (`04-app-restyle-moxo.md`): white paper, stone panels, charcoal buttons, Geist,
self-hosted. Where this build departs from it:

- Sentence-case labels instead of small caps.
- Tabular figures instead of mono for dates and fees.
- No middle-dot pill suffixes.

Colour still means status only:

| Colour | Means |
|---|---|
| Red | A chart gap or lateness |
| Amber | A person is needed |
| Green | Done |
| Slate | Sun Life |

Linen marks the step you're on. The one bold element is the runway.

## Open follow-ups

- The engine phrases new imaging as "Take a periapical of #16 at the Sep 24 appointment" (`ophi/engine/assess.py:131`).
  When that appointment is the crown itself, the request can't be back in time. Consider "before <send-by>";
  this changes golden expectations.
- `docs/demo-script.md` walks the old five screens and needs rewriting around the worklist.
- Not built:
  - patient phone numbers and scripts on the Recover list (they need a PMS read)
  - notifying the dentist outside the app
  - named owners beyond the two demo actors
  - partial approvals
