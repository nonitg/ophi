# 08 — Sun Life's decision back into Ophi

Goal: fill the "Decision back" column from Sun Life's answer, show the reason, and send a denied case to the
column that can fix it. Two ways the answer arrives, one flow after it.

## Verdict: viable, and worth it

Every resubmission goes to the back of Sun Life's queue, so a denial fixed on the first try is the product's
economic core (`cdcp-rules.md`). The risk is that staff never tell Ophi what the letter said. We handle that
three ways: electronic answers need no staff input, a letter takes one upload, and a "With Sun Life" card goes
overdue after the usual 7 days.

## What ABELDent gives us (verified on the lab VM, 2026-09-26)

| Fact | Where |
|---|---|
| Sent, when, and Sun Life's reference number | `Claim` (`IsPredetermination=1`, `BillingDate`, `CarrierClaimNumber`) |
| Which crown | `ClaimItem.ServiceTransaction` → `Transactions.TransID` |
| Where the answer is | `Claim.Status`. `P` "Pred. Explanation of Benefits received"; `S`/`C`/`N` waiting; `Q`/`H`/`B` "expect paper response"; `R`/`M`/`*` network rejected |
| Decision and reason, when the answer came electronically | `NetLog.ReceivedMessage`: G15 benefit per line, G28 total, G16/G45 note numbers, G26 note text, G07 disposition |

The Fictional Data install had never sent a claim, so the lab now holds three **fake** Sun Life answers
(`lab/fixtures/fake-sunlife-responses.sql`; undo script alongside; backup
`C:\AbelBackups\Abel_20260926_191225_before_fake_sunlife.bak`). ABELDent's own Claim History screen shows them
with the status labels above (`lab/out/pred-status/fake-*.png`).

| pid | Crown | Status | Answer |
|---|---|---|---|
| 158 Yokoyama | 27211 #24 | P | Denied: current periapical radiograph not received |
| 162 Randal | 27211 #26 | P | Approved, $290.50 |
| 160 Cherski | 27211 #26 | Q | Held for review; answer comes by mail (letter-upload demo) |

**Not verified:** the real CDAnet message layout isn't public, so the fake bodies are `field=value` pairs keyed
by ABELDent's `CDADataDictionary` ids. The parser is one function, to be swapped once we get a real response.
ABELDent shows the claim line's code as "Unknown", so the fake `ClaimItem` link is not what ABELDent expects.
It is cosmetic, because Ophi joins through `Transactions`.

## The letters

No real CDCP decision letters are public; only reason code N05 is documented. For the hackathon:

1. **Synthetic letters we write**, one per demo case and marked "SAMPLE — synthetic" (text and layout only, no
   Sun Life logo or branding). Their wording reuses the fake EOB note text, so both paths yield the same
   reason. Four letters: named reason (radiograph), named reason (clinical, ferrule), vague ("as per the plan
   criteria"), approved.
2. **After the hackathon:** ask a pilot clinic for one redacted real letter, then match the synthetic wording to it.

## Reading a letter

1. **Upload** a PDF or phone photo on a "With Sun Life" or "Decision back" case.
2. **Extract** the text: the file goes to the model as-is, a PDF as a document and a photo as an image.
3. **Structure it** with Gemini: outcome, decision date, the reason quoted word for word (it must appear in
   the text), the documents asked for, and one reason key from `laya_questions.REASON_KEYS` or `unspecified`.
4. **Laya handles vague letters only.** Laya is trained to predict the reason from the chart, not to read
   letters; untrained questions lean "no". When the letter is `unspecified`, Laya's decision head scores the chart
   and Ophi shows its top reason as "likely" (33% top-1 on the synthetic set), for staff to confirm.
5. **Staff confirm** with one click; that records the decision (`record_decision`, reason verbatim).

Electronic answers (`Status P`) skip steps 1–3: the reason is G26, and the outcome is G15 > 0.

Privacy: letters carry patient information. Gemini sees only synthetic letters for the demo. In production,
extraction runs locally (OCR + Laya fine-tuned on letter text) or on a Canadian-hosted model.

## Reason → column

On "Start resubmission", the confirmed reason reopens its requirement, and `workflow.stage_of` places the card.

| Reason key | Requirement reopened | Column |
|---|---|---|
| `missing_radiograph`, `stale_radiograph` | `radiograph_pa` / `radiograph_bw` | Needs the patient |
| `missing_perio_chart` | `perio_chart` | Needs the patient |
| `insufficient_notes`, `invalid_lab_code` | `tx_plan_details` / `lab_codes_current` | Paperwork |
| `basic_treatment_pending`, `endo_not_healed`, `perio_prognosis` | `basic_treatment_complete` / `endo_healed` / `restorability` | Needs the patient |
| `not_extensively_restored`, `insufficient_ferrule`, `need_not_met`, `indication_not_covered` | `extensively_restored` / `restorability` | Dentist review |
| `frequency_limit`, `client_ineligible`, `tooth_ineligible`, `duplicate_request` | none | Stays in Decision back: tell the patient; reconsideration only |

## Built (2026-09-26)

Demo files: `scripts/demo-real.sh`. Live ABELDent: `scripts/demo-abeldent.sh` (`USE_ABELDENT_PMS=true`; the VM must be up;
`GEMINI_API_KEY` in `.env` for letter reading). In ABELDent mode every patient with a planned crown is a case, judged as of
today, so its 2002–2007 evidence reads as stale.

| Piece | Where |
|---|---|
| Predetermination reader, `GET /api/abeldent/patients/{pid}/predeterminations` | `ophi/sources/abeldent.py`, `ophi/web/abeldent_api.py` |
| Cases from the VM: chart_dump charts → `chart_to_case` (shared with the mock repository), cached 5 min | `AbelDentPmsRepository` |
| Sync: ABELDent's claim marks the case sent (signed in Ophi or not; the audit says which); an electronic answer records the decision (by "ABELDent", once per claim, so undo sticks) | `CaseService.sync_from_pms`, every 30 s in ABELDent mode |
| Letter upload → Gemini (`gemini-2.5-pro`, PDF or photo) → decision form pre-filled for staff to check | `ophi/letters.py`, `POST /cases/{id}/letter` |
| Reason → column: picked at "Start resubmission" (pre-set from the letter or note), opens an ask; "Done" closes it | `workflow.REASONS`, `with_ask`, `CaseService.start_resubmission`/`resolve_ask` |
| Sample letters (SAMPLE-marked, no branding): Cherski (pid 160) ferrule, vague, approved, perio photo; Goertsen (pid 164) radiograph, notes, approved, acknowledgement (reads as unclear) | `fixtures/letters/`, `scripts/gen-sample-letters.py` |
| Checks every sample letter still reads as it should (needs `GEMINI_API_KEY`) | `scripts/check-sample-letters.py` |

Not built: network rejections (`R`/`M`/`*`) back to Ready to send; storing the uploaded letter file; Laya's likely
reason for vague letters (the case page's fix plan already ranks what is most likely wrong).

## Open

- A real CDAnet predetermination EOB (CDA/ITRANS certification environment or a pilot clinic) to replace the
  fake message format.
- Whether CDCP answers predeterminations electronically at all, or always by mail: this decides which path
  matters most.
