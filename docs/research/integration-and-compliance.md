# Integration & Compliance Research

Verified 2026-09-17. `[V]` = primary/vendor source. `[S]` = secondary only. `[U]` = UNVERIFIED.

## Three findings that change the plan

1. **ABELDent has no public API, SDK, developer portal, or published integration spec.** Every
   "ABELDent API" reference traces back to ABELDent marketing copy or third-party SEO pages. The
   product roadmap has no API line item. `[V]`
2. **ABELDent's published position is explicitly hostile to direct database integration** by third
   parties (exact quote below). Commercial/relationship risk, not a technical one. `[V]`
3. **Freemium almost certainly cannot send CDAnet attachments.** ABELDent scopes the feature to
   *"ABELDent Local Plus and ABELDent Cloud users, and to ABELDent LS version 14.8.2 users **with a
   current software maintenance agreement**."* Freemium explicitly excludes ongoing updates and
   support. Combined with CDAnet v2 retirement (claims rejected after 2026-03-31), an unmaintained
   Freemium install may not be a viable e-submission endpoint at all. `[V]`
   **Irrelevant to our MVP (we don't transmit) but decisive for any pilot clinic's submit path.**

## 1. ABELDent

**Vendor:** ABELDent Inc. / ABELSoft Inc., 3310 South Service Road, Burlington ON L7N 3M6.
800-267-ABEL (2235). `[V]`

| Product | Version | Data location | Client |
|---|---|---|---|
| ABELDent Cloud | v15 | Microsoft Azure | Installed Windows client — **not browser-based** |
| ABELDent Local Plus (fka LS+) | v15 | On-prem SQL Server | Installed Windows client |
| ABELDent LS / Local | v14.x | On-prem SQL Server | Installed Windows client |
| **ABELDent Freemium** | LOCAL platform | **SQL Server Express** | Installed Windows client |

v15 adds **ABELDent Scribe** (built-in AI clinical note generation) on Cloud + Local Plus. `[V]`
Note: they already ship AI in the chart. They may see a preauth copilot as partner or competitor.

### Freemium specifics
- Free, no credit card. *"looks and feels identical to our premium software."*
- **"MS SQL Server Express 2022 (or 2019) is the only database supported."** Windows 10/11 Pro or
  Home (Home = standalone only), 64-bit English only, .NET 4.7.2 or 3.5. Sized for **2–4
  workstations**. `[V]`
- SQL Express limits: **10 GB/database**, 1410 MB buffer pool, lesser of 1 socket / 4 cores. `[S]`
- Chargeable at regular rates: telephone support, one-on-one training, **ongoing software updates**,
  data migration, premium add-ons (R&A, Reputation Mgmt, Remote Backup, PCS). `[V]`
- No stated patient/record cap beyond the SQL Express ceiling. `[V]`
- **[U]** Whether Freemium can submit CDAnet e-claims/predeterminations at all.

### Database
- **Microsoft SQL Server.** Setup Conventions names SQL Server 2014/2016/2017/2019; older Access/JET
  databases still supported for existing customers. `[V]`
- **"ABELDent uses Windows authentication to authenticate with SQL Server."** `[V]`
- Ports: **MS SQL 1433 & 1434 TCP** (*"Do not open this port to the internet"*), ABELDent Portal
  1504 TCP, Office Communicator 1099 TCP, licensing 5093 UDP. `[V]`
- Install root `C:\ABELDent`; SQL backup path typically `C:\ABELDent\Data\Backup`. Installer modes
  Standalone / Server / Client. **Ships a "Fictional Data" sample dataset** — ideal for schema work
  with zero PHI. `[V]`
- **Schema documentation: none published.** `[V]` ABELDent's own KB has a "SQL Queries-Scripts"
  category (support-facing), confirming they operate directly on SQL, but no public data dictionary.
- **Indirect schema evidence** from Sikka's public ABELDent docs: entities **"Treatment ledger"**
  (fields *Provider*, *Responsible Provider*) and **"Financial ledger"**; ABELDent distinguishes
  "Summarized Totals" vs "Production Totals" report logic. `[V]`
- **ODBC is never mentioned in any ABELDent document.** Windows-auth-only SQL Server is the
  documented access model. `[V]`

### API / partner program
- **No developer documentation of any kind exists publicly.** `[V]`
- Partners page is a **reseller/MSP referral program** — commercial, not technical. `[V]`
- "Software Integration" service page is **imaging-only**, with a phone number for unlisted products. `[V]`
- *"ABELDent's commitment to secure API access enables you to use select third-party solutions
  safely"* appears in a Feb-2026 blog post — marketing copy, no spec, portal, or terms. `[V]`
- **Product roadmap has no API / partner-program / FHIR / interoperability item.** Only "integration
  with additional third-party [imaging] solutions during 2026." `[V]`
- Third-party claims to distrust: **crmbridge.ai** claims a "unified HIPAA-compliant REST API" over
  ABELDent — uses US HIPAA framing for a Canadian PMS, no evidence of an ABELDent relationship.
  **resonateapp.com** claims "ABELDent v15+ required for full API compatibility." Both `[U]`.

### Named integrations
- **Imaging (~30+ vendors, all via the launch bridge):** Adstra, AIS/Acteon SoPro, Air Techniques
  DBSWIN, Apixia, Apteryx XV, CADI/Synca, CaptureLink, Carestream KDIS, CliniView, Dexis, DTX Studio,
  EasyDent, Evasoft, Gendex VixWin, Planmeca DIMAXIS, Schick CDR, Sidexis, Soredex Digora, Trophy,
  DICOM systems, **Florida Probe** (perio). `[V]`
- **AI:** **Diagnocat** — the only named third-party AI integration (radiograph/CBCT analysis,
  automated perio charting from imaging, *"transfer of data generated and reviewed into your
  ABELDent odontogram (coming soon)"*). **Proof that a bespoke partner path exists informally.** `[V]`
- **Claims:** CDA **ITRANS** (via Continovation Services Inc.); **Dentaide (Quebec)** via the
  ACDQ-CDA Common Communication Driver (`CCD.ini`, Datapac dial-up — legacy). `[V]`
- **Analytics:** ABELDent R&A + **Microsoft Power BI** — strongly implies a supported read path into
  SQL, but `[U]` whether that is documented ODBC/SQL, a semantic model, or a hosted service. **R&A is
  a paid add-on NOT included in Freemium.**

### Imaging bridge mechanism — the real extension point
Workflow: patient -> **Imaging tab -> right-click -> Setup Integration** -> select vendor from a
**hard-coded list** -> Enable -> browse to the vendor's `.exe` -> restart ABELDent. `[V]`
Artifacts: **`ABELSoft.ImagingIntegrations.dll`** and **`C:\ABELDent\integrationsettings.ini`**.
Some bridges need the imaging app running in background. UAC must be off.
Patient handoff format (from Acteon setup): **`Type 2000: Number 'Name' 'First name' 'BirthDate'`**.

**Implication:** outbound **launch-with-context** from a **closed vendor list**. Gives patient
identity, not chart/treatment-plan/perio data. We cannot self-register. Not a viable primary data
path, but it is the template for how ABELDent thinks about partners (they add you to the DLL).

### File / export formats
**No HL7, no CDA, no FHIR, no documented CSV export API.** `[V]` Available: R&A custom reports +
Power BI; patient list builders over "hundreds of ABELDent data elements"; Document Manager;
print-to-PDF of forms/pre-treatment estimates.

### Useful KB articles
`KA-01025` Installing ITRANS - `KA-01063` Update EDI info for an insurance carrier -
`KA-01099` List of EDI Error Codes - `KA-01217` Canadian CCD & ICA Error Codes -
`KA-01141` **Sending Predetermination and Treatment Plans Electronically** (requires SQL v12.10+) -
`KA-01032` SQL Maintenance Plan - `KA-01064` Startup Utilities - `KA-01010` OS/SQL support matrix.
KB portal: https://abelsoft.microsoftcrmportals.com/knowledgebase/

### Stance on direct DB access — the exact quote
> *"Integrations developed by the dental practice management software vendor with the full
> cooperation of the third-party software vendor are your safest bet... **Unauthorized integrations
> created solely be third-party application vendors that directly read and update information in the
> dental practice management software's database may present a privacy and security risk to your
> data.** The dental practice management software vendor will likely not want to take responsibility
> for any data breach that may result and may advise users of these types of applications to use them
> at their own risk. These integrations are also vulnerable to breaking anytime the practice
> management software is updated to a new version."*
> — abeldent.com blog, 2020-01-22 `[V]`

ABELDent's Patient Privacy Policy: *"ABELDent acts as a service provider or agent of the customer,
and thus only indirectly collects patient information."* Contact `privacy@abelsoft.com`. Does not
name PIPEDA/PHIPA specifically. `[V]`

**[U]** Whether the EULA contains an explicit clause prohibiting third-party DB reads.
**Get a copy of the installed EULA — it is on the machine, 5-minute task.**

## 2. PMS integration patterns

| Pattern | How | Who | Fit for ABELDent |
|---|---|---|---|
| **Local agent -> direct DB read** | Windows service on practice server, reads SQL/file DB, pushes normalized data to vendor cloud | Sikka, most analytics vendors, most Canadian AI vendors | **Best technical fit.** SQL Express + Windows auth on the same box |
| **Vendor bridge executable** | PMS launches your `.exe` with patient context | ABELDent imaging bridges, Apteryx NameGrabber | Context only; closed list |
| **File drop / watched folder** | Write a file to a directory, a service picks it up | **ITRANS 2.0 ICD** (`\\Server\ICD\`) | Directly relevant for claim submission |
| **Cloud API** | REST, vendor-hosted | Open Dental, Dentrix/Ascend, CareStack, Curve, ClearDent | N/A for ABELDent |
| **Screen scraping / RPA** | Drive the Windows client UI | AI receptionists on closed PMSes | Viable fallback; brittle |
| **Aggregator** | Buy one API over N PMSes | Sikka ONE API | Viable; see cost |

### Sikka — the only realistic aggregator for ABELDent
- Practice installs the **Sikka Platform Utility (SPU)**, *"strongly recommend[ed]"* directly on the
  PMS server, requires Windows Administrator. Auto-detects the PMS, uploads to Sikka's cloud on a
  schedule (**default 2:00 AM local**, down to 15 min depending on licence). **The API reads Sikka's
  cloud copy, not the practice DB.** `[V]`
- **ABELDent explicitly supported.** Sikka documents ABELDent v9 (File -> System Status -> working
  directory) and **v10–14** (SPC -> Settings -> Data Path -> select SQL Server Instance). Also
  documents **Tracker** (`Settings.Config` -> `ServerName`) and **ClearDent**
  (`Cleardent.exe.config` -> `Cleardent.SQLConnection` -> `data source` + `initial catalog`). `[V]`
- Coverage: 400+ PMSes / 200+ dental; US, Canada, Australia; 100+ endpoints across patients,
  appointments, treatment plans, procedure codes, insurance accounts, claim details,
  **imaging/X-rays (Gold/Platinum tiers only)**, payments. `[V]`
- **Pricing (published Jul 2026):** **$350/mo standard licence** + per-location tier Silver $35 /
  Gold $45 / Platinum $175 / Payments $125. **All read-only; writeback quote-only and extra.**
  Support packages $250 each. Realistic floor **$385+/mo before writeback.** `[V]/[S]`
- **Gaps:**
  - `[U]` **ABELDent v15 / Cloud / Freemium support.** Docs stop at v14; Cloud has no local DB.
  - `[U]` Whether Sikka exposes **perio charting, clinical notes and radiograph pixel data** at
    preauth fidelity.
  - **Data residency: Sikka's cloud is US-based; their FAQ makes no HIPAA/SOC 2 claim and no mention
    of Canadian practices.** Material compliance problem — they become our sub-processor. `[V]`
  - Nightly default refresh too stale for an in-appointment copilot.
- **Do first:** one email asking (a) v15/Cloud/Freemium support, (b) perio/notes/imaging endpoint
  coverage, (c) data residency and SOC 2 status.

### Others
- **Dental Intelligence** — local-server agent; Analytics syncs nightly, Engagement near-real-time.
  No ABELDent evidence. `[V]`
- **Practice by Numbers** — Dentrix, Ascend, Eaglesoft, Open Dental, Practice-Web. **No ABELDent, no
  Canadian PMSes.** `[V]`
- **Zuub** — API-first, "Portal + EDI", native Open Dental. **US payers only (280+).** `[V]`
- **Onederful** — acquired by Vyne Nov 2021. US dental payer APIs, 240+ payers, X12. **No CDAnet.** `[V]`
- **Vyne FastAttach** — 750+ US dental plans. **No Canadian/CDAnet evidence.** `[U]`
- **DentalXChange** — US clearinghouse, **XConnect** gateway with a dedicated Attachment API. **No
  CDAnet.** `[V]`
- **Open Dental** — public REST API, fully public manual, **best open reference implementation of
  CDAnet in Canada.** `[V]`
- **Henry Schein One API Exchange** — Dentrix / Ascend, open to authorized vendors. `[V]`

**Conclusion: there is no universal aggregator we can simply buy that covers ABELDent AND handles
Canadian claims/attachments.** Sikka covers the read side for v9–14 only, with US residency.
Onederful/Vyne/DentalXChange are US-rail (X12) and irrelevant to CDAnet.

## 3. CDAnet / ITRANS

CDAnet is *"the agreement between the dental profession and the insurance carriers on the format in
which the information normally found on dental claims will be forwarded to the respective carrier
electronically."* Standards jointly set by **CDA, ACDQ, CLHIA**. Transport via **CDA ITRANS Claim
Service** or **CCDWS**; networks include TELUS Health, instream, Alberta Blue Cross. `[V]`

**Versions:** v2 retired Feb 2024; **v2 claims rejected after 2026-03-31.** All carriers on **v4**.
**Attachments require v4.1.** v4 adds Billing Provider Number, electronic COB, attachments,
predetermination transactions. `[V]`

### Transaction types `[S]`
The authoritative list is in the CDAnet Messaging Standard, which is **not public**. Verify under NDA.

| Code | Transaction | | Code | Transaction |
|---|---|---|---|---|
| 01 | Claim | | 11 | Claim Acknowledgement |
| 02 | Claim Reversal (same-day only) | | 13 | Predetermination Acknowledgement |
| **03** | **Predetermination / Pre-treatment Plan** | | 14 | ROT Response |
| 04 | Request for Outstanding Transaction | | **19** | **Attachment Response** |
| 07 | COB Claim | | 21 | Claim EOB |
| 08 | Eligibility | | 23 | Predetermination EOB |
| **09** | **Attachment** | | | |

**Predetermination behaviour (primary source):** *"Pretreatment plans are **always batch processed**.
A message will be displayed on your computer screen advising you that the pretreatment plan was
received successfully. The claims processor's approval or denial of the pretreatment plan will be
sent by mail to the insured."* Real-time pre-treatment EOBs possible where the carrier supports it.
**Claim limit: 1–7 procedures per claim**; more requires a second claim. `[V]`

### Who may transmit — the hard legal constraint
CDAnet Dental Office User Guide, **Prohibited Practices**: `[V]`
- *"**Use of non-certified software to submit claims and predeterminations through CDAnet.**"*
- *"**Only the treating dentist can send the claim.**"*
- *"A dentist cannot send a claim for services provided by another dentist..."*
- *"Attempts to access services other than those described in this User Guide."*
- Failure to comply *"will result in termination of services provided by the networks."*

**Reading:** a third party cannot act as a service bureau transmitting under a dentist's UIN. A
copilot may *assemble* the packet, and may be the certified software the dentist operates, but the
**dentist must be the sender of record.** Whether CDA permits a vendor-hosted certified product
acting under dentist credentials: `[U]` — ask CDA directly.

### Certification
Per-product against the CDAnet messaging standard. CDA *"does not test or endorse products beyond
their ability to send claims electronically."* **~40 certified vendors; ABELDent Inc. is certified
with the "(CDAnet attachments)" designation.** Others with attachments: Adstra, Akitu One, Tracker,
ExcelDent, Consult-PRO, Domtrak, Power Practice, axiUm, Gold, Dentrix, Dentally, Quadra, Paradigm,
MaxiDent, Dentonovo, Open Dental, DentalWare, Oryx, ClearDent, Progident/Clinique, Dentitek, AD2000,
Autopia. `[V]`
Contacts: `cdanet@cda-adc.ca` (vendor/certification), `pss@cda-adc.ca`, **1-866-788-1212**
(Mon–Fri 07:30–20:00 ET). **No public certification process doc, test harness, or fee schedule.** `[V]`

### ITRANS 2.0
- **ICD = ITRANS Claims Director**, successor to the ICA. Current **v4.1.0+**. Windows/macOS/Linux. `[V]`
- ICD *"removes the personal information of the patient and the plan member"* and determines routing
  **before** transmission — **de-identification happens at the edge, on the practice machine.** `[V]`
- **N-CPL (Network–Claims Processor List):** a **JSON** file regularly downloaded to auto-configure
  carriers, listing per carrier the networks, claims processor, **supported CDAnet message types**,
  and paper-claim mailing addresses. Schema in Appendix A of the Vendor Technical Reference. `[S]`
- **Authentication: CDA Digital ID** certificates, issued per office, from https://services.cda-adc.ca.
  MFA now mandatory on PSS. `[V]`
- **The concrete integration hook** (from Open Dental's public implementation): ICD installs as a
  Windows service at `C:\Program Files (x86)\CDA\ICD\` with a shared working folder at `C:\ICD\`; the
  PMS sets its claim export path to **`\\ServerName\ICD\`**; ICD watches the folder, transmits, and
  returns EOBs. **It is a file-drop interface.** `[V]`
- ITRANS 1 retires **2026-06-30**. `[S]`
- **Vendor docs — all 404 as of 2026-09-17 (indexed but not retrievable). Request from
  `cdanet@cda-adc.ca`:** `ITRANS_2.0_Vendor_Technical_Reference_1.5.pdf` (ICD v4.1, ~Apr 2025),
  `..._1.4.pdf`, `ITRANS_2.0_Vendor_Getting_Started_1.4.pdf`, `ErrorCodes-ICD-ICA-CCDWS-CDAnet.pdf`.

### Carriers
**Sun Life Financial: carrier ID `000016`, CDAnet Version 4.** `[S]`
**CDCP plan number `3333333`** per CDAnet news `[S]` — but Sun Life's own March 2026 CSI PDF says
**`333333`** (6 digits). CDA news also states "Policy numbers must be exactly 6 digits."
**Resolve before building validation.**
Other IDs: Canada Life `000011`, Desjardins `000051`, GreenShield `000102`, Alberta Blue Cross
`000090`, Beneva/SSQ `000079`, Beneva/La Capitale `600502`, TELUS AdjudiCare `000034`. `[S]`
**Cost: no additional fee for members.** Eligibility: licensed dentist in good standing with a
provincial/territorial association, or CDA Affiliate Member (Quebec). `[V]`

## 4. Attachments

### CDAnet Attachment spec (primary source) `[V]`
- *"Attachments may now be sent with **Version 4.1 only**; these attachments may consist of XRAYS or
  other oral images, or documents describing treatment plans or other pertinent information."*
- *"The Attachment message is an **optional** message for application software. A vendor does not need
  to support this message type... Any supporting material for a claim needs to be **physically
  mailed** if the carrier or the application software does not support this message type."*
- **Black & white:** *"XRAYS and other black and white images must be scanned in **8 or 16 Bit
  Greyscale at a resolution between 150 DPI and 300 DPI inclusive**."*
- **Colour:** *"Intra-oral and other images, pictures, must be scanned in **16, 24 or 32 bit Colour at
  a resolution between 300 DPI and 600 DPI inclusive**."*
- **Documents:** *"must be submitted in **ASCII text or Microsoft Word** formats."*

### Practical limits
**Up to 30 files per attachment message; 7 MB total combined.** Accepted in practice: **TXT, DOC,
DOCX, JPG, PNG, PDF, TIF.** Carriers may impose stricter limits. Harmful extensions auto-stripped,
removals noted in the message report. **Perio charts are a first-class attachment source** — Open
Dental can attach an existing perio chart directly. `[V]`

### Submission sequence
1. Submit predetermination (**03**)
2. Receive Acknowledgement (**13**)
3. Submit Attachment message (**09**) — carries the **predetermination message ID**, which the
   carrier uses to link the two
4. Receive Attachment Response (**19**)

**Sun Life/CDA requirement: attachment messages supporting preauthorizations must be submitted the
same day.** Carrier must have "Attachment" in its Supported Transaction Types. `[S]/[V]`

**Carriers accepting CDAnet attachments:** Alberta Blue Cross, Beneva, Canada Life, Desjardins,
TELUS AdjudiCare, AGA Financial, Quikcard, **Sun Life**. `[V]`

**Alternatives:** Vyne FastAttach in Canada — no evidence `[U]`. Sun Life portal upload for preauth —
not a documented channel `[V]`. **Mail fallback** is the documented non-EDI channel.

## 5. Sun Life

**Sun Life Direct** self-serve portal: participation sign-up, provider/facility linking, direct
deposit, claim and preauthorization status, EOBs. Requires **Access ID + password obtained by phone**
from the CDCP Contact Centre, **1-888-888-8110**. `[S]`
**No public API. No documented bulk upload. No published automation/scraping policy.** `[U]`

**Do not conflate with Sun Life U.S.** The 837/270/271/**278 prior auth**/835 X12 transaction set
belongs to Sun Life's **US** dental business and does **not** apply in Canada. Canada runs CDAnet. `[V]`

**CDCP preauthorization:** electronic preauth accepted since **2024-11-01** for Schedule B services
via CDAnet EDI including attachments. *"If your PMS does not support the submission of attachments
through EDI, you should submit your preauthorization requests and all supporting documentation by
mail only."* `[S]`

## 6. Standards

- **CDA USC&LS** is the Canadian dental procedure code set. **Licensed, not open:** *"intended for the
  sole use of the Corporate Members of the Canadian Dental Association and other organizations having
  signed the USC&LS Licensing Agreement only."* Contact **`uscls@cda-adc.ca`**. **We need this licence
  before shipping anything that stores or displays the code set.** Provincial fee guides separately
  licensed. CDHA maintains a parallel hygiene code list. `[S]`
- **HL7 FHIR Dental Data Exchange IG** — US Realm, **v2.0.0-ballot April 2025**, FHIR R4. Profiles
  dental referrals/consultation notes/conditions using Condition/Procedure/Observation/ServiceRequest,
  coded with **SNODENT**, on ANS/ADA Spec No. 1084. **Assessment: US-realm, ballot-stage, models
  medical<->dental referral, NOT claims/preauth. No Canadian PMS emits or consumes it. Zero
  interoperability benefit today.** Value is as vocabulary for an internal canonical model — cheap to
  borrow, wrong to depend on. `[S]`
- **DICOM:** dental radiography is fragmented; sensor vendors write proprietary formats, PMS-side
  integration is a launch bridge not a data standard. ABELDent Direct Capture Imaging uses **TWAIN**.
  **CDAnet does not accept DICOM** — any DICOM must be rendered to a compliant raster. `[V]`
- **Clinical notes:** free text / templated text inside the PMS database. No structured export
  standard. Regulatory baseline in Ontario: **RCDSO Dental Recordkeeping Guidelines** — records must
  be *"accurate, comprehensive, legible and accessible,"* dated and attributable to the treating
  clinician. Inadequate records = professional misconduct. `[S]`

## 7. Canadian privacy & compliance

### Who is who
- **The dental clinic / dentist is the Health Information Custodian** (Ontario PHIPA) / custodian
  (Alberta HIA) / an "organization" under BC PIPA & PIPEDA.
- **We are** an **agent** of the custodian (PHIPA s.17), an **electronic service provider (ESP)**
  (PHIPA, O. Reg. 329/04), an **Information Manager** (Alberta HIA s.66), or a **service
  provider/processor** (PIPEDA, BC PIPA, Quebec Law 25).
- **PHIPA ESP rules (O. Reg. 329/04):** where the ESP is *not* an agent, it must **not use** PHI
  except as necessary to provide the service, **must not disclose** it, and must not permit employees
  to access it unless they agree to the same restrictions. `[S]`
- **Alberta HIA:** an **Information Manager Agreement (IMA) is a statutory requirement** before a
  custodian may retain us. The IM must comply with HIA and have a security policy addressing
  privacy/security/confidentiality risks. Amended by Health Statutes Amendment Act 2025 (No. 2)
  (Bill 11), Royal Assent 2025-12-11, not yet fully proclaimed. `[S]`
- **ABELDent positions itself identically** — "service provider or agent of the customer" — so this is
  the familiar, accepted posture in this market. `[V]`

### Data residency
| Jurisdiction | Requirement |
|---|---|
| **PIPEDA** | No residency requirement. Accountability follows the data. |
| **Ontario PHIPA** | **Does not prohibit** storage/processing outside Ontario or Canada, but the custodian remains accountable and must exercise due diligence, transparency, contractual control. |
| **Alberta HIA** | No absolute prohibition; IMA + security policy required. |
| **BC PIPA** (private clinics) | No absolute prohibition; strong **procurement preference** for Canadian hosting. |
| **Quebec Law 25 (PPIPSA s.17)** | **PIA mandatory before communicating personal information outside Quebec** — including to another Canadian province. Must assess the receiving jurisdiction and, for US transfers, account for the CLOUD Act, FISA s.702, EO 12333. Written agreement required. In force since Sept 2023. |

### Breach notification
- **PIPEDA:** report to the OPC + notify individuals when a breach creates a **"real risk of
  significant harm" (RRSH)**, *"as soon as feasible"*; keep a breach record 24 months. OPC released an
  RRSH assessment tool 2025-03-26. **The OPC does not accept "it was our vendor's fault" as a defence
  for the customer-facing organization.** `[S]`
- **PHIPA:** as vendor/agent, notify the **custodian at the first reasonable opportunity**; the
  custodian handles patient and IPC notification.
- **Practical contract term:** clinics want a defined notification SLA (commonly 24–72h).

### LLM APIs and PHI
- **Nothing in Canadian law categorically prohibits it.** PHIPA/PIPEDA permit cross-border processing
  subject to accountability, due diligence, contractual controls, transparency. **Quebec is the
  exception: PIA required first.** `[S]`
- **Closest regulatory precedent, directly on point: Alberta OIPC AI Scribe PIA Guidance (September
  2025)** — https://oipc.ab.ca/wp-content/uploads/2025/09/AI-Scribe-PIA-Guidance-Sept-2025.pdf
  **Read before designing the pipeline.**
- **Standard mitigations Canadian health buyers expect:** Canadian-region or geo-pinned inference;
  contractual **no-training-on-customer-data**; **zero data retention**; de-identification/
  minimization before the model call; tamper-evident prompt/output logging; documented PIA; DPA naming
  the model provider as an approved sub-processor.
- **PHIPA's de-identification bar is high** — *"reasonably foreseeable... could be utilized, either
  alone or with other information, to identify the individual."* Stripping names from a radiograph +
  treatment plan + DOB is **not** de-identification.
- **Bill C-27 (CPPA + AIDA) died on the Order Paper January 2025.** No federal AI statute in force.

### Model hosting — Canadian regions
| Option | Canada residency | Notes |
|---|---|---|
| **Anthropic first-party API** | **No** | `inference_geo` supports only `"us"` and `"global"`; workspace geo supports only `"us"`. `[V]` |
| **AWS Bedrock ca-central-1** | **Partial** | Claude served via **Geo (`ca.anthropic.*`)** and **Global (`global.anthropic.*`)** cross-region profiles. **In-region-only inference not offered** for current Claude models — Geo keeps data in the US/Canada geography, not Canada alone. `[S]` |
| **Google Vertex (montreal/toronto)** | Partial | Listed by Anthropic as a Canada-residency path. `[S]` |
| **Microsoft Foundry / Azure** | Partial | Anthropic models in Foundry run on **Anthropic-hosted infrastructure, not Azure regional infrastructure**; only geo control is a **US Data Zone Standard** deployment. Azure itself has **Canada Central (Toronto)** and **Canada East (Québec City)**. `[V]` |

**Anthropic certifications:** SOC 2 Type 2 (Security, Availability, Confidentiality), ISO/IEC 27001 /
27017 / 27018, CSA STAR, HIPAA compliance with a DPA; **by default no training on commercial customer
data.** `[V]`

**Net: true Canada-only inference for Claude is not available today.** The defensible position is
geo-pinned (US/Canada) inference + ZDR + no-training + minimization + a documented PIA, **with
Canadian residency for storage at rest** (Azure Canada Central / AWS ca-central-1), which we fully
control.

## 8. Security expectations

**SOC 2 Type 2 is becoming table stakes.** Dental buyers and DSOs ask for the report, not a
self-attestation. Comparables holding it: Planet DDS, SOTA Cloud, Dentrix Ascend. **ABELDent Cloud
displays a SOC 2 Type 2 badge** (badge only, no report or auditor named — `[U]`).

What a Canadian clinic / DSO / their MSP will ask for:
1. SOC 2 Type 2 report (or ISO 27001 + roadmap if pre-SOC 2)
2. Signed **DPA / PHIPA agent–ESP addendum**; Alberta **IMA**; Quebec **PIA + written agreement**
3. **Data residency** statement + sub-processor list (incl. the LLM provider)
4. **Encryption** at rest (AES-256) and in transit (TLS 1.2+) — ABELDent calls out TLS 1.2 as the
   ICA/ITRANS floor
5. **Audit logging** of every PHI access, immutable, exportable to the custodian
6. **MFA + RBAC + least privilege** — CDA has made MFA mandatory on PSS and warns against shared accounts
7. Breach notification SLA to the custodian + incident response plan
8. Retention & deletion schedule; data-portability/exit plan
9. Penetration test summary + vulnerability management
10. Cyber liability insurance certificate

**Do not import US framing.** "HIPAA-compliant" on a Canadian dental product is a credibility tell.
Use PIPEDA/PHIPA/HIA/PIPA/Law 25 language.

## 9. Integration options ranked by time-to-first-value

**Assumption for all: the read side and the submit side are separable.** We can win on
read/assembly long before we can submit electronically.

| # | Option | TTFV | Effort | Key unknown |
|---|---|---|---|---|
| **1** | **Local read-only agent reading SQL Server Express directly** | 2–4 weeks to a working read | ~4–8 eng-weeks to production | **Whether ABELDent's EULA prohibits it and how they react commercially.** Also: schema stability across versions; whether clinical notes / perio / odontogram are relational or blobs |
| **2** | **Buy Sikka ONE API** | 2–6 weeks | ~1–3 eng-weeks + **$385+/mo** | (a) v15/Cloud/Freemium support — docs stop at v14; (b) whether perio, notes and radiograph images are exposed at preauth fidelity. Plus **US-hosted cloud, no SOC 2/HIPAA claim** becomes our sub-processor |
| **3** | **Assemble the packet; let ABELDent transmit** | Day one of #1 or #2 | ~0 engineering | Whether the clinic's install can send CDAnet attachments at all. **This is the correct MVP submit path — sidesteps certification entirely** |
| **4** | **Official ABELDent partner path** | 4–12 weeks to even know if it exists | BD, not engineering | Whether any programmatic interface exists behind the marketing language, and whether ABELDent (now shipping its own AI Scribe + Diagnocat) sees us as partner or competitor. **Free option value; converts #1's biggest risk into an asset. Do in parallel.** |
| **5** | **Report/export-driven (R&A, Power BI, print-to-file)** | 1–2 weeks | ~2–3 eng-weeks + permanent human friction | **R&A is a paid add-on Freemium lacks.** If Power BI turns out to use documented ODBC/SQL, this becomes a *sanctioned* version of #1 and jumps to the top |
| **6** | **UI automation / RPA against the Windows client** | 1–3 weeks for a narrow slice | 3–6 eng-weeks + continuous maintenance | Breakage across versions/resolutions (ABELDent specifies 1920x1080). **Only option that works across Freemium, Local Plus AND Cloud** — all are installed Windows clients. Bridge, not foundation |
| **7** | **Register as an imaging-bridge target** | Gated on #4 | Small once approved | Gives **patient identity only.** Vendor list hard-coded in the DLL |
| **8** | **Become CDAnet-certified ourselves** | 6–12+ months | Large | Whether CDA permits a vendor-hosted certified product under dentist credentials; cost and process; obtaining the vendor docs (all 404 today). **Only needed to own transmission — and Prohibited Practices means the dentist is still the sender, so it buys control, not a new business model** |

## 10. Compliance — must-have vs can-wait

### Must-have before the first real patient record touches our system
1. **Written agreement with the pilot clinic naming us agent / electronic service provider** under
   PHIPA (or IMA in AB, PIPA service provider in BC). Statutory prerequisite; in Alberta the IMA is a
   hard legal requirement before we may receive health information at all.
2. **DPA with sub-processor list** — cloud, model provider, any aggregator. First vendor-review
   question; also the artifact ABELDent will demand if this escalates.
3. **Confirm the ABELDent EULA position** (read the pilot clinic's installed copy). Determines whether
   option 1 is viable. **Zero cost. Do it this week.**
4. **Data minimization at the edge** — pull only the fields the CDCP matrix requires; don't bulk-mirror
   the practice DB. Both a PHIPA requirement and the strongest answer to "what if you get breached."
5. **No-training + zero-data-retention on the LLM path, contractually.**
6. **Geo-pinned inference + Canadian data residency at rest.** Be honest that in-region-only Claude
   inference isn't available yet.
7. **Encryption in transit (TLS 1.2+) and at rest (AES-256)**, including the local agent's cache.
8. **Immutable audit log of every PHI access and every model call** (who, what record, what prompt,
   what output, when). The Alberta OIPC AI Scribe guidance calls for exactly this.
9. **MFA + RBAC on our console; read-only DB credentials on the agent.**
10. **Breach notification commitment to the custodian** with a concrete SLA + named privacy contact.
11. **USC&LS licence enquiry to `uscls@cda-adc.ca`.** Paperwork lead-time, not engineering. Start early.
12. **Quebec: PIA before any Quebec clinic onboards.** Law 25 s.17 makes it a condition precedent.
    **Simply don't sell into Quebec until it exists.**

### Can wait (but date them)
| Item | When |
|---|---|
| **SOC 2 Type 2** | Start readiness/Type 1 at ~5–10 clinics; need Type 2 before the first DSO deal. **Design controls now so the audit is cheap later.** |
| ISO 27001 | Only for enterprise/DSO or government-adjacent buyers. SOC 2 is the North American dental default |
| External penetration test | Before the first paying multi-location customer |
| Cyber liability insurance | Before the first paid contract; not before the pilot |
| CDAnet vendor certification | Only when we decide to own transmission. Not an MVP item |
| FHIR / SNODENT conformance | Borrow the vocabulary now; conformance has zero buyer value in Canada today |
| Alberta IMA, BC PIPA specifics, provincial college guidance | Per-province as we expand. Ontario PHIPA first |
| Full de-identification before LLM calls | Start with minimization + contractual controls; invest when a buyer's PIA demands it |
| Data portability / exit tooling | Promise contractually at MVP; build before renewal season |

## 11. Immediate verification list (highest information per hour)

1. **Read the EULA** on our own Freemium install (installer -> "View Terms and Conditions", or the
   ABELDent folder). 5 minutes.
2. **Email `cdanet@cda-adc.ca`** — current ITRANS 2.0 vendor docs + certification process + whether a
   third party may transmit under dentist credentials. All three published PDF links are dead.
3. **Email `uscls@cda-adc.ca`** — start the USC&LS licence.
4. **Email Sikka** — ABELDent v15/Cloud/Freemium support, perio/notes/imaging endpoint coverage, data
   residency, SOC 2.
5. **Call ABELDent, 800-267-ABEL press 1** — what does a non-imaging integration partner path look
   like. Free option value; de-risks option 1.
6. **Ask any pilot clinic three questions:** which ABELDent version, whether "CDAnet Attachments"
   appears in their claims UI, and whether they can submit e-claims at all today. **That single answer
   determines whether their submit path is EDI or mail.**
