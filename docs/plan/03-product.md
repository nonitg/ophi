# Product Shape, Delivery Sequence, GTM De-Risking

*Pre-reconciliation deep-dive. PLAN.md carries the v1 cut; the effort and scope numbers here are uncut.*

## 0. Five corrections to the brief, before anything else

**0.1 — Per-clinic volume is a 30x uncertainty and it is the whole business.** The brief says ~1.9M
preauths/yr. CDCP provider guidance says **only ~1% of all CDCP claims are for services requiring
preauthorization.** With 4.76M enrollees at realistic utilization (~6M claims/yr), 1% implies ~60,000
preauths/yr = 2.4 per dentist per year — a product nobody would pay $10/mo for. The 480,000-per-quarter
figure implies 75 per dentist per year (~1.4/week) — a real product. Both readings cannot be true.
(Partial reconciliation: the gap is almost certainly resubmission churn, ~8–10 preauth *transactions*
per underlying *case*. Unique cases per clinic stay uncertain, and unique cases are what the product is
priced against.) **Falsifiable in two days for $0:** ask 10 office managers *"how many CDCP
predeterminations did your office submit last month?"* Do it first. Nothing else in this plan matters
if the answer is "two."

**0.2 — Crowns are the beachhead. Partial dentures are not.** Partial dentures approve at >76%: that
workflow is *already working*, so there is no pain to sell against. Crowns at 37% and molar endo at 44%
are where the denial mass is, and crowns carry the heaviest documentation burden. **Scope v1 to crowns
(27xxx) + endodontics (32xxx/33xxx). Ship nothing for dentures.** Sharper than any competitor's "we
help with preauth": *"We do the two procedures that get denied."*
> **Reconciled in PLAN.md:** v1 is crowns (27xxx) only; endodontics (32xxx/33xxx) deferred to v1.1.
> The denture reasoning above is unchanged.

**0.3 — CDCP crown criteria require measurements that are not in any chart.** Verified criteria: no
active periodontal disease, crown-to-root ratio <= 1:1, no furcation involvement, restoration margin
>= 3 mm from the alveolar crest, ferrule >= 1.5 mm, dated PA **and** BW within 12 months, complete
6-point perio chart within 12 months. **Three of those — crown-to-root ratio, margin-to-crest and ferrule —
are radiographic measurements a human makes by looking at the film.** They are not fields in ABELDent, and
extracting them needs image analysis, which is correctly out of MVP. Furcation is charted in ABELDent
(`Perio.Furcation`), but whether a probed value satisfies CDCP's radiographic criterion is an SME question. The resolution: a **Clinician Assertions** block where the dentist confirms
each criterion with one tap and the packet renders it as attributed clinical judgment — *"Dr. Lau
assessed ferrule height at #16 as >=1.5 mm on 2026-11-16."* This (a) removes image AI from scope, (b)
puts liability exactly where it legally sits, (c) produces a defensible audit artifact, and (d) is what
Smilepass and Cleer lack, because they are verification tools, not clinical-documentation tools.
**The scope limit and the liability contract are the same feature. Build it in M1, not M4.**

**0.4 — The authoritative rule sources are image-based PDFs with no text layer.** Both the CDA crown
checklist and the Health Canada supporting-documentation PDF are scanned/embedded-image documents (same
author metadata — Health Canada authored, CDA distributed). There is no machine-readable CDCP rule
source. Budget **1.5 eng-weeks + 6 SME hours** to hand-transcribe and verify. Also a small moat:
competitors' scrapers get nothing, and the transcription must be redone every time Health Canada
revises the grid, which makes **rule-pack versioning a product feature, not plumbing.**

**0.5 — Denials frequently arrive with no usable reason.** Documented cases show rejections stating
only *"as per the plan criteria,"* unchanged after supervisor escalation. So (a) the retrospective
Look-Back **cannot rely on denial reason codes** and must re-derive gaps from the chart itself, and (b)
*"we tell you why, because Sun Life won't"* is a legitimate, emotionally resonant wedge.

## 1. The demo that sells this

**The Look-Back, then the Friday Five.** Two screens, in that order, 6 minutes total. The Look-Back
sells; the Friday Five is what they buy.

