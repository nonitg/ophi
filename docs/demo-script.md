# Demo script — six minutes with a dentist

Start: `make demo`, open http://127.0.0.1:8765, set **Acting as** to *Kim Osei (coordinator)*.
Reset state first if it has been used: Settings → Reset demo state.

## Beat 1 — Look-Back (90 s)

Open **Look-Back**. Four numbers, read them top to bottom:

> 34 preauthorizations submitted · 20 denied · 14 of 20 were missing a document CDCP explicitly
> requires · 10 of 20 were never resubmitted — treatment that never happened.

Say: *"We do not read Sun Life's denial text. Half of these say 'as per the plan criteria'. We
re-open the chart as it stood on the day you sent it and find the gap ourselves."* Point at a row
whose denial text is blank and whose gap column says *periapical within 12 months*.

## Beat 2 — the queue (60 s)

Open **Queue**. Six crown cases, sorted by what blocks them and how soon the appointment is. Each
row already shows the top two things to do. Say: *"This page is empty and boring when nothing needs
attention. That is the point: no dashboard habit, just what is at risk this week."*

## Beat 3 — the moment (60 s)

Click **Amrit Singh #16**. The first blocking action reads:

> A bitewing dated 2026-08-02 is on file for #16. Bitewings do not image the periapical region.
> CDCP crown criteria require assessment of crown-to-root ratio and restoration margin relative to
> the alveolar crest — both require a periapical. Take a periapical of #16 at the Sep 24 appointment.

Then hover the clause chip on *Dated periapical radiograph*: it cites the documentation matrix row
and the Guide's radiograph-standards section. *"Nothing on this screen says 'missing' without naming
the rule that makes it missing."*

Scroll to **Clinician Assertions**. *"Four crown criteria are measurements you make on the film.
They exist in no chart. Colombus never asserts them. You do, once, and the packet renders it as your
clinical judgment with your name and a timestamp."*

## Beat 4 — the model proposes, the engine judges, you ratify (45 s)

Open **Yves Tremblay #24**. The treatment-plan requirement is amber: *satisfied pending
confirmation*. In the evidence panel the note has a highlighted sentence — *"Plan: ceramic crown 24
to protect the remaining structure."* — proposed as treatment-plan details. Click **Confirm**. The
requirement turns green. *"The proposer found it. It could not count until a human said yes."*

Switch **Acting as** to *Dr. Priya Lau*. Answer the ten assertions Met. The verdict becomes
*Complete — ready for sign-off*.

## Beat 5 — the packet (90 s)

Click **Packet preview & sign-off**. Left: the PDF preview — index, treatment form, labelled plates
with dates, the 6-site perio table, the rationale with every finding quoted verbatim from the chart
and attributed, the assertions block. Right: the editable rationale and the attestation sentence.
Below the preview: *Independent verifier: PASS — N files, X KB.* Say: *"A second program, sharing no
code with the one that built this, reopened every file and re-checked the CDAnet limits."*

Click **Sign off**. Then **Download packet**. Close with the line on screen:

> **Colombus never transmits. You do.**

## Beat 6 — if asked "how do I trust it?" (30 s)

Open **Settings**: rule pack version, content hash, source URLs, every requirement with its clause.
Then the audit log: every assertion and confirmation with actor and time. Then
`/api/cases/tremblay/assessment.json`: the full machine-readable verdict, including for each rule the
artifact it matched, its date, its age in days, and the day it goes stale.

## Cases and what each shows

| Case | What it demonstrates |
|---|---|
| Singh #16 | Bitewing on file, no PA: the "bitewings do not image the apex" sentence |
| Kowalchuk #46 | PA from 2023 (stale by 673 days) and a 4-point perio chart |
| Deng #37 | PSR path: PSR 3 in the requested tooth's sextant demands that sextant's charting; retired lab code 99333; pending filling on #47 blocks "basic treatment complete" |
| Tremblay #24 | Plan details live in a note → proposer → confirm; endodontically treated tooth adds the "healed" assertion |
| Rosco #11 | The source cannot see imaging: *indeterminate*, not *missing*. "Check the imaging software" instead of "take a radiograph" |
| Whitfield #36 | Fully documented and asserted: READY, 13 of 13 |

## Do not say

Approved, will be approved, eligible, covered, likely. Say *complete against the cited rule*.
Do not lead with time saved; the strip on Case Review shows the manual baseline as a sourced
estimate. Lead with the 10 never-resubmitted cases.
