# Demo script: about three minutes, driven live

Start: `make demo`, open http://127.0.0.1:8765, click **Start over** in the demo banner, and view as **Kim Osei**
(front desk). The demo clock is fixed at Thursday Sep 17, 2026. Every patient is fictional.

The story in one line: *a crown request is cheapest to complete while the patient is still in the chair, and Ophi
tells the right person, at that moment, exactly what's missing and which CDCP rule asks for it.*

## Beat 1: the board (0:00–0:20)

Point at the columns left to right, then the stamp top right ("Ophi checked 11 charts against the CDCP rules just
now").

> "Every CDCP crown needs Sun Life's sign-off before treatment. Health Canada names missing X-rays, perio charts and
> treatment plans as the most common reasons requests are incomplete. Ophi reads each chart and puts every gap in
> front of the one person who can close it. Each column says who that is."

## Beat 2: in the chair (0:20–0:55)

The hero reads **Before Teresa leaves · In the chair now · Op 2 with M. Haddad RDH**.

> "Dr. Lau just planned a crown on #46 at Teresa's recall. She's still in Op 2. Her last periapical is from 2023 and
> her perio chart is 4-point. If she walks out, she comes back for another visit before this can even be sent."

Click **Mark taken (demo)** on the PA, then on the perio chart (listed in the fix plan's order). The toast reads *Nothing left to take. The patient can
go.* Teresa's card is now in **Dentist review**.

> "The hygienist and assistant did it on the spot. Nobody hunted through the chart, and the card moved by itself.
> In the clinic, 'Taken' happens when the film reaches the imaging software."

## Beat 3: the fallback, and the fix plan (0:55–1:35)

Open **Amrit Singh** in **Needs the patient**. Expand **Why** on *Take a periapical of #16*.

> "Amrit already went home. His bitewings don't show the root, and the rule is cited right here. Now it's a visit:
> Kim books it, and the chip, *Visit needed today*, says it has to happen today to hold his Sep 24 crown."

Then open **Mei Deng**. Point at **Denial risk: Now High → After these fixes Medium**, then click **Apply it**.

> "Ophi ranks her fixes by how much each lowers denial risk in past decisions. That's a guide from synthetic
> training data, not Sun Life's answer. The retired lab code it can fix itself; the perio chart and the pending
> filling need her back in the chair, and her Sep 23 crown has to move first."

## Beat 4: paperwork (1:35–1:50)

Open **Yves Tremblay** in **Paperwork**. Under *Does the note say this?*, click **Yes**.

> "Ophi found the treatment plan in the dentist's note. A person confirms it before it counts."

## Beat 5: the dentist (1:50–2:15)

Switch **View as** to **Dr. Priya Lau**. Open **Dana Whitfield**, then **Review and sign**, then **Sign**.

> "13 of 13 requirements documented, each tied to a CDCP clause and a chart entry. Her licence, her signature."

## Beat 6: send (2:15–2:30)

Switch back to **Kim Osei**. Open **Claire Fontaine** in **Ready to send** and click **Mark as sent**.

> "Kim sends it from her own practice software. Ophi never sends anything."

## Beat 7: after Sun Life (2:30–2:50)

On the board, point at **Chidi Okafor** (*Sent 8 days ago*, *Check your CDAnet mailbox*). Then **Decision back**:
open **Linh Nguyen** and click **Mark as booked**. Her card drops to the foot of the column as *Booked*.

> "Past Sun Life's usual 7 days, Kim checks the mailbox. Sun Life approved Linh's, so Kim books the crown. Sun Life
> denied Luc's, so it goes back for a resubmission."

## Beat 8: the owner (2:50–3:20)

Open **Results**.
- **In progress:** dollars in progress.
- **Caught before sending:** split into *Needed the patient* and *At the desk*, with *2 were taken while the patient
  was still in the chair*.
- **Last 12 months:** 20 denials; all 14 with a missing document lacked an X-ray or perio chart; 10 were never
  resubmitted, and the call list is one click away.

> "Ophi doesn't predict Sun Life, and it doesn't send. It makes sure what goes out is complete, and that the patient
> doesn't have to come back for it."

If anything goes wrong mid-demo, **Start over** in the banner resets every case.

## Cases and what each shows

| Case | What it demonstrates |
|---|---|
| Kowalchuk #46 | In the chair now, at today's recall: PA from 2023 and a 4-point perio chart, both taken before she leaves |
| Singh #16 | Patient left. Bitewings on file, no periapical: "bitewings do not image the apex". Visit today to hold the Sep 24 crown |
| Deng #37 | Chair and desk gaps together, and late for the Sep 23 crown. PSR path, a pending filling blocking "basic treatment complete", and a retired lab code Ophi replaces itself (**Apply it**). Denial risk High → Medium |
| Rosco #11 | No perio chart (needs a visit) plus four desk fixes, including "Check the imaging software", because the source can't see imaging |
| Tremblay #24 | Paperwork only: the plan is in a note, the proposer finds it, a person confirms it. The dentist can confirm criteria in parallel |
| Whitfield #36 | Fully documented: 13 of 13, ready for the dentist's signature |
| Fontaine, Okafor, Park, Nguyen, Marchand | Seeded past sign-off: ready to send, with Sun Life, approved (book), denied (resubmit) |

## Do not say

- Never say approved, will be approved, eligible, covered or likely in Ophi's voice. Say *complete against the cited
  rule*.
- Never put an approval rate next to a claim about Ophi.
- Don't cite "about 20% arrive incomplete" until it has a public source.
- Don't lead with time saved.
