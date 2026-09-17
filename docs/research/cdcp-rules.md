# CDCP Preauthorization — Rules Reference

Verified 2026-09-17 against primary sources. This is the product specification.
Claims marked UNVERIFIED are not confirmed against a primary source — do not encode them.

## 0. Authority precedence (encode this ordering)

canada.ca states it explicitly: *"If there are discrepancies between this chart and the Guide,
the policies in the Guide prevail."* Health Canada's April 2026 factsheet adds:
*"The CDCP Benefit Grids remain the definitive source"* for codes.

1. **CDCP Dental Benefit Grids** (province x provider-type x year) — which codes exist, fees, Schedule A/B, inline frequency
2. **CDCP Dental Benefits Guide** — clinical criteria, policies, documentation
3. Supporting-documentation chart — summary only
4. Sun Life FAQ / newsletters — operational detail

## 1. Program status (Aug 31 2026 official statistics)

| Metric | Value |
|---|---|
| Enrolled, 2026-27 benefit period | 4,764,250 |
| Cumulative unique enrolled | 7,535,054 |
| Cumulative members who used coverage | 4,830,986 |
| Participating providers | 29,293 (25,409 dentists/specialists, 2,212 denturists, 1,675 hygienists) |
| Largest provinces 2026-27 | ON 1,962,231 / QC 1,356,742 / BC 612,584 |

Rollout complete (final phase May 2025). Benefit period 2026-27 = **Jul 1 2026 – Jun 30 2027**.

Roles: **Health Canada** owns policy + adjudicates exception requests. **Sun Life** is claims
processor only (~$750M contract, awarded Dec 2023, 5-yr operations; preauth + paper claims added
Nov 1 2024). **ESDC/Service Canada** handles enrolment. **CRA** supplies adjusted family net income.

Eligibility (all four): no access to dental insurance; filed tax return; **adjusted family net
income < $90,000**; Canadian resident for tax purposes.

Co-pay tiers — share **of the CDCP established fee**, not the dentist's fee:

| AFNI | CDCP pays | Patient co-pay |
|---|---|---|
| < $70,000 | 100% | 0% |
| $70,000–79,999 | 60% | 40% |
| $80,000–89,999 | 40% | 60% |

## 2. What requires preauthorization

Two orthogonal triggers:
- **Always-preauth** — code sits in Schedule B (GPSP/OMFS/DH grids) or is flagged **P** / **I.C.**
  (Independent Consideration) on denturist grids.
- **Above-frequency** — any Schedule A service beyond its frequency limit.

### Schedule B, Ontario GPSP 2026 (241 codes)

| Category | Codes | Notes |
|---|---|---|
| Specialist exam – complete | 01401, 01501, 01701, 01801 | 1/60mo per specialty, referral + justification |
| Diagnostic casts, unmounted | 04911, 04913 | |
| Interproximal disking | 16201 | 1 unit/12mo |
| Cores & posts | 21301, 21302, 23601, 23602, 25751–25756, 25761–25766 | 4/120mo/client; permanent; 18+; core only if existing restoration >24mo old; **only alongside approved crown preauth** |
| Crowns | 27201, 27211, 27301 | 4/120mo/client; 1/96mo/tooth |
| Crown removal | 29301 | |
| **RCT (conditional)** | 33111, 33121, 33131, 33141 | Appear in **BOTH** Schedule A and B. *"Preauthorization is required for teeth ending in 8 at all times."* |
| RCT re-treatment | 33115, 33125, 33135, 33145 | 1/tooth/lifetime |
| Apicoectomy | 33601–33605, 33611–33614, 33621–33624, 34111–34164 | 1/tooth/lifetime |
| Retrofilling | 34211–34264 | 1/tooth/lifetime |
| **Desensitization** | 41301, 41302 | **NEW Apr 1 2026**; 2 units/12mo |
| Perio splint/ligation | 43211, 43221, 43231, 43241, 43281 | |
| Perio re-evaluation | 49101, 49102 | Only for identified perio problem; not with 01502 |
| Complete overdentures | 51711–51713 | 1/arch/96mo |
| Complete immediate overdentures | 51811–51813 | 1/arch/lifetime, combined with immediate/provisional |
| Partial acrylic – provisional | 52101–52103, 52121–52123 | 1/arch/60mo; **initial placement only** |
| Partial acrylic | 52111–52113, 52201–52203, 52301–52313, 52401–52403, 52711–52713 | 1/arch/60mo; initial only |
| Partial cast | 53101–53103, 53201–53203, 53301–53302, 53711–53713 | 1/arch/96mo; initial only |
| Oral surgery (subset) | 72321, 72329, 72331, 72339, 72511, 72519, 72521, 72529, 72531, 72539, 72541, 72551, 73121, 73411, 75302, 75401, 75403, 75411, 75412, 76201, 76301, 79603, 79604 | |
| Orthodontics (NOT claimable) | P0500, P1200, P1300, P1400; 80602, 80661, 80669, 80671, 80679, 81111–81254 | Header: "CAN BE REQUESTED AT A DATE TO BE DETERMINED" |
| Parenteral conscious sedation | 92441–92448 | 1 session/12mo |
| Combined inhalation + IV/IM | 92451–92458 | 1 session/12mo |
| GA – facilities | 92222–92228 | 1/12mo |
| **GA – delivery w/o facilities** | 92232–92238 | **New 2026** (replaces 92212–92218) |
| Deep sedation – facilities | 92321–92328 | 1/12mo |
| **Deep sedation – delivery w/o facilities** | 92331–92338 | **New 2026** (replaces 92301–92308) |
| Office/institutional visit | 94301, 94302 | 94301 new to Sched B in 2026 |
| Laboratory fees | 99111, 99112, 99113 | All I.C. |

