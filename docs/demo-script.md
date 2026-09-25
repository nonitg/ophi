# Demo script — six minutes with a dentist

Start: `make demo` (real cases from `cases/demo/`) or `USE_MOCK_PMS_API=true make demo`
(mock fixtures from `mocks/` — see `docs/pms-basics.md` — Toggling real vs mock). Open
http://127.0.0.1:8765 and pick *Kim Osei, coordinator* in the person menu at the top right.
Reset state first if it has been used: Settings → Reset demo state.

> Scripts: `scripts/demo-real.sh` (real) and `scripts/demo-mock.sh` (dummy) wrap the same
> commands. `make demo-real` / `make demo-mock` are aliases.

## Beat 1 — Look-back (90 s)

Open **Look-back**. Four numbers, read them left to right:

> 34 preauthorizations submitted · 20 denied · 14 of 20 were missing a document CDCP explicitly
> requires · 10 of 20 were never resubmitted — treatment that never happened.

Say: *"We do not read Sun Life's denial text. Half of these say 'as per the plan criteria'. We
re-open the chart as it stood on the day you sent it and find the gap ourselves."* Point at the month
chart: one square per request, solid red where a required document was missing, a ring where the
request was never resubmitted. Then point at a table row whose gap column says *periapical within 12
months*.

## Beat 2 — the queue (60 s)

Open **Queue**. One sentence at the top: how many cases need something before they can go out, and
the dollars of treatment behind them. Under it, five stages with counts and dollars (Blocked, Needs
input, Ready to sign, Signed, Submitted), then a **Waiting on you** line that changes with the person
acting. Six crown cases, sorted by what blocks them and how soon the appointment is. Each row shows
the one thing to do next, who it waits on, the appointment countdown, and the rule check as a strip of
cells grouped Chart, Limits and Clinical. Say: *"This page is empty and boring when nothing needs
attention. That is the point: no dashboard habit, just what is at risk this week."*

## Beat 3 — the moment (60 s)

Click **Amrit Singh**. The screen opens with the verdict in one sentence — *Not ready to submit.
1 chart gap and 9 clinical criteria for Dr. Priya Lau to confirm* — and the strip: nine green, one
red, three amber. Under **Next steps**, the first item waiting on Kim Osei is the hero:

> **Take a periapical of #16 at the Sep 24 appointment.** A bitewing dated 2026-08-02 is on file for
> #16. Bitewings do not image the periapical region. CDCP crown criteria require assessment of
> crown-to-root ratio and restoration margin relative to the alveolar crest — both require a periapical.

Then hover the **Required by** chip under it: it cites the documentation matrix row and the Guide's
radiograph-standards section. *"Nothing on this screen says 'missing' without naming the rule that
makes it missing."* The **Documented** fold lists everything already settled, with its evidence, date,
age and source (hover a name for its clause). On the right, **What Ophi did** counts the chart
entries, subsystems, requirements and clauses behind the verdict, and the **chart timeline** puts every
dated entry against the 12-month window: on Kowalchuk, the 2023 periapical sits far outside it in red.
The raw chart Ophi read is in the **Chart entries Ophi read** fold.

Below it, **Waiting on Dr. Priya Lau** reads *Confirm 9 clinical criteria*. *"Four crown criteria are
measurements you make on the film. They exist in no chart. Ophi never asserts them. You do, once, and
the packet renders it as your clinical judgment with your name and a timestamp."* The **Hands off to**
rows close the list: the dentist signs, the clinic submits, Ophi never transmits.

## Beat 4 — the model proposes, the engine judges, you ratify (45 s)

Open **Yves Tremblay**. The verdict reads *Needs a human before it can go out*, and the strip has
one hatched amber cell: *awaiting confirmation*. The hero under **Next steps** is the proposed chart
finding, with the quoted sentence — *"Plan: ceramic crown 24 to protect the remaining structure."* —
and **Confirm** / **Reject**. Click **Confirm**. The hatched cell turns green.
*"The proposer found it. It could not count until a human said yes."* (The same highlighted sentence
is visible in the note inside the **Chart entries Ophi read** fold.)

Click **Switch to Dr. Priya Lau** in the dentist's lane. The **Clinical criteria** form opens under
Next steps: **Select all**, **Met**, **Record selected**. The verdict becomes *Documentation complete —
ready for sign-off*.

## Beat 5 — the packet (90 s)

Click **Review and sign** in the hand-off row. A four-step rail runs across the top: *Assembled by
Ophi*, *Checked by the verifier*, *Signed by Dr. Priya Lau*, *Sent by the clinic*. Left: the PDF
preview — index, treatment form, labelled plates with dates, the 6-site perio table, the rationale with
every finding quoted verbatim from the chart and attributed, the assertions block. Right: the
attestation and the sign-off button, then **In the packet** with a spec check per file; the narrative
editor is in the **Clinical narrative** fold. The facts row reads *Independent verifier: passed N files,
X KB.* Say: *"A second program, sharing no code with the one that built this, reopened every file and
re-checked the CDAnet limits."*

Before sign-off the status reads *Draft, not for submission* and the download is refused. Click **Sign
off as Dr. Priya Lau**. The card becomes *Signed by Dr. Priya Lau* and the rail moves to *Sent by the
clinic*. Then **Download packet (.zip)**. Close with the line on screen:

> **Ophi never transmits. You do.**

## Beat 6 — if asked "how do I trust it?" (30 s)

Open **Settings**: rule pack version, content hash, source URLs, every requirement with its clause.
Then the audit log: every assertion and confirmation with actor and time. Then
`/api/cases/tremblay/assessment.json`: the full machine-readable verdict, including for each rule the
artifact it matched, its date, its age in days, and the day it goes stale.

## Cases and what each shows

| Case | What it demonstrates |
|---|---|
| Singh #16 | Bitewings on file that image #16, no periapical at all: the "bitewings do not image the apex" sentence |
| Kowalchuk #46 | PA from 2023 (stale by 673 days) and a 4-point perio chart |
| Deng #37 | PSR path: PSR 3 in the requested tooth's sextant demands that sextant's charting; retired lab code 99333; pending filling on #47 blocks "basic treatment complete" |
| Tremblay #24 | Plan details live in a note → proposer → confirm; endodontically treated tooth adds the "healed" assertion |
| Rosco #11 | No perio chart (a confirmed gap) plus a source that cannot see imaging: radiographs read *cannot verify*, not *missing*, and the action is "Check the imaging software" rather than "take a radiograph"; no CDCP client ID on file blocks the claim form |
| Whitfield #36 | Fully documented and asserted: READY, 13 of 13 |

## Do not say

Approved, will be approved, eligible, covered, likely. Say *complete against the cited rule*.
Do not lead with time saved; the strip on Case Review shows the manual baseline as a sourced
estimate. Lead with the 10 never-resubmitted cases.