**Beat 1 — The Look-Back (90 seconds).** One screen, four numbers, on their own chart:
```
CDCP Preauthorization Look-Back - last 12 months
  34  preauthorizations submitted
  19  denied - $17,340 of treatment
  11 of 19  were missing a document CDCP explicitly requires
   6 of 19  were never resubmitted - $5,940 of treatment that never happened
```
**The number that lands is not the $17,340. It is "6 were never resubmitted."** Every owner hears that
as: a patient was told no, and walked. Lost revenue *and* undelivered care — the one line that makes a
dentist, not just an office manager, lean forward.

**Beat 2 — The Friday Five (3 minutes).** The working queue, one week of real volume:
```
OPHI - Preauth Queue - Fictional Dental Centre         Week of Nov 9-13
5 CDCP cases open                            $4,860 of treatment at risk

* BLOCKED  T. Kowalchuk  #46  27211 Crown        $1,285   appt Nov 12 (3d)
           - No periapical of #46 within 12 months (last 2023-11-14, 35 mo)
           - Perio chart is 4-point; CDCP requires 6 measurements per tooth
* BLOCKED  A. Singh      #16  27211 Crown        $1,285   appt Nov 16 (7d)
           - Bitewing 2026-08-02 on file, but does not image the apex
* BLOCKED  M. Deng       #37  32221 RCT molar    $1,040   appt Nov 13 (4d)
           - No pre-operative periapical of #37 on file
~ REVIEW   Y. Tremblay   #24  27201 Crown        $  985   3 assertions pending
+ READY    D. Whitfield  #35  32211 RCT bicuspid $  265   awaiting Dr. Lau
```

**Beat 3 — the explanation (30 seconds).** Click Amrit Singh:
> *A bitewing dated 2026-08-02 is on file for #16. Bitewings do not image the periapical region. CDCP
> crown criteria require assessment of crown-to-root ratio and restoration margin relative to the
> alveolar crest — both require a periapical. Take a PA of #16 at the Nov 16 prep appointment.*

Generic "AI for dental insurance" never says *"bitewings do not image the apex."* It is the proof that
the people who built this understand dentistry, not just PDFs. Rehearse so it is on screen by minute
four.

**Beat 4 — the packet (90 seconds).** Click Print Packet. A PDF fans out: cover sheet, procedure table,
labelled image plates with dates, 6-point perio chart render, drafted clinical rationale where every
clinical sentence carries a citation chip to the chart, signature block with the dentist's name,
licence number, timestamp, and the assertions they made. Then the closing line: **"We never send this.
You do."**

### Working backwards: the minimum system

| Component | What it must do for the demo | Eng-weeks |
|---|---|---|
| ABELDent reader | patients, appointments, planned procedures (code + tooth), clinical notes (text), perio exam (structured, with point count), image catalogue (**type, tooth, date — not pixels**), plan/CDCP flag | 6.0 |
| CDCP rule pack | ~28 hand-transcribed rules covering 27xxx + 32xxx/33xxx, each citing its source clause, versioned | 1.5 |
| Evidence matcher | deterministic for structured; LLM-with-span-citation for free-text notes | 3.0 |
| Clinician Assertions | the 5 crown criteria as attributed, timestamped dentist input | 1.0 |
| Rationale drafter | template-scaffolded; every clinical claim carries a chart span or it is blocked | 2.5 |
| Packet renderer | PDF: cover, procedure table, image plates, perio render, rationale, signature block | 3.0 |
| Web app — 5 screens | see below | 7.0 |
| Local agent | Windows service, read-only, outbound-only TLS, tray status | 4.0 |
| Look-Back | **v0 is a founder-run spreadsheet, not software, until M4** | 2.0 |
| Eval harness + audit log | see section 4 | 3.0 |
| **Total** | | **33.0** |

> **Reconciled in PLAN.md:** the rule-pack row is ~12 crown rules only in v1; endodontics is v1.1.

More than three engineers comfortably carry in one release. First thing cut if v1 runs over is the
*generated* rationale — fall back to template plus verbatim chart quotes. Less impressive, still sells.

## 2. Product surface for v1

**Decision: email-triggered web app, plus a silent Windows tray agent. No desktop overlay.**

The documented failure mode is *stacking systems causes staff burnout.* The usual mitigation — "embed
in the PMS" — is wrong here: a desktop overlay pinned to ABELDent is 6–8 eng-weeks, breaks on every
ABELDent release, and we have no vendor relationship to protect us. It would spend a quarter of the
budget defending against a risk product discipline defeats instead.