### Provider-type dependence — a real trap

**Oral and maxillofacial surgeons do NOT need preauth for sedation/GA.** OMFS 2026 grid puts
nitrous, oral sedation, parenteral conscious sedation and combined techniques in **Schedule A**;
its Schedule B contains only 94301, 94302, 99113. The OMFS grid has **no Prevention, Restoration,
Prosthodontics or Orthodontics sections at all** — those codes don't exist for that provider type.

### What does NOT require preauth

Standard RCT on anteriors/bicuspids/1st+2nd molars (only **third molars / teeth ending in 8**
need it); complete dentures standard; transitional/provisional; **complete immediate dentures
(changed Apr 1 2026)**; denture repairs/additions; relines/rebases; tissue conditioning;
adjustments; prefabricated posts without a core; partial denture *replacements* where CDCP paid
the initial placement and frequency is met; nitrous/oral/combined sedation (4 sessions/12mo);
emergency exams; caries/trauma/pain control; pulpotomy/pulpectomy; open and drain; fillings;
most extractions; SRP within frequency.

### Exclusions — never covered, never reconsiderable (Guide App. E)

veneers (composite or ceramic) - all 3/4 crowns - restorations for incisal wear involving enamel
and dentin - cosmetic treatment incl. whitening - inlays/onlays in composite, precious metal or
ceramic - TMJ therapy and appliances - **fixed prosthodontics (bridges and all bridge-related)** -
periodontal appliances incl. night guards - mouth guards - crown lengthening - **implants and all
implant-related procedures** - bone grafts - extensive rehabilitation - precision attachment
partial dentures - fluorescent diagnostic light

Implant-supported crowns, complete and partial dentures are exclusions, **not eligible for
reconsideration**. **Orthodontics: "currently not available"** (Guide 6.8, eff. Apr 1 2026).

Exception-request pathway exists for out-of-scope services that are *not* exclusions; adjudicated
by Health Canada; *"expected to be extremely rare."*

## 3. Documentation requirements

Official matrix, updated **2026-01-26**:

| CDCP service | Claim form | Tx plan | PA+BW (R&L) <=12mo | Complete perio chart <=12mo | Missing teeth / pano | Planned extractions | Referral + justification | Rationale |
|---|---|---|---|---|---|---|---|---|
| Specialist examinations | Yes | – | – | – | – | – | **Yes** | – |
| Restorative services | Yes | Yes(1) | **Yes** | Yes, **crowns only**(7) | – | – | – | – |
| Endodontic services | Yes | Yes(1) | Yes(3,4) | Yes(7) | – | – | – | **Yes** |
| Additional units SRP | Yes | – | – | Yes(6) | – | – | – | – |
| Removable complete dentures | Yes | Yes(1) | – | – | **Yes** | Yes, if any | – | **Yes** |
| Removable partial dentures | Yes | Yes(1) | Yes(5) | – | **Yes** | Yes, if any | – | – |
| Oral surgery services | Yes | Yes(1) | Yes(3) | – | – | – | – | **Yes** |
| Sedation services | Yes | Yes(2) | – | – | – | – | – | **Yes** |

Footnotes (verbatim, load-bearing):

1. Treatment plan details indicating all relevant completed and pending treatment needs, or, based
   on scope of practice, confirmation that potential basic treatment needs are being referred
   and/or will be addressed. **Does not need to be a stand-alone document labelled "treatment
   plan" so long as the information is included in the documentation submitted.**
2. Planned/proposed treatment to be completed during the sedation session.
3. Dated panoramic considered when it is not possible to obtain intraoral radiographs, **as
   indicated in a rationale**.
