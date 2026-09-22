# Expansion research — where else Colombus could go

Researched 2026-09-18. Four parallel tracks: clinic operations, access to care, records/interop, payer side.
Evidence grades are load-bearing. **VERIFIED** = named primary source (government, regulator, college,
peer-reviewed, company's own filing). **CLAIMED** = vendor, advocacy, media, or self-report.
**NO DATA FOUND** = searched, nothing exists — never estimated to fill a hole.

## The headline: the preauth problem is real, but not the one we were selling

| Fact | Grade | Source |
|---|---|---|
| **480,000 complete preauth requests, Mar 1 – May 31 2026** (≈1.9M/yr) | VERIFIED — Health Canada figures given to Oral Health Group | [oralhealthgroup.com](https://www.oralhealthgroup.com/dental-governance-regulations/cdcp-update-less-than-half-of-dental-preauthorization-requests-approved-as-new-trends-emerge-1003996608/) |
| **46% approved overall. Crowns ~37%. Partial dentures >76%. Root canals 44%** | VERIFIED — same | same |
| **>95% processed within 7 days, majority under 5** | VERIFIED — same | same |
| Health Canada attributes elevated denials partly to *"an unexpectedly high volume of incomplete submissions"* | CLAIMED — official's statement via trade press, no number published | [benefitsandpensionsmonitor.com](https://www.benefitsandpensionsmonitor.com/benefits/group-health/canadians-left-in-the-dark-as-cdcp-claim-denials-expose-design-flaws/393687) |
| Health Canada also attributes denials to *clinical criteria "more stringent than private insurance"* | VERIFIED — Health Canada via Oral Health Group | first source above |

**This resolves the volume question.** 480k/quarter over ~18,000 employer clinics is ~107 preauths/clinic/yr,
≈2/week. The ~2.4/dentist/yr low end in `market.md` is dead. Volume and denial mass are real.

**It also explains the dismissive clinic.** >95% processed in under 7 days, sent over CDAnet in minutes.
A clinic asked "is sending pre-ops much work?" will correctly say no. **Nothing in our thesis ever claimed
otherwise** — the claim is about the 54% that come back denied. We have been asking about the wrong half
of the transaction.

**The one number that decides everything is still open.** Health Canada names *both* incomplete submissions
*and* stringent clinical criteria as denial drivers, and has published **no split between them**. If most of
the 54% are clinically ineligible crowns, a documentation engine cannot flip them and there is no business.
Recoverability, not volume, is now the whole thesis. `colombus/lookback.py` is the instrument that answers it.

## Ranked expansion options

Scored on (evidence strength × reuse of the extraction engine × an identified payer).

### 1. Multi-payer predetermination — the cheapest real expansion
Private carriers require predeterminations with documentation that closely mirrors CDCP's.
**VERIFIED:** Manulife requires a treatment plan/predetermination when a proposed course exceeds **$500**,
and requires **pre-treatment x-rays for crowns** ([manulife.ca group benefits FAQ and dental claim form]).
CDCP's crown checklist is periapical + bitewing within 12 months, perio chart within 12 months, treatment plan
([cda-adc.ca Preauthorization Checklist for Crowns]). Canada Life targets a 5-business-day predetermination
turnaround ([welcome.canadalife.com/dental-provider/faq.html]).

- **Engine reuse: total.** The rule pack is ~1.5 of 34.5 engineer-weeks. Everything else is payer-agnostic by design.
- **Why it matters:** it kills the CDCP political-fragmentation risk in `market.md`. Alberta's opt-out (notice
  given Dec 2024) **still has not happened** — CDCP remains operational there with 306,000+ enrolled as of
  July 2026 — but a multi-payer engine stops caring either way.
- **Disconfirming signal:** only Manulife's threshold was found in primary sources. Sun Life's private book,
  Canada Life, Green Shield, Desjardins, Beneva and Equitable thresholds are **NO DATA FOUND**. Generalization
  is demonstrated for exactly one carrier.

### 2. Audit-defence documentation — the second act, brought forward
The engine already produces "which chart entry supports which claim, on what date, with what provenance."
That is an audit response packet with a different cover page.

- **VERIFIED (regulator):** RCDSO *Guidelines on Dental Recordkeeping* require records that are "accurate,
  comprehensive, legible and accessible," with entries "dated and signed, initialed or otherwise attributable
  to the treating clinician," retained **10 years after the last entry**. Inadequate records are professional
  misconduct. ([rcdso.org recordkeeping FAQ])
- **CLAIMED:** insurer audits of Canadian dentists rising sharply; one Ontario practice audited back to 2017,
  ending in delisting; KPMG Canada 2025 reports insurers scaling GenAI claims analytics.
- **Disconfirming signal:** **NO DATA FOUND** on RCDSO practice-assessment failure rates or insurer audit
  frequency — the entire size of this market is lawyer anecdote. Tailwind is real; magnitude is unmeasured.

### 3. CDCP enrolment-to-utilization gap — biggest number, weakest fit
**VERIFIED (canada.ca, data as of Aug 31 2026):** 4,764,250 enrolled for 2026-27; **900,606 accessed care
(18.9%)**. Cumulative since launch: 7,535,054 enrolled, 4,830,986 ever treated. 29,293 participating providers.

- Millions of funded patients are not converting to care. This is the largest unaddressed number in Canadian dental.
- **Disconfirming signal, and it is fatal for us:** nothing distinguishes "enrolled speculatively, no current
  need" from "wants care, blocked." No data source splits them. The payer would be government, on a
  government sales cycle, and this is patient-acquisition software — **zero reuse of our extraction engine.**

### 4. CDCP balance-billing / co-pay estimation — real, new, unowned
Dentists are not obliged to bill at the CDCP grid; the excess is balance-billed to patients who were told the
plan was free. Co-pay tiers are 0/40/60% by income band under $90K AFNI. A federally-created AR category that
did not exist before Dec 2023, with **no Canadian software found targeting it.**

- **Disconfirming signal:** magnitude is entirely **NO DATA FOUND** — no average gap per claim, no write-off
  rates. The Health Minister says the department is "monitoring how fees are applied," so the rules may move again.

### 5. Portable structured chart / records transfer — technically ours, commercially dead for now
**VERIFIED:** no province mandates a structured electronic format for transferring a dental record; RCDSO and
Saskatchewan's CDSS govern transfer by paper-form process. FHIR's Dental Data Exchange IG is US ADA/HL7-driven
with **no Canadian adoption found**. CDAnet remains claims-only.
- Our engine would be a genuine first mover. **But:** transfer volume, delay and complaint rates are all
  **NO DATA FOUND**, and the manual process satisfies the colleges today. No regulatory pressure, no buyer.

## What the evidence says to avoid

1. **A payer-side pivot.** `market.md` concluded "the money is on the payer side." **Canadian evidence
   contradicts that.** The Sun Life CDCP contract is **VERIFIED locked to Oct 29 2029** — CAD $746,698,598.22,
   70 months, contract CW2341316 ([canadabuys.canada.ca contract history]) — with no disclosed option period.
   **TELUS Health** already sells dental claims adjudication and AI fraud flagging to Canadian insurers and TPAs.
   **Green Shield** runs "Claim Watch" AI on dental claims **built in-house**. The payer layer is occupied by an
   incumbent with the distribution, not greenfield. Update `market.md` accordingly.
2. **No-shows, recall, missed calls, case acceptance.** Every circulating number (15–20% no-show,
   $105K–$240K/yr lost, 30–38% calls missed, 50–60% case acceptance) is **US vendor marketing with no named
   survey**. Canadian primary data: **NO DATA FOUND, all four.** And Dentrix, Weave, Solutionreach and
   RevenueWell already bundle recall into PM suites clinics own.
3. **Staffing marketplaces.** CDA reports a ~5,000 dental assistant shortfall and assistant-to-dentist ratios
   falling 3:1 to 1:1. **CDHA rejects the shortage framing outright** — its 2025 survey (n=3,003) shows 0.5%
   unemployment but attributes churn to retention: 60% report workplace mistreatment, 87% musculoskeletal
   issues. The two most authoritative Canadian bodies directly contradict each other. Not a software problem.
4. **Anything requiring us to transmit.** Unchanged. CDAnet Prohibited Practices.

## Open questions, ranked

1. **What share of the 54% of denials is documentation-recoverable vs clinically ineligible?** Health Canada
   has published no split. This is the business. Answer it with a governed Look-Back on real denial exports,
   not a survey — a clinic cannot tell you why it was denied.
2. **Predetermination thresholds and crown documentation checklists for Sun Life's private book, Canada Life,
   Green Shield, Desjardins, Beneva, Equitable.** Decides whether option 1 is one carrier or the market.
3. **RCDSO practice-assessment recordkeeping deficiency rate.** Decides whether option 2 has a market.
4. **Crown-specific preauth volume.** Health Canada publishes approval rate by category but not volume by
   category. We know crowns approve at 37%; we do not know how many crowns that is.