**The discipline: Ophi has no homepage habit. It has an inbox habit.** One email, 7:00 a.m., only
when money is at risk:
> **3 CDCP cases this week need something before you submit.** $3,610 at risk. -> Open queue

**If there are no gaps, no email is sent** — a tool that is silent when things are fine does not cause
burnout. That is the entire anti-stacking argument, and it costs 1 eng-week.

The web app is Canadian-hosted, opened from that link or a tray icon. The tray agent has no UI beyond
connection status, Pause, and a log — staff must never be asked to operate it. Teams/Slack digest: **do
not build.** Canadian dental front desks run on Outlook and the PMS.

### The five screens
| # | Screen | Purpose | The one thing it must do |
|---|---|---|---|
| 1 | **Preauth Queue** | The Friday Five. Sorted by $ at risk x appointment proximity | **Be empty and boring when there is nothing to do** |
| 2 | **Case Review** | Left: proposed treatment + per-rule verdict with cited clause. Centre: gap checklist. Right: evidence panel — images with type/tooth/date, perio chart, note excerpts with the matching sentence highlighted. Bottom: **Clinician Assertions** | **Never state a gap without naming the clause that creates it** |
| 3 | **Packet Preview & Sign-off** | The packet exactly as the adjudicator will see it, plus the editable rationale with provenance chips | Hold the human-review contract |
| 4 | **Look-Back** | Retrospective denial analysis + recoverability meter. Sales screen *and* permanent ROI screen *and* the measurement instrument | **Show "never resubmitted" count, not just dollars** |
| 5 | **Practice Settings & Audit** | Connection health, provider roster + licence numbers, CDCP grid version, rule-pack version, immutable audit log with CSV export | Make the PHIPA and pilot-agreement obligations self-serve |

> **Reconciled in PLAN.md:** the v1 budget funds 4 screens, and Screen 5 is the named next cut if v1
> runs over. All five are described here.

**Deliberately absent:** dashboards, analytics, a settings maze, anything resembling a second PMS.

### Where the human-review contract lives
Screen 3, enforced structurally in five places:
1. **We never transmit.** Architectural, not policy. Say it in the product, the contract, and the demo.
2. **Provenance gating.** Every generated sentence carries a chip linking to its chart span. A sentence
   without one renders amber and **blocks sign-off** until edited or explicitly accepted under *"I
   attest this reflects my clinical judgment."* Unsourced text cannot silently reach a payer.
3. **Clinician Assertions are attributed by name.** Ophi never asserts ferrule height; the dentist
   does, with a timestamp.
4. **The sign-off record** stores pre-edit draft, post-edit final, the diff, user, licence number,
   timestamp, rule-pack version — the practice's liability artifact, exportable. It is *for them*, and
   also our training corpus if they consent.
5. **Copy law, no exceptions.** Ophi never says "approved," "will be approved," "eligible," or
   "covered." It says *"CDCP crown criteria require a periapical within 12 months. The most recent
   periapical of #46 is dated 2023-11-14."* Statements are about **documentation completeness against a
   cited rule**, never about payer behaviour. This rule is what separates us from Olive AI and from the
   #1 complaint about AI verification ("verified benefits don't match what's paid"). Put it in the style
   guide and enforce it in code review.

## 3. Build sequence

Team: **3 engineers + 1 founder.** Eng A = ingestion/Windows. Eng B = reasoning/rules. Eng C =
product/web. Founder = compliance + BD + SME wrangling. *(If only 2 engineers: cut the generated
rationale entirely and ship template+quotes; cut the Look-Back product to permanent-spreadsheet.)*

### The $0 actions that must happen before any code, in order
| Action | Owner |
|---|---|
| Email `uscls@cda-adc.ca` requesting the USC&LS procedure-code licence. **Longest calendar lead time in the plan, lowest cost.** | Founder |
| Call 10 office managers via officemanagers.ca and ODAA: *"How many CDCP predeterminations did you submit last month?"* **Resolves 0.1.** | Founder |
| File an ATIP request with Health Canada on CDCP administration vendor contracts and any planned intake-validation capability. Free, ~30-day turnaround, **directly tests the Olive scenario.** | Founder |
| Book a Smilepass demo *through an advisor, not from a Ophi address.* Map exactly what they do on predeterminations. | Founder |
| Email ABELDent partnerships: integration guidance + warm intros to 3 reference customers. Do not disclose the wedge. | Founder |

