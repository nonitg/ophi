# Market Research — CDCP Preauth Copilot

Verified 2026-09-17. UNVERIFIED tags are load-bearing — do not repeat them as fact.

## Headline

Pain is real and unusually well-documented. But the honest labour math is small: preauth alone is
**~$1,000–1,500/clinic/year of displaceable staff time**. The business only works if priced against
**recovered revenue**, not saved minutes — and if preauth is a wedge into eligibility + claims +
denials, not the whole product. Two Canadian startups already own the adjacent beachhead.

## Sizing

| Metric | Value | Source |
|---|---|---|
| Employer dental establishments, Canada (NAICS 6212) | **17,857** (33,287 incl. non-employer/sole-prop) | ISED Canadian Industry Statistics 2025 |
| Employer size split | Micro 1–4 emp: 7,086 (39.7%); Small 5–99: 10,749 (60.2%); Medium 20; Large 2 | same |
| Industry revenue | **$23.1B**, +3.9% 2026, 2.0% 5-yr CAGR | IBISWorld Canada, Feb 2026 |
| Dentists/specialists in CDCP | 25,409 | canada.ca, Aug 2026 |
| CDCP benefits funding | $3.4B (2026-27) | Oral Health Group |
| CDCP program admin cost | $472.9M cumulative + $149M Supp. Estimates (A) | same |

**Use 17,857 as the serviceable clinic count**, not 33,287 — the higher number double-counts
incorporated sole practitioners.

### Bottom-up TAM — the number that matters

```
1.9M preauth requests/yr / ~18,000 employer clinics   ~= 106 preauths/clinic/yr (~2/week)
106 x 25 min each                                     ~= 44 staff-hours/clinic/yr
44 hrs x $26.70/hr (ON treatment coordinator)         ~= $1,180/clinic/yr of labour
x 18,000 clinics                                      ~= $21M/yr total Canadian labour pool
```

**A $21M/yr labour pool cannot support a venture-scale company at 20% capture.** Price on revenue
recovery instead:

```
1.9M requests x ~54% denied                           ~= 1.0M denials/yr
Assume 20% recoverable with complete documentation    ~= 200,000 cases/yr
x ~$700-900 CDCP crown-class fee                      ~= $140M-180M/yr recoverable revenue
```

**7–9x larger than the labour number.** DERIVED — the 20% recoverability assumption is the single
most important thing a pilot must measure.

### The US comparison is a trap
DentalXChange alone processes 300M dental claims/yr across ~200,000 providers. Canada's entire
dental industry is $23.1B with ~25,400 dentists — **roughly 1/10th the US market on a completely
incompatible transmission standard (CDAnet, not X12).** None of the Canadian rails, certifications
or payer integrations transfer. Any "win Canada then port to the US" plan must account for this.

## Competitors

### Tier 1 — direct, Canadian, already selling to our buyer

| Company | What | CDCP | PMS coverage | Threat |
|---|---|---|---|---|
| **Smilepass** (Toronto) | AI insurance verification, digital treatment plans, payments/AR, financing. Canada-first | **Yes, explicit.** Verifies CDCP enrolment/benefit periods, captures income-tiered co-pay, **tracks submitted predeterminations and auto-updates the PMS on approval** | Dentrix, Open Dental, Curve, **Tracker, ABELDent, ClearDent, MaxiDent, Paradigm** | **Highest.** Owns verification + the exact PMS list we need. Stops short of *submitting* predeterminations — our only gap, and narrow |
| **Cleer** | AI agents verifying dental insurance, "no hold times, no portals". **200+ offices**. Presented at Pacific Dental Conference 2026 | Canada-only positioning | not published | High — 200+ existing Canadian clinic relationships = distribution we'd have to out-run |

Funding, headcount, pricing for both: **UNVERIFIED, all unpublished.**

### Tier 2 — US dental claims/preauth, structurally blocked from Canada
- **Curo** (fka FlowHx) — closest US analog: automated pre-determination processing, NLP clinical-note
  extraction, clearinghouse APIs, ERA posting, approval-rate analytics. US-hosted, HIPAA framing, no CDCP.