4. Dated **periapical only**.
5. ONE OF: dated PA of abutment teeth + dated BW (<=12mo); OR if PA/BW not possible, most recent
   dated pano; OR if radiographs unavailable: dated photos of upper and lower arches (2, separate),
   OR dated photos of stone models (2, separate), OR dated stone models (upper and lower).
6. If a complete perio chart cannot be provided, a rationale is required explaining why it is
   incomplete and providing relevant information not captured.
7. If a complete perio chart is not available, a dated **PSR for each sextant plus 6-site
   periodontal measurements for each tooth requested, within last 12 months**, will be considered.
   **PSR 4 in any sextant, OR PSR 3 in two or more sextants -> complete perio chart must be
   submitted. PSR 3 in the sextant of the requested tooth -> charting of that sextant must be
   submitted.**

### Accepted request forms

CDA/CLHIA Standard Dental Claim Form; ACDQ Dental Claim and Treatment Plan Form; CDHA National
Dental Hygiene Claim Form; DAC Dental Care Claim Form; **computer-generated treatment form**.
Form eligibility varies by service — restorative and endodontic accept only CDA/CLHIA, ACDQ and
computer-generated; denture sections accept CDA/CLHIA, ACDQ, DAC, computer-generated.

### Radiograph standards (Guide 6.1.2)

Must be **current, dated, of diagnostic quality**. *"Intraoral radiographs are considered 'current'
for preauthorization purposes if dated within the last 12 months of the preauthorization
submission."* Mailed film: dated, mounted, **both provider and client name on the mount**;
duplicates must indicate right vs left. Enlarged digital: providers *"requested to print a
measurement scale when possible."*

### Clinical criteria that drive approve/deny

**Crowns (6.3.5)** — preauth, 18+, and ALL of:
- Tooth eligibility: incisors, canines, bicuspids, 1st and 2nd molars; third molars **only** where
  1st and 2nd are missing and the 3rd is in occlusion with a prosthetic or natural molar.
- Restorability: absence of active periodontal disease; **crown-to-root ratio <= 1:1**; **absence
  of furcation involvement**; restoration margin **3 mm from alveolar crest**; **adequate ferrule
  (1.5 mm)**; mesio-distal space equivalent to natural tooth; no crown lengthening, root
  resectioning or orthodontics required.
- "Extensively restored": anteriors — loss involves entire incisal edge mesial-to-distal and
  extends cervically to both interproximal contacts; **endodontically treated** premolars/molars —
  >=3 continuous surfaces involving both marginal ridges or entire cusp destruction;
  **non-endodontically treated** premolars/molars — **5 continuous surfaces**.
- *"All basic treatment addressing any existing active biological disease (caries and periodontal)
  must be completed before submitting requests for crowns."*
- *"An endodontically treated tooth must have healed before requesting a crown."*
- Explicit non-coverage: aesthetics; stress fractures/chipping on minimally restored teeth; high
  caries risk or generalized moderate-to-severe perio disease with long-standing/uncontrolled/
  untreated rampant disease; solely to treat sensitivity from cracked tooth syndrome, erosion,
  abrasion or attrition.

**Endodontics (6.4.2)** — same tooth-eligibility and restorability criteria as crowns minus the
ferrule requirement; same rampant-disease exclusion.

**Partial dentures (6.6.2.3)** — teeth 16–26 and 36–46 inclusive; all basic treatment completed;
space >= corresponding natural teeth; existing CDCP-paid partial cast >=96mo / acrylic >=60mo.
Specific: **>=1 missing tooth in the anterior sextant, OR >=2 missing posterior teeth in a quadrant
excluding 2nd and 3rd molars.** Critical: *"The CDCP will not consider a client's existing partial
denture (obtained outside of the CDCP)"* — a new client with a non-CDCP partial is still an
**initial placement** (preauth required).

**Sedation (6.9)** — nitrous/oral: ages 0–11 where treatment cannot be rendered without sedation;
12+ where treatment was attempted and unsuccessful, or cannot be attempted due to significant
mental and/or physical impairment (rationale). Parenteral/deep/GA: complex or extensive treatment
needs, or age-related behaviour management (0–11) / significant impairment (all ages), in a
rationale. *"The CDCP does not define 'significant mental and/or physical impairment'."*

**SRP above limit (6.5.1.1)** — severity of perio disease from current (<=12mo) clinical notes,
diagnosis and prognosis, complete perio charting and radiographs; plus medical condition relative
to perio disease including prescribed medication.

### Partial-documentation policy (repeated in every service section)

*"the CDCP may consider preauthorization submissions where only some, but not all, required
documentation is provided... Where a submission does not sufficiently demonstrate the eligibility
criteria are met, additional information may be requested and/or the submission will be denied."*