### Milestones

Stages with falsifiable exits, in order. No dates: the calendar follows the work.

**M0 — "Read the chart"**
Ingestion: ABELDent Freemium SQL Server schema mapped; read-only service account; 6 entities extracted
from Fictional Data. Reasoning: rule-pack DSL with an explicit **payer-adapter seam** (2 days — the
Alberta hedge, near-free now, a rewrite later). Product: repo, CI, Canadian-region infra, auth.
Compliance: USC&LS request sent; PHIPA counsel engaged.
**Artifact:** CLI dump of a Fictional Data patient's full preauth-relevant chart as structured JSON.
**Exit (falsifiable):** for >=20 Fictional Data patients (counted from `Transactions` — 24 patients
with planned work, against `tdi`'s 14; any shortfall is filled by UI-entered probe fixtures, not a
blocker), extract planned procedure + tooth + all
radiograph metadata (type/tooth/date) + perio exam with point-count + clinical note text, **zero manual
steps.** If imaging metadata or perio point-count cannot be read, that is a kill-level finding —
escalate immediately.

**M1 — "First verdict"**
Reasoning: 12 crown rules (27xxx) transcribed and encoded, each with source citation. Evidence matcher
for structured fields. Clinician Assertions model. Product: Screen 2, ugly but real. BD: SME billing
coordinator contracted (~$70/hr, 6–8 hrs/wk). First manual Look-Back on 2 friendly clinics' exported
denial reports — **spreadsheet, no product.**
**Exit:** SME reviews 20 crown cases; >=16 verdicts judged correct; **0 cases where Ophi says
"ready" and the SME says "would be denied."** False-ready is the unforgivable error and is tracked
separately from accuracy forever.

**M2 — "The packet"**
Product: packet PDF renderer. Reasoning: rationale drafter v1 **with provenance gating live from day
one, not a later hardening pass.** Ingestion: image file retrieval + render; local agent skeleton as a
Windows service. Compliance: PHIPA agent/ESP agreement template drafted.
**Artifact:** a printed packet on a desk.
**Exit:** 3 external billing coordinators (paid $100 each, recruited via office-manager groups) score
10 packets on the rubric. **Median >=3/4 on Completeness and Correctness, and 0 hallucinated clinical
claims across all 30 scorings.**

**M3 — "The Friday Five"**
Product: Screens 1, 3, 5. Email digest. Sign-off record with diff capture. Reasoning: endodontic rules
(32xxx/33xxx) — 10 rules *(reconciled in PLAN.md: deferred to v1.1)*. Ingestion: agent hardened;
outbound-only TLS; no inbound ports; tray UI. BD: demo rehearsed; first 10 prospect demos booked.
**Artifact:** the full 6-minute demo, run end-to-end on Fictional Data **by someone who did not build
it.**
**Exit:** 3 cold-open tests (team members who did not build the feature, 15 min, no instructions,
recorded) reach a signed packet without asking for help. Playwright visual regression green on 12
canonical cases.

**M4 — "Look-Back + lockdown"**
Product: Screen 4 productized. Security: pen-test of the local agent, secrets handling, encryption at
rest/in transit, Canadian-region inference confirmed with a signed DPA. Reasoning: one **non-CDCP
adapter stub** (Canada Life) to prove the seam is real.
**Exit:** Look-Back runs unattended on a 12-month Fictional Data history and reproduces the SME's
manual spreadsheet result **within +/-10%** on "denials with a documentation gap."

**M5 — "First install"**
Install at pilot clinic #1. Shadow mode on 40% of cases. Instrumentation live.
**Exit:** local agent runs 7 days on a real practice server with **zero unplanned restarts and zero
inbound firewall changes required.**

**M6 — "Pilot running"**
2 clinics live. Weekly Outcome Sweep in use.
**Exit:** >=10 real cases through Case Review -> sign-off, and >=1 outcome recorded via the Sweep.