- **Vyne Dental** (Trellis/FastAttach) — legacy leader in dental attachments. Flat monthly unlimited. PE-owned. **Not a Canadian clearinghouse.**
- **DentalXChange** — clearinghouse since 1989, ~200k providers, ~1,400 payers, 300M claims/yr.
  **~$0.25/claim; $25/mo unlimited portal attachments; $19.95/mo eligibility; $19.95/mo ERA.** US only.
- **Onederful** (acquired by Vyne) — real-time eligibility API, 200+ US payers.
- **Zuub** — AI verification, treatment plans, financing, RCM. **$299/user/month.** No CDAnet evidence.
- **Zentist** (Remit AI) — EOB/ERA aggregation, payment posting, denial categorization. 2,300+ practices,
  $2.1B revenue managed. **Only automates Open Dental**; humans for other PMS. US.
- **Sikka** — PMS data-access middleware. 400+ PMS, 100+ endpoints, 50,000+ practices; **explicitly US,
  Canada, Australia.** **$350/mo licence + $35–175/mo per-location tier**; writeback quote-only.
  Our build-vs-buy decision.
- **Dental Intelligence** — analytics, **from $399/user/mo**, sold in Canada.
- **eAssist** — outsourced human billing. **2.5–3.5% of collections** at >$150k/mo; **4.99–7.99% +
  minimums** for small practices. **US-focused; no Canadian pricing found** — possibly a signal that
  Canadian dental billing outsourcing is structurally underdeveloped, because CDAnet auto-adjudicates
  most claims in seconds.

### Tier 3 — dental clinical AI (possible partners or acquirers)
Overjet ($35M Series C Jan 2026; sells to providers **and payers**) - Pearl ($40M Series B Nov 2025,
ADA strategic investment) - VideaHealth ($22M Series B; **Health Canada licensed**, deployed across
123Dentist) - **Denti.AI** (Toronto, Health Canada licensed; **Detect $49/mo; Scribe+Voice Perio
$399/mo**) - LightSpun (fka 32Health, $13M Series A Sep 2025; **payer-side**).

**As of May 2026 no AI dental diagnostic software holds a full Health Canada licence for autonomous
caries detection**, with a typical 12–24 month lag behind FDA clearance. If our product ever makes a
*clinical* assertion rather than an *administrative* one, we inherit that regulatory lag.

### Tier 4 — medical prior-auth, the business-model evidence
| Company | Model | Funding | Outcome |
|---|---|---|---|
| **Cohere Health** | **Payer-paid** | $90M Series C 2025, $200M total (Temasek) | 12M+ prior auths/yr, up to 90% auto-approved, all 50 states |
| **Humata Health** | Provider-paid | $25M (Blue Venture Fund, LRVHealth, Optum Ventures) | 225+ hospitals, 90% touchless. **Being acquired by R1 RCM, closing Q3 2026** |
| **Anomaly Insights** | Provider-paid | $17M Series A May 2026, $34M total | 20+ health systems |
| **Olive AI** | Provider-paid (bought Verata for $120M) | **$902M raised, $4B valuation** | **Shut down.** |
| **Candid Health** | Provider-paid RCM | $120M Series D | $7B annual claim volume |
| **Adonis** | Provider-paid RCM | $40M Series C 2026 | 4x revenue growth 2025, >130% NRR |

**>$500M went into AI-RCM in 2026 alone.**

**The pattern:** provider-paid prior-auth *does* work — but every verified success sells to
**hospitals and health systems** with millions in denied revenue and a dedicated RCM budget line.
**Zero verified examples of provider-paid prior-auth succeeding at 2–5 operatory single-site
practice scale.** Payer-paid (Cohere) reaches 12M transactions/yr on a fraction of the sales effort.
**The money is on the payer side.** In Canada that payer is Sun Life, and behind it Health Canada —
currently paying $472.9M+ in admin partly to chase incomplete submissions.

## Canadian PMS landscape

**40 vendors / 44 products are CDAnet-certified; only 28 support attachments.**

