# Demo script — six minutes with a dentist

Start: `make demo` (real cases from `cases/demo/`) or `USE_MOCK_PMS_API=true make demo`
(mock fixtures from `mocks/` — see `docs/pms-basics.md` — Toggling real vs mock). Open
http://127.0.0.1:8765, set **Acting as** to *Kim Osei (coordinator)*.
Reset state first if it has been used: Settings → Reset demo state.

> Scripts: `scripts/demo-real.sh` (real) and `scripts/demo-mock.sh` (dummy) wrap the same
> commands. `make demo-real` / `make demo-mock` are aliases.

## Beat 1 — Look-Back (90 s)

Open **Look-Back**. Four numbers, read them top to bottom:

> 34 preauthorizations submitted · 20 denied · 14 of 20 were missing a document CDCP explicitly
> requires · 10 of 20 were never resubmitted — treatment that never happened.

Say: *"We do not read Sun Life's denial text. Half of these say 'as per the plan criteria'. We
re-open the chart as it stood on the day you sent it and find the gap ourselves."* Point at a row
whose denial text is blank and whose gap column says *periapical within 12 months*.

## Beat 2 — the queue (60 s)

Open **Queue**. One sentence at the top: how many cases need something before they can go out, and
the dollars of treatment behind them. Six crown cases, sorted by what blocks them and how soon the
appointment is. Each row shows the one thing to do next, how many more stand behind it, and a
13-segment bar of the rule check. Say: *"This page is empty and boring when nothing needs attention.
That is the point: no dashboard habit, just what is at risk this week."*

## Beat 3 — the moment (60 s)

Click **Amrit Singh #16**. The screen opens with the verdict in one sentence — *Not ready to submit.
1 chart gap and 9 clinical criteria for Dr. Priya Lau to confirm* — and the 13-segment bar: nine
green, one red, three amber. Under **Before this can go out**, item 1 is the hero:

> **Take a periapical of #16 at the Sep 24 appointment.** A bitewing dated 2026-08-02 is on file for
> #16. Bitewings do not image the periapical region. CDCP crown criteria require assessment of
> crown-to-root ratio and restoration margin relative to the alveolar crest — both require a periapical.

Then hover the **Required by** chip under it: it cites the documentation matrix row and the Guide's
radiograph-standards section. *"Nothing on this screen says 'missing' without naming the rule that
makes it missing."* The full list of 13 requirements, each with its clause, is one click away in the
**All 13 CDCP requirements** fold; the chart Ophi read is in the fold below it.

Item 2 is *Dr. Priya Lau confirms 9 clinical criteria*. *"Four crown criteria are measurements you
make on the film. They exist in no chart. Ophi never asserts them. You do, once, and the packet
renders it as your clinical judgment with your name and a timestamp."* The **Clinician assertions**
fold at the bottom holds the form; it is open whenever you are acting as the dentist.

## Beat 4 — the model proposes, the engine judges, you ratify (45 s)

Open **Yves Tremblay #24**. The verdict reads *Needs a human before it can go out*, and the bar has
one dashed amber segment: *awaiting confirmation*. Item 1 under **Before this can go out** is the
proposed chart finding, with the quoted sentence — *"Plan: ceramic crown 24 to protect the remaining
structure."* — and **Confirm** / **Reject**. Click **Confirm**. The dashed segment turns green.
*"The proposer found it. It could not count until a human said yes."* (The same highlighted sentence
is visible in the note inside the **What Ophi read in the chart** fold.)

Switch **Acting as** to *Dr. Priya Lau*. The assertions fold is open: **Select all**, **Met**,
**Record selected**. The verdict becomes *Documentation complete — ready for sign-off*.

## Beat 5 — the packet (90 s)

Click **Packet preview & sign-off**. Left: the PDF preview — index, treatment form, labelled plates
with dates, the 6-site perio table, the rationale with every finding quoted verbatim from the chart
and attributed, the assertions block. Right: the editable rationale and the attestation sentence.
In the header line: *Independent verifier passed N files, X KB.* Say: *"A second program, sharing no
code with the one that built this, reopened every file and re-checked the CDAnet limits."*

Before sign-off the verdict sentence reads *This is a draft — not signed, not for submission* and the
download is refused. Click **Sign off**. The sentence becomes *Signed by Dr. Priya Lau* and the
verifier reports a signed packet. Then **Download packet**. Close with the line on screen:

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