### What is NOT in v1
SOC 2 Type 2 (needs a 3–12 month observation window after Type 1, so **no DSO deal until well after the
pilot**). Any second PMS (Dentrix/Open Dental are 6–10 eng-weeks each). CDAnet transmission. PMS
write-back. Approval prediction. Radiographic image analysis. Partial dentures. Quebec (Law 25 PIA not
started) and Alberta (statutory Information Manager Agreement) — **pilot clinics must be Ontario, with
BC as the fallback.** Multi-payer adapters beyond the stub. Self-serve signup and billing. Mobile.

## 4. The self-verification loop

Goal: the team works for **10 consecutive days with no external input** and still knows whether it is
getting better.

**4.1 Synthetic case corpus — 150 cases before first install.** From Fictional Data plus hand-authored
perturbations: 90 crown, 45 endo, 15 adversarial. By construction: ~35% ready, ~45% single gap, ~15%
multi-gap, ~5% not-covered-as-coded. Each case is `(chart state, proposed procedure) -> golden output
(verdict, gap list, required evidence, rationale rubric)`. **Golden labels authored by the SME, not by
the engineers who wrote the rules.**
> **Reconciled in PLAN.md:** the v1 cut is **60 cases (40 crown + 20 adversarial)**;
> docs/plan/02-reasoning.md says 120. The 150-case composition above is the uncut target.

**4.2 The SME.** A part-time or retired **dental insurance/billing coordinator** at ~$70/hr, 6–8
hrs/week from M1, plus a **general dentist advisor** at ~$250/hr, 2 hrs/month, for clinical
plausibility of rationales. ~$12,000 over the build: the highest-leverage non-engineering spend in the
plan, and available immediately, since it does not require a clinic.

**4.3 The rubric: "Would a billing coordinator submit this packet as-is?"** Score 0–4 each:
| Dimension | 4 = |
|---|---|
| Completeness | Every CDCP-required artifact present and correctly labelled |
| Correctness | Codes, teeth, surfaces, dates, provider, patient ID all match the chart |
| Evidence sufficiency | Image type/date/tooth actually satisfies the cited rule |
| Rationale defensibility | Narrative supported by chart; no invented findings |
| **Hallucination** | **Binary gate. Any unsourced clinical claim fails the entire packet.** |
| Effort saved | Minutes a coordinator would spend fixing it. 0 = accept as-is |

**Ship gate: >=85% of corpus at "accept as-is or <=2 minutes of edits," AND 0 hallucination failures in
100 consecutive packets.**

**4.4 Golden-output regression in CI.** Every rule-pack change re-runs all 150 cases and diffs verdicts.
**Any changed verdict requires explicit human approval** — snapshot-test discipline applied to clinical
logic. Track false-ready rate as a first-class, separately-alarmed metric.

**4.5 Automated hallucination detection.** Every generated sentence must resolve to a chart span. A
second-model entailment check runs nightly across the corpus; unsourced-claim rate is on the dashboard
from the first day generation exists, target 0.

**4.6 Playwright E2E + visual regression** on all 5 screens across 12 canonical cases, every PR.

**4.7 Red-team Friday, every second week.** Three hours, one person, trying to make Ophi produce a
*confidently wrong* packet. Every success becomes a corpus case — this is where the adversarial 15 come
from.

**4.8 Cold-open test, weekly.** A team member who did not build the feature uses the app for 15 minutes
with no instructions, narrating. Recorded.

**4.9 Paid external coordinator panels — at M2 and again before M5.** 3 coordinators x $100 x 45
minutes, scoring packets on the rubric, recruited from office-manager Facebook groups and ODAA. Zero
PHI, zero clinic, real external signal. **Do not skip these because "we don't have a pilot yet."**

## 5. Pilot design

### Landing the first 3–5 clinics, ranked by cost
1. **ABELDent itself.** Their customers are the only ones we can serve. Ask for integration guidance
   and three warm intros. First.
2. **Coordinators, not dentists.** The office manager is the champion; the dentist signs.
   officemanagers.ca (**which publishes its own CDCP preauthorization factsheet — they are already
   organized around this exact pain**), ODAA, local study clubs.
3. **The free Look-Back as the lead magnet.** *"30 minutes, we run it on your last 12 months, you keep
   the PDF whether or not you buy."* A lead magnet, a demo, *and* the measurement instrument at once.
4. **Practice-management consultants and dental accountants** in Ontario who already sit across from
   owners.