| PMS | Vendor | Cloud/on-prem | CDAnet attachments | API |
|---|---|---|---|---|
| **ABELDent** | ABELDent Inc (Burlington ON) | Both (Azure cloud / Local Plus) | yes | **None public.** Integration list is imaging-only |
| **Tracker** | Bridge Network | On-prem | yes | Read-only via 3rd-party bridges. ON multi-chair |
| **ClearDent** | Prococious (Burnaby BC) | Cloud/on-prem/hybrid | yes | **Formal partner program + API, read AND write-back.** Canadian hosting. Strong BC/AB |
| **Dentrix** | Henry Schein One Canada | Hybrid | yes | Vendor-gated (API Exchange) |
| **Open Dental** | Open Dental | On-prem | yes | **Best API/docs in the market** |
| **Curve Hero** | Curve Dental | Cloud | **NO attachments** | — |
| Power Practice/axiUm, MaxiDent, Paradigm, Akitu One, ADSTRA, Gold, Quadra, Domtrak, Oryx, Consult-PRO, ExcelDent | various | — | yes | — |
| Progident/Clinique, Dentitek, CLICK | Progident/Progitek/Info-Data | — | mostly yes | Quebec |

**No credible Canada-specific PMS market-share data exists publicly.** Directional only: ABELDent,
ClearDent and Tracker are the top Canadian-built platforms; Tracker + ABELDent skew Ontario,
ClearDent skews BC/AB. North American shares (Henry Schein 18–22%, Open Dental 14–18%) are **not**
Canadian. **UNVERIFIED — commission our own count.**

### Correction to the starting assumption
**"AbleDent (Land Software)" does not exist.** No dental PMS vendor named "Land Software" was found.
The product is **ABELDent**, by **ABELDent Inc. / ABELSoft** (Burlington ON, in healthcare since 1977).

### ABELDent Freemium
Free, no credit card, downloadable, full premium UI. **SQL Server Express 2022/2019 only** (10GB db
cap, 1410MB RAM, 1 socket/4 cores). Sized for 2–4 workstations. LMS access 90 days.
**Excluded: telephone support, one-on-one training, software updates, data migration, PCS.**
Target: evaluators, students, startups, hygiene practices.

**Strategic read:** it is a lead-gen funnel for new/small practices, deliberately crippled on support
and updates. Its users are **the smallest, poorest, lowest-CDCP-volume practices in Canada**, on
on-prem SQL Express, with **no vendor support contract and no public API**. That is close to the
worst possible *first customer* profile. As a free local **development sandbox with a real SQL
schema**, it is excellent. Keep those two roles separate.

ABELDent paid pricing (~$99/mo single user; $299–599/mo up to 100 users; $1,000–5,000
implementation) comes only from an aggregator, not the vendor. **UNVERIFIED.**

## Buyer and willingness to pay

Independent practices: **dentist-owner and office/practice manager decide jointly, 4–12 week
evaluation cycles.** DSO-affiliated: procurement moves to the DSO.
**Dentalcorp ~550 practices. 123Dentist 400+** (after the 2022 Altima/Lapointe merger).
Do DSOs build in-house? Mostly **no — they partner** (123Dentist deployed VideaHealth). Dentalcorp
runs proprietary `hellodent` and publishes CDCP preauth patient guides, but **no evidence of building
preauth tooling. UNVERIFIED.**

| Anchor | Price |
|---|---|
| Denti.AI Detect (Canadian, HC-licensed) | **$49/mo** — the floor |
| Denti.AI Scribe + Voice Perio | **$399/mo** — Canadian ceiling for a point AI tool |
| Dental Intelligence | $399/user/mo |
| Zuub | $299/user/mo |
| Sikka (our input cost) | **$385+/mo/practice** before write-back |
| AI dental VA | $199–870/mo |
| Human dental VA FTE | $1,200–2,500/mo |
| eAssist | 2.5–7.99% of collections |
| DentalXChange | **$0.25/claim; $25/mo unlimited attachments** |

**Landing zone: $199–499/clinic/month**, or outcome-priced against approved cases.
**Do not price per-claim** — DentalXChange anchored it at $0.25 and we cannot win there.

## What won't stick — the evidence

1. **Olive AI.** $902M raised, $4B valuation, bought Verata for $120M to own prior auth, then shut
   down. Documented failure mode: "exaggerated capabilities," promised 5x admin savings and "didn't
   come close," relied on "rough estimates." One postmortem: *"figuring out prior authorization rules
   by brute force learning from approvals/rejections didn't seem like a sustainable model."*
