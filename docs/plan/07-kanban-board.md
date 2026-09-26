# From worklist to board

Status: built on branch `kanban-board`, 2026-09-26. Scope: `ophi/web` only. The engine, workflow, service and
packet are unchanged. Supersedes the screens in `06-clinic-worklist.md`; its decisions (derived stage, send-by
date, cited dates, copy law, demo clock) all still hold.

## Why

The owner found the worklist had too much text, was confusing to navigate, and had too much going on. They
didn't understand the runway bars. They asked for a modern kanban board that surfaces actions and gives
recommendations you can take in at a glance, with a small learning curve. Rule for every element: it must
lead to an action or an outcome.

## What changed

| Before | Now |
|---|---|
| Stat strip, two warning paragraphs, a legend, six grouped tables with runway bars and fees | **Board**: six columns (Fix chart → Dentist review → Ready to send → With Sun Life → Decision back → Booked), each captioned with who does what ("You add what's missing in the PMS") |
| Runway bar + "4 days late to send" + an explanation line per row | One **deadline chip** per card: `Send by Sep 22`, `Send today` (amber), `Late for Sep 20 crown` (red), `Sent 8 days ago` (amber), `Book by …`, `Booked …` (green) |
| Warning paragraphs naming late cases | **Start here**: the viewer's single most urgent card, with one recommendation ("…sooner than Sun Life's usual 7 days. Move it, or tell the patient.") and its source |
| The dentist saw only their pile | Everyone sees the whole board. The viewer's cards are solid white; everyone else's are outlined. The headline and Start here count only the viewer's |
| "Acting as" select | "View as" two-button switch |
| Case: 7-step vertical timeline, a jump button, five aside cards | Stepper that mirrors the board columns; one **Now** panel holding the current step's form; "Then: …" names the next step and who does it; requirements, chart evidence, patient and activity are folded away |
| Gap explanation and clause always shown | Gap title and last-seen hint shown; the explanation and clause sit under "Why" |
| Packet: status box, narrative textarea, sign-off in a side column | The dentist signs at the top; the PDF preview follows; narrative editing, files and staleness are folded away |
| Results "in progress" bar chart | A count and dollar list per column, using the same names as the board |
| Green confirmation bar at the top of the page | A toast that fades after 4 seconds |

## Decisions

1. **Columns are stages, merged where the job is the same person deciding next.** Book and Resubmit share
   "Decision back": both start with reading Sun Life's reply, and the card's slate line says which it was.
2. **Priority.** A case late for its appointment beats Sun Life running past 7 days, which beats the nearest
   deadline (`present.card`). A late appointment affects a patient; a slow reply only needs a mailbox check.
3. **Cards never drag.** Stage stays derived (`ophi/workflow.stage_of`); a line under the Start here strip says
   cards move on their own.
4. **Colour means status, on chips only.** Red is late, amber is due within two days, green is done, and slate
   is Sun Life's words. Solid vs outlined cards show whose turn it is. No other coloured text on the board.
5. **No fees on cards.** The fee didn't change what anyone does next. It stays in case details and Results.
6. **The source travels with the number.** Wherever Ophi states Sun Life's usual 7 days, a "Source" link follows it.

## Verified

The full test suite passes (board, chip and dentist-view tests replace the worklist and runway ones).
`scripts/app-flow.py` walks every step as both actors. `scripts/app-qa.py` reports no overflow at 390px,
visible focus, and contrast of 4.5:1 or better. Two independent UX review passes checked the screenshots.