5. **No paid advertising.** Not at $4.2k ACV, not yet.

**Funnel target: 25 conversations -> 8 Look-Backs -> 4 pilots signed, all Ontario.**

### The honest statistical reality
4 clinics x ~75 preauths/dentist/yr over 90 days ~= **150 cases total** — nowhere near enough to prove a
denial-rate reduction. So:
- **The pilot measures adoption, gap prevalence, and packet acceptance.** n=150 is plenty for that.
- **The Look-Back measures recoverability.** Run it on **20+ clinics even if only 4 pilot** — 300–1,000
  historical denials. That is where the 20% assumption actually gets tested.

Separate these two instruments and do not conflate them in a board deck.

### Instrument from day one
Per case: `case_id`, `patient_hash`, codes, tooth, appointment date, payer. Verdict at T0 + gap list +
rule-pack version. Coordinator action (accepted / edited-with-diff / overrode / abandoned). Seconds on
Case Review and Packet. Submitted? when? how?

**The Outcome Sweep** — a weekly 30-second, two-click screen where the coordinator records approved /
denied / partial / no-response for last week's cases, plus any reason text. **This is the single most
important screen we will build, and it is not in the top five, because it must feel like nothing.**
Without outcomes we measure nothing. Given that CDCP denials often carry no usable reason, **capture the
raw text verbatim and re-derive the gap from the chart ourselves.** Also per denial: did they resubmit?
outcome? days elapsed? dollars recovered? And the under-measured one: **did the patient proceed with
treatment at all?** A denied crown that never happens is the biggest dollar in this business and nobody
has quantified it.

**Shadow mode:** randomize by patient-ID hash, ~40% silent for the first 30 days. Not statistically
powered, but directional signal on gap-flag rate. **Must be disclosed in the agreement.**

### The pilot agreement must contain
PHIPA **agent + electronic service provider** designation, clinic as HIC, permitted uses and limits
written out. Explicit **"Ophi does not transmit to any payer."** Data minimization schedule naming
every table and field read. Radiographs handled as metadata plus rendered copies, with a stated
retention window. Subprocessor list with Canadian residency attestation, **including the LLM inference
endpoint** — the sharp edge; confirm the endpoint and DPA before the first install, or design PHI
redaction before egress as the fallback. Breach notification timelines. Right to audit. Data return and
destruction within 30 days of termination. **Measurement rights** — de-identified outcome data may be
aggregated and published; clinic named only with consent. Shadow-mode consent. **Clinical
responsibility clause: the dentist is solely responsible for clinical content and submission decisions;
Ophi is a documentation assistant, not a benefits determination.** **Termination for convenience on
14 days' notice** (removes purchase anxiety). **Pre-agreed conversion price signed at pilot start,
auto-converting unless they opt out** — this is how you avoid a second sales cycle. Named contact for a
weekly 20-minute call.

### Numeric success criteria (assess after the pilots' first full quarter)
| Metric | Threshold |
|---|---|
| Eligible CDCP preauth cases flowing through Ophi | **>=70%** |
| Packets accepted with <=2 min of edits | **>=60%** |
| Cases with a real gap caught (coordinator confirms "I would have submitted without this") | **>=25%** |
| Hallucinated clinical claims reaching sign-off | **0** |
| False-ready cases (said ready, was denied for documentation) | **<=2%** |
| Look-Back across >=10 clinics: denials that are documentation-recoverable | **>=12%** |
| Pilots converting to paid at >=$249/mo | **>=3 of 5** |
| "Very disappointed if it went away" (Sean Ellis) | **>=60%** |

## 6. Pricing and packaging

**Recommendation: $349/clinic/month, flat. Unlimited users, unlimited cases, one location. Annual
$3,490 (two months free).**

- **Per-claim is dead.** DentalXChange anchors $0.25/claim and $25/mo unlimited attachments. Never set
  foot on that pricing surface.
- **Per-user is self-defeating.** Zuub ($299/user) and Dental Intelligence ($399/user) price per seat;
  we need the *whole* front desk in the tool for adoption. Flat pricing is both correct and a sales
  weapon: *"one price, put everyone on it."*
- **$349 is under the $400 psychological line,** above Denti.AI Detect's $49 (which signals "feature"),
  and at/below the $399 tier that demonstrably clears in Canadian dental.