2. **AI verification accuracy is the #1 field complaint.** NC practice's AI showed 80% filling
   coverage but missed that posterior composites were excluded; AZ practice's AI missed a six-month
   crown waiting period -> denied claim; IL practice's AI worked for Delta/Cigna but not regional
   insurers so staff still phoned. *"The single most common complaint from dental office managers is
   that the benefits verified before treatment do not match what the insurance company actually
   paid."* **Liability stays with the practice regardless.**
3. **A single-doctor Ohio practice abandoned AI verification after three months** because
   subscription fees exceeded hiring a part-time coordinator. That is our exact buyer doing the math.
4. **Switching costs and IT conservatism are severe.** ~$219,032 total cost for a 5-doctor PMS
   migration with 30–40% productivity drop in month 1. Proprietary imaging formats lock practices in.
   Support frustration is "the most consistent complaint across the board." Many clinics still run
   Windows 10 approaching end-of-life on on-prem servers.
5. **Canadian-specific AI failure modes.** AI scribes hit only 85–90% clinical accuracy; **not all
   handle Canadian procedure codes natively** (ADA->CDA mapping introduces error); AI receptionists
   fail on Mandarin, Cantonese, Punjabi, Tamil — all common in the GTA. *"Stacking three new systems
   at once is a recipe for staff burnout and poor adoption."*
6. **Adoption, not capability, kills dental software** — overbuilding, ignoring users, rollouts that
   fail "usually because the team didn't adopt them."

## Regulatory / platform risk

### CDAnet is a real gate
*"Unless you have CDA-certified practice management software licensed from an independent software
vendor, you will not be able to use CDAnet or ITRANS."* Access is tied to provincial dental
association membership (CDA Affiliate in Quebec); no extra fee for members. Canadian clearinghouses:
**ITRANS 2.0 (dentists only)**, Claimstream / TELUS CCDWS (hygienists only), RAMQ E-Claims
("Incomplete. Do not use."). **No US clearinghouse serves Canada.**

**Whether a non-PMS third party can be certified is UNVERIFIED** — CDA pages do not address service
bureaus. **Call CDA Practice Support Services, 1-866-788-1212, pss@cda-adc.ca, before writing a line
of transmission code.** Highest-priority open question.

### Sun Life CDCP billing agreement
**Third-party agents are explicitly contemplated and permitted:** *"Employees, agents, and
subcontractors must comply with the CDCP claims processing and payment terms in respect of claims
that are submitted on your behalf."* **Favourable** — we can operate as the provider's agent. The
provider remains liable. Full text could not be retrieved (sunlife.ca 403s automated fetches);
**have a lawyer read the PDF manually before launch.** Sun Life's 403-on-bots posture is itself a
signal: **do not build on portal scraping.**

### The audit climate is turning hostile — and cuts both ways
A health law specialist: *"In the past year, I have seen more insurer audits involving dentists than
in the previous five years combined."* One Ontario practice with >$2M revenue got audit letters
questioning claims back to **2017**. **Nearly half of Canadian insurers use AI-enabled analytics**
(KPMG Canada 2025); insurers have hired hygienists and ex-police officers to run them. One delisted
dentist lost **20% of annual revenue and 40% of practice value.**

Tailwind: defensible documentation is now existential for dentists.
Liability: if our product auto-generates a "clinical rationale" that later reads as templated
justification across 500 clinics, we have built an audit magnet and a plaintiff's exhibit.

## Will stick — 5 ranked bets

1. **"Complete-on-first-submission" for crowns, specifically.** Crowns approve at ~37%, the worst
   category, and are exactly where radiographs, perio charting and treatment plans go missing. The
   rules are a one-page table; the hard part is finding the right PA/BW within 12 months and the
   perio chart inside a messy legacy chart. Ship a product that refuses to let a crown preauth go out
   incomplete and prove it lifts a clinic from 37% to 55%+. Narrow, measurable, attributable.
2. **Outcome-based pricing against approved cases, not saved minutes.** $21M labour pool vs
   $140–180M recoverable-revenue pool. At $199–499/clinic/mo the ROI story must be "you got 3 more
   crowns approved," not "you saved 45 hours." Also inoculates against the Ohio-practice math.
