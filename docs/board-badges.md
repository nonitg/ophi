# Board badges: where each one's data comes from

How every chip, tag and mark on the board and case screens is produced, and which parts are read
from ABELDent versus computed by Ophi. Written after a review of `ophi/web/present.py`,
`ophi/web/templates/macros.html` and `ophi/sources/`.

## The short version

ABELDent supplies **three dates** and the chart. Every "due", "late" or "needed by" wording is
Ophi's arithmetic on top of them. No due date exists anywhere in ABELDent, and Sun Life sends none.

| Fact | Source |
| --- | --- |
| Crown appointment date | ABELDent `apt` table |
| Predetermination sent date | ABELDent claims (`BillingDate`) |
| Decision date and outcome | ABELDent claims, or recorded in Ophi by staff |
| Everything else below | Ophi constants and rules |

## Badge inventory

| Badge | Rendered by | Built by | Data behind it |
| --- | --- | --- | --- |
| Due chip ("Send by Oct 21", "Visit needed in 2 days", "Late for Oct 28 crown") | `macros.html` `due()` | `present.timing()` (`present.py:409`) | Appointment date from ABELDent, minus Ophi's 7-day turnaround constant |
| Risk chip ("Risk High → Low") | `board.html:78` | `present.board_risk()` (`present.py:363`) | Laya's readout for this case, scored against the rule pack. Model output, not a payer statement |
| Pre-filled count ("3 of 5 criteria") | `board.html:75` | `present.prefilled()` (`present.py:1022`) | Criteria the engine answered from the chart that still wait on the dentist |
| "Waiting on …" | `board.html:67` | `present.card()` (`present.py:555`) | `OWNER[stage]` — whose column the case sits in, compared with the signed-in actor |
| Test tag | `board.html:64` | `Assessment.test_run` (`engine/models.py:188`) | True when any requirement was skipped to try the flow |
| Sun Life note | `board.html:71` | `present._payer()` | The decision text, quoted verbatim. Marked `data-voice="payer"` so the copy-law test skips it |
| "Before X leaves" banner | `board.html:10` | `present.in_chair()` (`present.py:241`) | `case.in_chair` — **demo data only**, see gaps below |
| Status marks (tick, cross, question, dot) | `macros.html` `status_mark()` | Engine `Status` per requirement | Rule evaluation against the chart |
| Clause chips (source + reference) | `macros.html` `clause_chip()` | Rule pack | The CDCP pack's own citations and quotes |
| Column header count and job | `board.html:52-57` | `present.board()` (`present.py:666`) | Stage assignment from `workflow.stage_of()` |

## How a deadline is computed

1. Find the appointment. `present.py:413` takes `state.booked_on` if staff booked through Ophi,
   otherwise `case.treatment.appointment_date`.
2. In live ABELDent mode, that appointment is the patient's next future row in `apt` whose free-text
   `apwork` matches `%crn%` or `%crown%` (`sources/pms_repository.py:192`, read at `:262`).
   In demo and casegen runs it comes from the scenario's `appointment` field (`casegen/dsl.py:69`).
3. Subtract the turnaround: `send_by(appt) = appt - 7 days` (`workflow.py:137`).
4. `left = (send_by - today).days` decides the wording (`present.py:427-433`):
   - `left > 2` — absolute, "Send by Oct 21", no colour.
   - `left <= 2` — relative, "Send in 2 days", amber.
   - `left < 0` — "Late for Oct 28 crown", red.
5. The verb changes with the column, the date does not. `Needs the patient` reads "Visit needed",
   `Dentist review` reads "Sign", every other pre-send column reads "Send".

One deadline exists per case. It is relabelled per column, not recalculated.

Other columns use their own clock:

- **With Sun Life** counts days since the sent date, and turns amber past 7 (`present.py:436`).
- **Book the crown** counts down to `decided_on + 12 months`, and only shows a chip inside the last
  30 days (`present.py:441`, `BOOK_SOON_DAYS`).
- **Test runs** get no deadline at all, so fake work never competes with real work (`present.py:415`).

## Constants and their provenance

All in `ophi/workflow.py`, each with its citation in a comment beside it.

| Constant | Value | Cited to |
| --- | --- | --- |
| `SUN_LIFE_TURNAROUND_DAYS` | 7 | Health Canada via Oral Health Group, June 2026. A population statistic ("95% processed within seven days"), not a service level for any one case. `TURNAROUND_SOURCE` links it, and `macros.turnaround_source()` puts that link one tap from every place the figure is used |
| `DECISION_VALID_MONTHS` | 12 | CDCP Dental Benefits Guide, "Preauthorization validity" |
| `RECONSIDERATION_DAYS` | 60 | CDCP Dental Benefits Guide, Appendix C |
| `BOOK_SOON_DAYS` | 30 | `present.py:113`. A display threshold, no external source |
| Amber at 2 days | 2 | `present.py:431`. A display threshold, no external source |

## Known gaps

1. **Appointment matching is free text.** `apwork LIKE '%crn%'` misses "crwn", a blank work field, or
   any other spelling. The case then shows "No appointment" and carries no deadline.
2. **Appointment matching ignores the tooth.** Any crown appointment for the patient anchors the
   deadline, including one for a different tooth.
3. **"In the chair" is demo-only.** `case.in_chair` is set in `casegen/dsl.py` and nowhere else; the
   ABELDent repository never populates it, so the chair banner cannot fire on live data.
4. **The 7 days is a national average.** It is presented as planning guidance, but a case near the
   boundary is amber or red on a figure that describes other people's claims, not this one.