- **The documented churn case** — a single-doctor practice that dropped AI verification because it cost
  more than a part-time coordinator — sets a hard ceiling. $349/mo ~= 11 hours of a $30/hr coordinator.
  Stay well under $1,000.

### The labour story is too weak. What to do about it.
$1,180/clinic/yr of displaced labour against a $4,188/yr price is a losing argument. **Never lead with
time saved.** Rank the pitch:
1. **Denied revenue recovered.** Derive it in front of them: 1.9M preauths x 54% denied x ~$900 avg
   CDCP-rate case value = ~$923M denied treatment nationally x 20% recoverable = **$185M**, which lands
   inside the researched $140–180M band, so the model is self-consistent. Per clinic that is
   **$5,500–$10,300/yr** depending on whether you divide by 33,287 or 17,857 establishments. At the
   bottom of that range a $349 product is barely worth it: **replace this estimate with a measured
   Look-Back number as fast as possible.**
2. **Patient-promise risk.** *"You told the patient it was covered."* Visceral for owners, unquantified,
   real.
3. **Case acceptance** — the denied crown that never happens. Biggest dollar, least measured. Name it as
   a hypothesis, not a claim.

### Packaging
| Tier | Price | Contents | When |
|---|---|---|---|
| **Look-Back** | Free, quarterly, <=200 past cases | Retrospective denial analysis | M4 |
| **Ophi Core** | **$349/mo/location** | CDCP gap-check, packet assembly, Look-Back, audit log, 1 PMS connection | M6 |
| **Ophi Multi-Payer** | **$549/mo/location** | Carrier adapters: Canada Life, Desjardins, Alberta Blue Cross, TELUS AdjudiCare, Beneva | After v1 |
| **Group/DSO** | ~$249/location, min 10 | Requires SOC 2 Type 2 | After SOC 2 Type 2 |

**Founding-clinic terms:** first 5 pilots free for 90 days, then **$249/mo locked for 12 months**,
signed at pilot start. **No free trial of Core** — 30-day money-back instead; free trials of workflow
tools produce "installed and forgot," which is our documented failure mode. Multi-Payer is the
Alberta-opt-out hedge converted into a price lever, the right way to monetize a risk mitigation.

**Unit economics reality check:** 3 engineers + founder ~= $70k/mo burn. Breakeven ~= **200 clinics** =
1.1% of employer establishments. Achievable — but this plan currently contains no salesperson and no
self-serve motion. At $4.2k ACV you need a channel: ABELDent, a DSO, or a billing-service reseller.
**Largest non-technical gap in the plan.**

## 7. Kill criteria

**K1 — Volume. Test first.** If 10 office managers report a median of **<2 CDCP predeterminations per
month**, the addressable work does not exist. **Stop.** (Cheapest kill in the plan — do it first.)

**K2 — Recoverability.** If Look-Backs across >=10 clinics and >=300 real denials show **<8%
documentation-recoverable**, the revenue story collapses, the price ceiling drops to ~$149, and this is
a feature, not a company. **Stop, or sell it to someone who already has distribution.**