3. **Attachment fallback for the 16 non-attachment-capable certified products (and the paper tail).**
   Clinics on Curve Hero, X-Trac, Dolphin, Enterdent, Dental 365, Patient7, MacPractice, TDO cannot
   send CDAnet attachments at all and are stuck with mail/fax/SecureSend/BrightSquid. Being the
   assembler-and-router for that cohort is real, unserved, and **requires no CDAnet certification.**
4. **Sell to Dentalcorp (550) and 123Dentist (400+) before single sites.** Per-practice sales at
   $300/mo against a 4–12 week evaluation cycle is unit-economics suicide across 18,000 clinics.
   Both partner rather than build. Two logos = ~950 clinics.
5. **Audit-defensible documentation as the second act.** A system producing a contemporaneous,
   evidence-linked record of *why* each submission was made is worth more than one that just gets
   approvals — and is far stickier, because we become the clinic's audit insurance.

## Won't stick — 5 ranked things to avoid

1. **Making ABELDent Freemium clinics the first paying segment.** Lead-gen funnel for startups and
   hygiene practices, no support contract, no updates, no API, lowest CDCP volume, least money.
   **First paid integration should be ClearDent (partner program + API + write-back) or Open Dental.**
2. **Per-claim or per-transaction pricing.** DentalXChange anchored at $0.25/claim and $25/mo
   unlimited attachments. No room underneath; frames us as plumbing, not revenue recovery.
3. **A rules engine as the core product.** The CDCP preauth rules are one PDF table. Health Canada
   changes it quarterly. Rules are a maintenance cost, not an asset. Smilepass or Cleer can encode
   them in a sprint.
4. **Anything that scrapes the Sun Life provider portal.** 403s to automated agents sitewide.
   Building on a platform already actively blocking us, whose terms we cannot fully read.
5. **Broad "AI copilot" surface area at launch.** Eligibility + claims + denials + reconsiderations +
   prediction all at once is the Olive failure mode, and hits the documented adoption ceiling.

## Biggest existential risk: CDCP political fragmentation

**Alberta formally notified Health Canada of intent to opt out in December 2024**, after Premier
Smith's June 2024 letter calling the CDCP *"inferior, wasteful and infringing on provincial
jurisdiction"* and demanding the funds as a direct transfer. **306,000+ Albertans enrolled.** The
**Dental Care Measures Act contains explicit provincial opt-out provisions** — Ottawa anticipated
this. Quebec "could follow a similar path"; Saskatchewan and BC have voiced overlap concerns.

If two or three provinces opt out, "CDCP preauthorization copilot" fragments into N provincial
programs with N rule sets, N payers and N fee grids — in a market one-tenth the size of the US.

**The compounding version:** Health Canada spends $472.9M+ on admin, much of it absorbing rework from
a ~20% incomplete-submission rate. The cheapest fix available to *them* is not to subsidize 18,000
clinic-side copilots — it is to make Sun Life reject incomplete submissions at intake with structured
error codes, or contract one Cohere-style payer-side vendor. **The moment the payer fixes this
upstream, the provider-side product's core value evaporates.** That is precisely what killed Olive.

**Mitigation:** architect from day one so CDCP is *one payer adapter among many*, not the product.
Eight carriers already accept CDAnet attachments (Alberta Blue Cross, Beneva, Canada Life,
Desjardins, TELUS AdjudiCare, AGA Financial, Quikcard, Sun Life) — the predetermination-packet
problem exists across all of them. Build the **chart-evidence-extraction engine** as the durable
asset; treat every payer's rule set as swappable configuration. And open a conversation with Sun Life
and Health Canada early: if the money is on the payer side — and the Cohere/Humata/Olive evidence
says it is — better to discover that in a meeting than in a post-mortem.

## Open questions to close

1. **Can a non-PMS third party obtain CDAnet/ITRANS certification, or must we ride inside a certified
   PMS?** Call CDA PSS, 1-866-788-1212. Highest priority.
2. **What is the true submissions-per-case ratio?** The 1.9M-vs-1% gap is the central thesis and is
   currently derived, not sourced.
3. **Smilepass and Cleer funding, headcount, customer counts, pricing.** All unpublished.
4. **ABELDent's actual integration terms.** No public API.
5. **Full text of the Sun Life CDCP billing agreement** re: automation and agent obligations.