## 4. Submission, turnaround, response

| Channel | Detail |
|---|---|
| **EDI (CDAnet/ITRANS)** | Preferred. Requires **UIN** from CDA/DAC/CDHA/ACDQ. **CDCP plan number `333333`** (see discrepancy #1). Must be submitted **"Assigned."** Attachments: **up to 30 files, 7 MB combined**; attachment message **same day** as the predetermination. |
| **Mail** | Sun Life Assurance Company of Canada, CDCP, PO Box 99865 STND, Montreal QC H3C 0E6. *"Submissions by mail will require additional time."* |
| **Courier** (postal disruption) | Sun Life, CDCP Claims, 1155 Rue Metcalfe, Suite 1024, Montreal QC H3B 2V6 |
| **Sun Life Direct portal** | **NOT a preauth submission channel.** Coverage look-up, EOB retrieval, EFT setup, history. Access ID by calling 1-888-888-8110. |

**Hard rule:** if the PMS cannot send attachments via EDI, Sun Life instructs providers to submit
*"by mail only"* — not EDI-then-mail.

**Who can submit:** the oral health provider only. Clients cannot submit or be reimbursed. For
specialist exams, either the specialist or the referring provider may submit. Supporting docs may
originate from another provider.

**Cross-specialty portability:** an approved, still-valid preauth under one specialty does NOT need
restarting if another specialty performs the same treatment — Sun Life pays using the equivalent
code and that provider type's grid. Only a *different* treatment plan needs a new preauth.

**Turnaround — no published SLA.** Health Canada reported **>95% processed within 7 days, majority
under 5 days** as of May 31 2026 (up from >80% in July 2025). The widely-circulated 25–30 business
day figures are UNVERIFIED secondary-blog estimates.

**Processing order: first-come, first-processed. Every resubmission is treated as a brand-new
request at the back of the queue** — including resubmissions caused by Sun Life's own
"missing documentation" denial. This is the economic core of the product.

**Response:** EOB via Sun Life Direct or mail. Not sent to members. Preauths do not appear in
Sun Life Direct until processed.

**Response codes:** only **N05** is publicly documented (*"This expense is not covered under your
benefits plan"*). **No public catalogue of CDCP EOB/denial reason codes exists — UNVERIFIED and a
significant gap.**

**Validity:** most decisions valid **12 months**; **24 months** for some preventive and periodontal
services. Conditional on the client still being eligible on the date of service.

**Post-determination (5.4):** adjudicated after service, for procedures that normally need preauth.
*"Intended to be used rarely, and only in emergent clinical situations."* Requires the full preauth
document set **plus a rationale explaining why post-determination is sought.**

**Reconsideration (App. C):** within **60 days** of denial; submitted by the provider at the
client's request; **must include additional or new clinical information**; **one level only**,
final; reviewed by a different adjudicator; **exclusions never eligible.**

**Payment:** EFT within ~2 business days of processing; ~90% of claims process immediately. Claims
must be received within **12 months of date of service**, inclusive of all resubmissions.

## 5. Procedure code systems

Five underlying sets (Guide 2.0): **CDA USC&LS** (dentists/specialists), **ACDQ** (QC general),
**FDSQ** (QC specialists), **DAC** (denturists), **CDHA** (hygienists).

**USC&LS is licensed, not open.** *"intended for the sole use of the Corporate Members of the
Canadian Dental Association (CDA) and other organizations having signed the USC&LS Licensing
Agreement only."* Licensing via `uscls@cda-adc.ca`. **Real procurement dependency — start early.**

**Code sets are not interchangeable.** Same service, different codes per association:

| Service | CDA | ACDQ | FDSQ | DAC | CDHA |
|---|---|---|---|---|---|
| Desensitization | 41301, 41302 | 41306, 41307 | 41305 | – | 00641, 00642, 00647 |
| Complete immediate dentures | 51301–51303, 51611–51613 | 51300, 51310, 51320 | 51305, 51315, 51325 | 31311, 31321, 31511, 31521 | – |
| Denture liners | 51104, 56601 | – | 56226 | 73008, 32318, 32328, 42318, 42328, 32510, 32520, 42516, 42526 | – |
| PA radiographs 7 & 8 images | – | – | – | – | 00227, 00228 |

**CDCP fees are independent of provincial fee guides.** Grid fees are **per-specialty columns**
(GP, Anest, Endo, O. Med, O. Path, Ortho, Paed, Perio, Pros, Radio) — crown 27201 is $884.15 (GP)
vs $1,060.98 (Pros) in Ontario 2026. `Lab` column "L" = variable commercial lab fee allowed;
`I.C.` = independent consideration. Dentists may bill their usual fees, creating balance bills.

## 6. Denial evidence

| Period | Metric |
|---|---|
| Nov 2024 – Jun 2025 | **49% of complex-care preauth denied** (Health Canada DG) / 52% (CBC) |
| Program start – Jul 2025 | Only **~1% of all CDCP claims required preauth** |
| **Mar 1 – May 31 2026** | **~480,000 complete requests, ~224,000 approved = ~46% approval** |
| As of May 31 2026 | **Crowns ~37% approved. Partial dentures >76%. Root canals requiring preauth ~44%.** |

**Crowns are the problem category.** Partial dentures are comparatively fine.

Official denial reasons — Health Canada spokesperson to CBC, May 27 2026: *"The most common reasons
for denials are incomplete submissions, such as missing X-rays, insufficient evidence that the
clinical criteria has been met, duplicate requests and requests for services not covered under the
program such as implants or bridges."*

Health Canada, July 2025 — most frequently missing: *"Radiographs, periodontal charting
information, and treatment plan details."*

Sun Life, Dec 2024 alert: *"most requests are being sent without the necessary attachments or
missing documentation."*

Field friction: an Ottawa dentist had all but one of dozens of crown predeterminations denied —
*"It's tremendously frustrating when we're receiving rejection after rejection after rejection
without any details or instructions, recommendations, action items as to why."* A BC dental
administrator: *"The periodontal part of the plan is woefully inadequate."*

**NOTE:** the 1%-of-claims figure vs 1.9M/yr processed requests implies roughly **8–10 preauth
transactions per underlying clinical case** — resubmission churn. This is the central thesis and is
DERIVED, not sourced. Validate it.

## 7. Frequency limits to encode

**All frequency limits are rolling, not calendar.** Guide 4.0 canonical example: recall rendered
Apr 1 2025 -> next eligible **Apr 2 2026**.

**Examinations** — max **3 in any 12 months** overall; specialist and denturist exams excluded from
that count.
- Complete oral: 1/60mo (replaces recall + new-patient-limited for the period)
- New patient limited: 1/12mo, in lieu of recall
- Recall: 1/12mo
- Specific: 1/12mo; **if performed with recall services -> treated as a recall exam**
- Emergency: **no frequency limit**; with recall services -> treated as recall
- First dental visit/orientation (<=3y): 1/lifetime
- Specialist complete: 1/60mo **per specialty** (preauth); Specialist limited: 1/12mo per specialty

**Radiographs**
- Intraoral 1–8 images (PA, BW, occlusal): **8 in any 12 months**
- Intraoral 12–16 complete series: 1/60mo
- Panoramic: 1/60mo, **max 3 per lifetime**

**Preventive** (by age band 0–11 / 12–16 / 17+)
- Polishing: 1/2 unit/12mo (all ages)
- Topical fluoride: 1/6mo (0–16), 1/12mo (17+)
- Topical antimicrobial/remineralization incl. SDF: 2/12mo
- Sealants/PRR: **<=17y only**; occlusal of permanent molars and bicuspids, lingual of permanent
  maxillary incisors, **unrestored surfaces only**; **third molars, permanent canines and
  mandibular incisors not eligible**; **lifetime limit 2 per eligible tooth**
- Interproximal disking: 1 unit/12mo (preauth); only mesial of 53/63/73/83, distal of 55/65/75/85

**Restorative**
- **Once per tooth surface in any 24 months** (as of Dec 2025 **no longer** qualified by
  same-provider/same-office)
- Primary incisors 51,52,61,62,71,72,81,82: client must be **under age 5**
- Caries/trauma/pain control: **not eligible** same date + same tooth as restorations, open & drain,
  pulpectomy, pulpotomy, or RCT
- Cores & posts: 4/120mo/client combined, permanent only, **18+**; core only if existing restoration
  >24mo old; core/post-with-core only alongside an approved crown preauth
- Post removal: 1/lifetime per permanent tooth
- Crowns: **4/120mo per client; 1/96mo per tooth**; 18+
- Repair to crowns 1/36mo/tooth; recementation 1/36mo/tooth

**Endodontics**
- RCT re-treatment, apicoectomy, retrofilling: **1 each per tooth per lifetime**
- Pulpectomy/pulpotomy: 1/tooth/lifetime; primary incisors only if <5y
- RCT payment absorbs pulpectomy/pulpotomy and open-and-drain performed within the **prior 3
  months** by the same provider/office, plus temporary restoration and its replacement

**Periodontics**
- Scaling: 1/2 unit/12mo (0–11), 1 unit/12mo (12–16), **4 units/12mo combined with root planing (17+)**
- Desensitization: 2 units/12mo — **preauth as of Apr 1 2026**
- Management of oral disease (two categories): 2 units/12mo each

**Dentures**
- Complete standard / overdentures / standard with long-term soft liner: **1/arch/96mo**
- Complete transitional-provisional / immediate / immediate overdentures: **1/arch/lifetime** (combined)
- Partial cast: 1/arch/96mo. Partial acrylic (all variants): 1/arch/60mo
- Repairs/additions 1/arch/12mo. Reline/rebase 1/arch/24mo. Tissue conditioning 1/arch/24mo
- **No new denture within 24 months of a reline or rebase** — *"This rule applies regardless of
  other denture frequency limits."* Example: relined Dec 15 2025 -> new denture not eligible until
  **Dec 16 2027**
- Sequencing: after transitional/provisional -> other denture types after **6 months**; after
  complete immediate -> other complete dentures after **96 months**; after partial immediate ->
  other partial acrylic after **60 months**, partial cast after **96 months**
- CDCP fee includes a **3-month post-insertion care period**
- **Insertion timing (new, Jun 2026):** provisional/transitional inserted **within 7 days of
  extractions**; immediate dentures **within 45 days**. **Date of service = date of insertion, not
  fabrication.** Failure can trigger payment recovery.
- Non-inserted: dentures up to **50%** of CDCP professional fee + R&C lab fee; **crowns up to 20%**
  — conditional on documented client-contact efforts and written notice to Sun Life

**Sedation**
- Nitrous / oral / nitrous+oral: **4 sessions/12mo**, no preauth
- Parenteral conscious and combined inhalation + IV/IM: **1 session/12mo**, preauth
- Deep sedation and GA: **1 session/12mo**, preauth
- Sedation must be rendered **in conjunction with at least one eligible CDCP procedure**

**Claims verification:** documentation requests answered within **21 calendar days**; records
retained **minimum 2 years** from claim submission; overpayments offset against future claims if
unpaid within 30 days. New post-payment verification started summer 2026 (mailed confirmation
letters to a sample of members and providers).

## 8. Parseable source artifacts

| Artifact | URL |
|---|---|
| **CDCP Dental Benefits Guide** (eff. Apr 1 2026) | https://www.canada.ca/en/services/benefits/dental/dental-care-plan/guide.html |
| Previous Guide (eff. Dec 7 2025) | https://www.canada.ca/en/services/benefits/dental/dental-care-plan/guide/previous-version.html |
| **Supporting documentation matrix** (PDF, 2026-01-26) | https://www.canada.ca/content/dam/canada/employment-social-development/services/benefits/dental/dental-care-plan/providers/cdcp-supporting-documentation-requirements-for-preauthorization-submissions-en.pdf |
| Preauthorization resources | https://www.canada.ca/en/services/benefits/dental/dental-care-plan/providers/preauthorization.html |
| Statistics (monthly HTML tables) | https://www.canada.ca/en/services/benefits/dental/dental-care-plan/statistics.html |
| **Dental Benefit Grids index** (147 PDFs) | https://www.sunlife.ca/sl/cdcp/en/provider/dental-benefit-grids/ |
| Claims Submission Information | https://www.sunlife.ca/content/dam/sunlife/regional/canada/documents/cxo/cdcp/cdcp-csi-en.pdf |
| Billing agreement / payment terms | https://www.sunlife.ca/sl/cdcp/en/provider/claims-processing-and-payment-terms/ |
| Claims verification program | https://www.sunlife.ca/sl/cdcp/en/provider/additional-resources/cdcp-claims-verification-program/ |
| **Provider newsletters — the real change log** | https://www.sunlife.ca/sl/cdcp/en/provider/newsletters/ |
| Health Canada Apr 2026 change factsheet | https://nsdental.org/wp-content/uploads/2026/02/Factsheet-on-CDCP-Guide-and-Grids-updates-April-2026.pdf |

**Grid URL pattern:**
`https://www.sunlife.ca/content/dam/sunlife/regional/canada/documents/cxo/cdcp/grids/cdcp-{prov}-{type}-benefit-grid-{year}-e.pdf`
`{prov}` in ab,bc,mb,nb,nl,ns,nt,nu,on,pe,qc,sk (+Yukon, naming UNVERIFIED);
`{type}` in gpsp,dd,dh,omfs. 46 live 2026 URLs confirmed. NT and NU have no `dh` grid. `-f` = French.

**Grid PDF structure** (GPSP/DH/OMFS): `Schedule A` then `Schedule B`, each split into
`SCHEDULE {A|B} - {0.0 DIAGNOSTIC | 1.0 PREVENTION | 2.0 RESTORATION | 3.0 ENDODONTICS |
4.0 PERIODONTICS | 5.0 PROSTHODONTICS - REMOVABLE | 7.0 ORAL AND MAXILLOFACIAL SURGERY |
8.0 ORTHODONTICS | 9.0 ADJUNCTIVE GENERAL SERVICES}`. Rows:
`Code | Lab | GP | Anest | Endo | O. Med | O. Path | Ortho | Paed | Perio | Pros | Radio`.
Frequency limits appear as bullet text above each code block.
**Denturist grids use a different layout entirely** —
`Code | Service | Fee | Commercial Laboratory Fee | In-house Laboratory Fee | Preauthorization`
with "P" flags.

**Access engineering note:** sunlife.ca is behind DataDome + Akamai. Plain HTTP fetchers get **403
on every URL including DAM PDFs.** A headless browser session (or cookie forwarding of `datadome`
+ `bm_sz`) is required; cookies rotate within minutes.

**Not publicly available:** CDA USC&LS master code list (licensed), CDCP EOB/denial reason code
catalogue, any preauthorization API.

## 9. What changed 2025–2026

### Dec 7 2025 (Guide; grids not updated until April)
- **Frequency limits: same-provider / same-office qualifiers removed.** "once per tooth surface in
  any 24-month period by the same provider or a different provider in the same office" ->
  **"once per tooth surface in any 24-month period."**
- New dentures not eligible within 24 months of a reline/rebase.
- **Documentation relief (CDA/PTDA advocacy):** treatment plan and radiographs no longer required
  for additional scaling units; **PSR accepted in lieu of a complete perio chart for crowns and
  endodontics**, score-dependent.
- Commercial lab fees: R&C amounts applied as of Oct 17 2025.

### Apr 1 2026 (Guide + all grids)
| Change | Direction | Codes (CDA) |
|---|---|---|
| Desensitization now requires preauth | A -> B | 41301, 41302 |
| Complete immediate dentures no longer require preauth | B -> A | 51301–51303 |
| Complete immediate overdentures — new preauth category | new in B | 51811–51813 |
| Denture liners without preauth | new in A | 51104, 56601 |
| Sedation codes realigned to 2025 USC&LS | swap within B | 92212–92218 -> **92232–92238**; 92301–92308 -> **92331–92338** |
| Lab fee codes replaced | — | 99222, 99333 -> **99112, 99113** |
| Office/institutional visit | new in B | 94301 |
| CDCP professional fees + commercial lab fee ceilings increased | — | all |

Net Schedule B for ON GPSP: 241 codes in both 2025 and 2026 (20 out, 20 in).

**Explicit no-grandfathering:** *"if these changes do affect an existing treatment plan, no
retroactive payments or legacy provisions will apply."* Pricing follows **date of service**, not
date of preauth approval.

**Orthodontics regressed.** Dec 2025 Guide had detailed criteria (Modified HLD Index for children
<18; adults with craniofacial anomaly). April 2026 Guide cut 6.8 to one sentence: *"Orthodontic
services are currently not available."* Grids still carry ortho codes with published fees. **Treat
orthodontics as not implementable.**

## 10. Known discrepancies — resolve before encoding

1. **Plan number.** Sun Life's March 2026 CSI PDF says **`333333`** (6 digits, stated twice). The
   CDAnet news archive (2024) says **`3333333`** (7 digits). Verify against a live EDI transaction.
2. **Immediate dentures.** canada.ca/coverage still reads *"complete immediate and overdentures
   (requires preauthorization)"*, contradicting the April 2026 Guide + factsheet. **Guide and Grids
   prevail.**
3. **Orthodontics.** Guide says "currently not available"; grids say "at a date to be determined"
   with live fees.
4. **Internal cross-reference errors in the Guide** (6.6.1 points to "6.5.4", etc.). Section
   numbering shifted between versions. **Do not key rules to section numbers.**
5. **Footnote 3 wording differs** between the PDF matrix ("intraoral radiographs") and the HTML page
   ("periapical or bitewing radiographs"). Guide 6.4.4/6.7.1 is the tiebreaker.
6. **No published turnaround SLA. No published EOB/denial reason code catalogue.**
7. **Yukon grid URL naming** not confirmed.

## 11. Encodable vs requires-a-human

### Deterministic — encode with high confidence
- **Exclusion check.** Closed list, App. E. Match -> not covered, not reconsiderable. Highest-value
  early exit; Health Canada names implants/bridges among top denial causes.
- **Schedule A vs B lookup** per (procedure code x province x provider type x service-date year).
- **Conditional preauth: RCT 33111/33121/33131/33141 require preauth iff tooth number ends in 8.**
- **Partial denture initial-vs-replacement.** Preauth unless the prior partial was CDCP-paid and
  frequency met. A pre-existing non-CDCP partial is ignored -> still initial placement.
- **Provider-type overrides.** OMFS -> sedation/GA in Schedule A. Denturist grids use P/I.C. flags
  and a different code set. Must be a first-class dimension.
- **Frequency arithmetic.** All rolling-window per-tooth/arch/surface/client/lifetime rules,
  including the 3-exams-per-12-months aggregate, exam-type substitution, specific/emergency-with-
  recall reclassification, the 24-month reline/rebase block, and denture sequencing waits.
- **Age gates.** Crowns/cores/posts 18+; sealants <=17; primary incisor restorations and pulpectomy <5.
- **Tooth eligibility for crowns and RCT**, incl. the third-molar-in-occlusion exception.
- **Sealant surface/tooth rules. Interproximal disking tooth list.**
- **Documentation completeness checklist** per service category — the matrix is a literal rule
  table. Includes radiograph recency and the substitution ladders (esp. the 3-tier partial-denture
  ladder: PA+BW -> pano -> photos/stone models).
- **PSR escalation logic** — fully algorithmic.
- **Sedation must accompany >=1 eligible CDCP procedure.**
- **Cores/posts-with-core only valid alongside an approved crown preauth.**
- **Temporal validity.** 12-month claim deadline; preauth validity 12mo (24 for select
  preventive/perio); grid-year selection by **date of service**; benefit-period boundary (Jul 1);
  an approved preauth is void if the client is not eligible on the day of care.
- **Code-set version guards.** 2025 sedation codes (92212–92218, 92301–92308) and lab codes
  (99222, 99333) are **invalid for 2026 dates of service.** A stale PMS code table is a silent
  denial generator — one of the highest-value deterministic checks available.
- **Submission-channel routing.** No EDI attachment support -> mail only. 30 files / 7 MB ceiling.
  Claim must be "Assigned."
- **Reconsideration eligibility.** Within 60 days; one level; requires NEW information; never for
  exclusions. Also: distinguishing a *resubmission* (missing docs, new queue position) from a
  *reconsideration* — providers evidently get this wrong.

### Requires a human (or human sign-off)
- **"Absence of active periodontal disease" / "all basic treatment completed."** Active vs arrested
  is a clinical determination. **This is the crux of most crown denials.**
- **"High risk of caries" / "generalized moderate to severe periodontal disease with evidence of
  long-standing, uncontrolled and/or untreated rampant biological disease."** No numeric threshold
  given anywhere. Pure adjudicator judgment.
- **Radiographic measurement extraction** — crown-to-root ratio, furcation, ferrule,
  margin-to-crest. Only computable from calibrated radiographs. The Guide asks providers to print a
  measurement scale *"to facilitate the assessment"*, implying Sun Life's own adjudicators struggle.
  Treat any automated measurement as a draft for clinician confirmation.
- **"Extensively restored" classification.** Surface counts are specified but mapping a restoration
  to "3+ continuous surfaces involving both marginal ridges" requires reading the radiograph.
- **Every free-text rationale.** Mandatory for endodontics, oral surgery, complete dentures,
  sedation, all post-determinations, all reconsiderations, pano-instead-of-intraoral justifications,
  and incomplete-perio-chart explanations. The system assembles evidence and drafts; **a clinician
  must own the clinical assertion.**
- **"Significant mental and/or physical impairment"** — the Guide states outright the CDCP does not
  define it.
- **"Emergent clinical situation"** for post-determination — *"The CDCP does not define emergency
  care. It is up to oral health providers to determine the urgency."*
- **Diagnostic-quality judgment on radiographs.**
- **Whether a submission will be approved.** With crowns at ~37%, the honest output is a gap list,
  not a prediction. **Do not imply the tool can guarantee approval.**

### Structural cautions
1. **Dimension the rule store as (code x province/territory x provider type x effective-date
   range).** All four demonstrably change behaviour. A single national table will be wrong.
2. **Grids are the code/schedule authority; the Guide is the policy authority; the summary chart is
   neither.** Encode that precedence.
3. **Version everything by date of service.** Explicit no-grandfathering.
4. **Archive the previous Guide version yourself** — canada.ca retains exactly one, overwritten on
   update.
5. **Denturist grids need a separate parser.**
6. **Eligibility is volatile within a benefit period.** Re-check coverage at date of service, not
   just at planning time. An approved preauth does not guarantee payment.
7. **Resubmission is expensive** — it re-enters the queue as a new request. The strongest defensible
   value is getting the first submission complete, which aligns exactly with the #1 denial reason.
8. **Preserve the evidence bundle** — 2-year retention, 21-day verification response window.