**K3 — Wrong denial mechanism.** If **<30% of crown denials are attributable to missing or insufficient
documentation** — i.e. they would be denied with a perfect packet because the tooth simply does not meet
criteria — the premise is inverted. **Pivot** to a pre-treatment-planning coverage advisor ("don't
propose this, propose that"): a different, smaller, but real product.

**K4 — Payer fixes it at intake. Monitor continuously.** If Sun Life or Health Canada ships structured
intake validation, a portal that rejects incomplete submissions with error codes, or mandatory
attachment schemas, provider-side value evaporates. **This is exactly how Olive AI died.** Monitor CDCP
provider bulletins, CDA/ODA member communications, the ATIP response.

**K5 — Payer-side vendor contracted.** If Health Canada contracts a single payer-side documentation
vendor (the Cohere Health pattern), **pivot immediately** — sell into that vendor as the provider-side
complement, or exit.

**K6 — Smilepass ships it.** They already have ABELDent integration, CDCP awareness, and distribution.
If they ship predetermination submission with gap-checking, we are 12 months behind on integrations with
a narrower product. Either we have a wedge they structurally cannot copy (the Clinician Assertions
liability artifact and evidence depth are the candidates) or **stop.**

**K7 — Ingestion is impossible.** If imaging metadata, perio point-count and clinical notes cannot be
read out of ABELDent reliably and licensably, the entire local-agent thesis is broken. **Early kill,
cheapest of all.**

**K8 — USC&LS licence denied or priced prohibitively.** Without the right to store and display the
procedure code set, the product is unshippable as designed.

**K9 — One hallucinated clinical finding reaches a real submission. Stop shipping.** Root cause.
Seriously reconsider whether generative rationale belongs in v1 at all, versus template plus verbatim
chart quotes. **One-strike rule.**

**K10 — Adoption. Two months into the pilot.** If <50% of eligible cases flow through Ophi in 3+ of
4 clinics, staff will not use it. **No accuracy improvement fixes that.**

## 8. Sequenced risk register (P: 0–1, I: 1–5)

| # | Risk | P | I | Score | Cheapest next action | Owner |
|---|---|---|---|---|---|---|
| 1 | **Recoverability <8%** — the whole pricing thesis | 0.40 | 5 | **2.00** | Manual spreadsheet Look-Back on 2 friendly clinics' denial exports. No product needed. | Founder + SME |
| 2 | **No distribution at $4.2k ACV** | 0.50 | 4 | **2.00** | 20 discovery calls + ABELDent partnerships conversation | Founder |
| 3 | **Per-clinic preauth volume is 30x lower than modelled** | 0.35 | 5 | **1.75** | 10 phone calls to office managers. Zero cost. | Founder |
| 4 | **Payer fixes it at intake / contracts a vendor** (Olive scenario) | 0.35 | 5 | **1.75** | Subscribe to CDCP provider bulletins; file the ATIP request; call two Sun Life provider-relations contacts | Founder |
| 5 | **ABELDent read access blocked or fragile** | 0.35 | 5 | **1.75** | 2-day DB spike on Freemium; email ABELDent integration team at the same time; design an ODBC/report-export fallback | Eng A |
| 6 | **Smilepass/Cleer ship predetermination submission** | 0.45 | 3.5 | **1.58** | Book a Smilepass demo through an advisor; map their predetermination behaviour precisely | Founder |
| 7 | **Staff adoption failure (system stacking)** | 0.40 | 4 | **1.60** | Email-first architecture (already in the design); weekly cold-open tests; paid coordinator panel at M2 | Eng C + Founder |
| 8 | **Hallucinated clinical content -> trust/liability incident** | 0.30 | 5 | **1.50** | Make provenance gating a blocking M2 feature, not M4 polish; unsourced-claim rate on the dashboard from the first generated sentence | Eng B |

**Tracked but outside the top 8:** CDCP provincial erosion beyond Alberta (P 0.5 x I 3 — mitigated by
building the adapter seam in M0 for ~2 engineer-days); the compliance calendar — USC&LS / PHIPA / Law 25
/ SOC 2 (P 0.4 x I 3 — mitigated by sending the USC&LS email first and explicitly deferring Quebec and
SOC 2); PHI-safe Canadian-region LLM inference (P 0.3 x I 4 — confirm endpoint and DPA before first
install, pre-egress redaction as fallback).

## 9. Unverified assumptions ledger

| # | Assumption | Status | Test |
|---|---|---|---|
| A1 | ~75 preauths/dentist/yr, not ~2.4 | **Contradicted by one source** | 10 phone calls, first |
| A2 | 20% of denials are documentation-recoverable | Unverified; the most important thing to measure | Look-Back on >=10 clinics |
| A3 | Avg CDCP-rate preauth case value ~$900 | Modelled, not measured. Reconciles to the $140–180M national figure, so at least self-consistent | Extract from pilot fee schedules |
| A4 | Coordinators will do a weekly Outcome Sweep | Unverified, and it gates all measurement | Test in the M2 coordinator panel |
| A5 | Denial reason text is usable enough to classify | **Evidence says often not** ("as per the plan criteria") | Manual Look-Back |
| A6 | ABELDent stores radiograph tooth number and type as queryable metadata | Unverified; if false, gap detection on imaging degrades sharply | M0 spike |
| A7 | Denied preauth -> patient does not proceed (lost case) | Pure hypothesis. **Potentially the largest dollar in the business.** | Pilot instrumentation |
