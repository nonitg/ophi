# Chair first: route each gap to who can close it

Status: built on branch `chair-first`, 2026-09-26. Builds on `07-kanban-board.md`, whose decisions (derived stage, one
deadline chip, colour on chips only, cards never drag) all still hold.

## Why

The first column, "Fix chart · You fix the chart", held every chart gap as desk work for the coordinator. But a
missing periapical or 6-site perio chart needs the patient in the chair and a clinician. The desk can only book the
visit. The cheapest moment to close those gaps is the diagnosis visit itself, before the patient leaves. That
moment is Ophi's clearest value, and the board didn't show it. The PA gap also read "at the Sep 20 appointment",
naming the crown appointment itself, which was already past its send-by date.

## What changed

| Before | Now |
|---|---|
| **Fix chart**: every gap | **Needs the patient** (film, perio chart, basic treatment; the desk books one visit for all of them) and **Paperwork** (lab code, CDCP ID, a note to confirm, the imaging check) |
| Booked: its own column, usually empty | Booked cards close out **Decision back**, newest first, with a green `Booked` chip |
| Start here: the most urgent card | When a patient is still in the operatory, the hero becomes **Before Teresa leaves**: operatory, clinician, and a checklist with the role that does each item. Otherwise, Start here as before |
| "Take a periapical of #46 at the Sep 20 appointment" | "Take a periapical of #46". The card reads "Book a visit: PA X-ray of #16" with a `Visit needed by` / `Visit needed today` chip |
| Ophi was invisible on the board | "Ophi checked 11 charts against the CDCP rules just now" beside the headline; "Ophi checks each one as it reaches the chart" under the checklist; "Ophi found 3 gaps: 2 need the patient, 1 at the desk" on the case |
| Case: one list of chart gaps | Two groups, *Needs the patient* and *At the desk*, with the chair group first |
| Results: one list of caught gaps | Split into *Needed the patient* and *At the desk*; "N taken while the patient was still in the chair"; past denials missing an X-ray or perio chart |

## Decisions

1. **The pack says which gaps need the patient.** `Gap.needs_patient` is set on radiograph_pa, radiograph_bw,
   perio_chart and basic_treatment_complete, and the engine copies it to the capture action. Desk checks on those same
   requirements (check the imaging software, establish a date) stay at the desk: the film may already exist.
2. **Chair gaps lead.** `stage_of` returns `PATIENT` before `PREPARE`. The visit takes longest to arrange, and desk
   fixes can happen meanwhile, shown on the card as `+N desk fixes`.
3. **In the chair is not chart evidence.** `Case.in_chair` is excluded from the case dump, so the patient leaving never
   changes the assessment or voids a signature. Today it comes from the case file. With ABELDent it comes from today's
   appointment status (arrived or seated) and its chair.
4. **Now beats every date.** An in-chair case sorts first for both viewers, shows `In the chair now`, and makes the
   dentist's team the owner of the chart step.
5. **Who does what, per Ontario scope of practice.** Only a dentist orders X-rays; an assistant or hygienist takes
   them (RCDSO, CDHO). Only a hygienist or the dentist probes. Hence the role tags: Assistant, Hygienist, Dentist.
6. **Taken is a demo stand-in, and says so.** "Mark taken (demo)" records a fictional PA or 6-site chart dated today. The
   engine judges it like any film, and the packet plate is the existing labelled placeholder. A note on the case offers
   "Take back the last one". In production the item ticks itself when the film reaches the chart.
7. **No chair-time estimates.** There's no public source for minutes per film or chart, so none are shown.
8. **Ophi never owns a column.** It reads, checks and routes; people act. "Ophi is never the one you wait on."

## Verified

- `make test` and `make eval` pass (50 golden cases).
- `scripts/app-flow.py` walks the in-chair capture, then every step as both actors.
- `scripts/app-qa.py` and `scripts/app-overflow.py` report no sideways scroll at 390, 1280 and 1440 px, visible
  focus, and every token pair at 4.5:1 or better.
- A fresh-eyes reviewer given only the board screenshot named what Ophi does and why Teresa is urgent, and that people
  sign and send.
