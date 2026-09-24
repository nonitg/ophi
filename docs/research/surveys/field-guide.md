# Clinic workflow discovery study

This study is designed to answer two different questions:

1. **Is Ophi aimed at a frequent, consequential problem?**
2. **If so, does the proposed human-review workflow fit how clinics actually work?**

The first campus clinic is a **cognitive and qualitative pilot**, not market validation. Its value is
to correct language, expose missing workflow steps, compare the dentist's view with the administrator's
view, and earn permission for a recent-case walkthrough. Market-level conclusions require multiple
independent clinics.

## Recommended sequence

1. Ask one dentist and one administrator to complete their forms **separately**, without discussing
   answers first.
2. Watch them think aloud during this first run. Note every term, answer choice, or time period they
   interpret differently than intended.
3. Revise the forms. Treat these first responses as pretest data, not part of the main sample.
4. Hold a 30-minute recent-case interview with each role. If they agree, finish with a 15-minute joint
   debrief to reconcile differences in their process maps.
5. Run the revised administrator survey at 10 or more target clinics. Pair a dentist response at as
   many of those clinics as possible. Count a paired dentist and administrator as **one clinic**, not
   two independent observations.
6. Ask clinics with useful records for a governed Look-Back. A survey cannot establish whether a
   denial was documentation-recoverable.

## What the forms deliberately do

- Begin with an unaided question about avoidable work before naming predeterminations.
- Reconstruct the **most recent real case** rather than asking for general opinions.
- Separate active labour from elapsed insurer or patient waiting time.
- Separate unique patient/treatment-plan cases from submission attempts and resubmissions.
- Ask about a smooth case as well as an exception, so the study does not presume every workflow is
  broken.
- Measure frequency, effort, rework, and consequence separately.
- Present the Ophi concept only after current-state questions.
- Use concrete choices, including `None`, `Not sure`, and `Not part of my role`.
- End with an observable commitment, not a hypothetical "Would you buy this?"

## Hypotheses and evidence

| Hypothesis | Survey evidence | Stronger follow-up evidence | Disconfirming signal |
|---|---|---|---|
| Target clinics have enough CDCP work | Administrator's clinic-wide unique cases in the named month | PMS/CDAnet report | Median under 2 unique CDCP predeterminations/month across 10 target clinics |
| Published transaction volume reflects rework | Unique CDCP cases versus total submission attempts | Case-level submission log | Attempts are close to unique cases and resubmission is rare |
| Documentation gathering causes preventable work | Recent-case steps, systems, waits, corrections, dentist handoffs | Observe one case and inspect a de-identified process trace | Friction occurs mainly after a complete packet, in payer delay or clinical ineligibility |
| A negative or delayed determination can reduce care | Recent-case patient outcome | Look-Back and scheduled/completed treatment record | Patients usually proceed and cases rarely disappear |
| Administrator operates; dentist makes clinical judgments and signs | Paired ownership answers | Joint workflow map | Work is owned by a third party or roles do not match the proposed handoff |
| Evidence-linked review is trusted enough to test | Dentist safety requirement, both roles' strongest objection, next-step commitment | Review a fictional packet; shadow pilot | Neither role will inspect a case, share aggregate counts, or test in shadow mode |
| Predetermination is the best initial wedge | Unaided first answer and forced broad-workflow choice | Interviews across clinics | Another recurring workflow dominates both staff effort and patient impact |

Do not convert the table into one composite "validation score." Preserve contradictory evidence.

## Electronic implementation

Use the campus's Qualtrics account if available. It supports the branch, display, and answer-choice
randomization used here. Google Forms is a workable fallback using sections and shuffled answer
choices, but it is more cumbersome for conditional grids.

Create **two independent forms**, not one role selector:

- `How treatment planning becomes scheduled care — dentist`
- `How work moves through the dental office — administrator/coordinator`

Configuration:

- Use four blocks: `role and unaided discovery`, `recent case`, `concept`, `profile and follow-up`.
- Put 2–4 questions on a page. Avoid one very long matrix on mobile.
- Randomize unordered answer lists. Keep time ranges and other ordinal scales in order.
- Keep `Other`, `None`, `Not sure`, and `Not part of my role` fixed at the bottom.
- Use a non-identifying `clinic_code` embedded in each invitation link to pair responses.
- For the September 2026 launch, replace `[NAMED MONTH]` with **August 2026** everywhere. Always name
  the month; do not display the ambiguous phrase "last month."
- Do not collect IP address, login identity, or email with response data if anonymity is promised.
  For a known design partner, say **confidential**, not anonymous.
- Send follow-up opt-in to a separate contact form so identity is not stored with survey answers.
- Do not require optional open-text questions.
- Test every branch on a phone and desktop before launch.

Suggested invitation copy:

> We are studying how dental clinics move from a treatment decision through cost or coverage
> questions to scheduled care. We are interested in what actually happens, including processes that
> work well. This 6–8 minute questionnaire is research, not a test of your clinic. Please complete it
> independently and do not enter any patient names or identifying details. We will discuss a software
> concept only at the end.

## Privacy and research boundary

- Never request patient name, initials, date of birth, chart number, exact appointment date, image,
  or free-text clinical content.
- Ask respondents to describe a **process**, not a patient.
- State the purpose, estimated completion time, confidentiality treatment, and who will see results.
- Keep research follow-up distinct from a sales conversation. Obtain explicit permission before a
  pilot or commercial discussion.
- If a later Look-Back uses real clinic data, it needs its own privacy, access, minimization, and
  retention agreement; survey consent does not cover it.

## Analysis plan

Pre-register these fields before sending the revised survey:

- `unique_cdcp_cases_month`
- `unique_cdcp_crown_cases_month`
- `cdcp_submission_attempts_month`
- `attempts_per_unique_case = attempts / unique cases`
- recent-case active minutes, elapsed time, handoffs, dentist interruptions, and attempts
- recent-case outcome and whether treatment proceeded
- broad workflow named unaided
- broad workflow chosen for staff impact and patient impact
- current tracking method and current workaround
- strongest safety/adoption barrier
- strongest next-step commitment

Rules for interpretation:

- For fewer than 20 clinics, report counts, medians, ranges, and verbatim themes—not percentages with
  false precision.
- Keep `Don't know` visible. It often signals a tracking problem and must not be converted to zero.
- Separate answers based on a report from answers based on memory.
- Analyze target clinics separately from campus/teaching clinics, specialists, and clinics outside the
  launch province.
- Do not count a polite concept rating as validation. Give greater weight to a recent incident,
  observable workaround, aggregate-data access, scheduled observation, or pilot commitment.
- Do not infer documentation recoverability from a respondent's impression. Confirm it with a
  Look-Back.

### Why the first forms do not ask "Would you pay?"

An affirmative hypothetical answer is cheap and systematically overstates real purchase behavior. In
the interview, first establish current cost: verified case volume, active staff time, corrections,
delayed treatment, cases that do not proceed, and any software or outside-service spend. Once the team
can describe a real offer, test a concrete choice that includes the status quo—for example, keep the
current process, use a managed service, or begin a defined shadow pilot at a stated conversion price.
The best early commercial signal is accepting the work needed for that pilot and involving the actual
decision-maker, not selecting a price range in a survey.

The existing Ophi stop condition remains primary: if 10 target-clinic administrators report a
median of fewer than 2 unique CDCP predetermination cases in the named month, stop treating a
CDCP-crown-only product as a sufficient market.

### Decision rules after the first 10 target clinics

| Pattern in the evidence | Interpretation | Next action |
|---|---|---|
| Median is under 2 unique CDCP cases/month | CDCP crowns alone do not create enough work | Stop or broaden the payer/procedure wedge before more product work |
| Submission attempts greatly exceed unique cases, and corrections are documentation-related | Rework is real and the completeness wedge is plausible | Verify causes and recoverability with a Look-Back |
| Attempts are high, but work is mainly status checking or opaque payer responses | The problem exists, but packet completeness is not the main job | Test a cross-carrier status/exception workflow rather than force the current concept |
| Most negative cases met documentation requirements but failed clinical criteria | The product would organize a packet without changing the outcome | Reconsider the core value proposition; do not market completeness as revenue recovery |
| Another task appears unaided and wins both staff- and patient-impact choices | The adjacent workflow may be a better entry point | Run a second round centred on that task before changing scope |
| Both roles describe the same repeated handoff and accept a concrete next step | The workflow is understood well enough for a narrow prototype test | Test one fictional case, then a governed shadow pilot |
| Respondents like the concept but will not verify counts, inspect a case, or schedule follow-up | Stated interest has not become evidence | Treat as weak signal and continue discovery |

The campus/teaching clinic should not be included in a target-clinic median unless it genuinely matches
the intended customer on staffing, purchasing authority, payer mix, and case volume.

## Thirty-minute recent-case interview

Run this separately with the dentist and administrator before a joint debrief.

### 0–3 minutes: set the boundary

> We want to understand what happened, not evaluate how anyone performed. Please use a recent case,
> but do not show or say any patient identifiers. I may interrupt to ask what happened next or where
> information came from.

Ask permission to take notes. Do not record unless they separately consent.

### 3–12 minutes: reconstruct the timeline

> Start at the moment the treatment was proposed. What happened next?

For each step, ask:

- Who did it?
- What triggered it?
- Which system, screen, paper, inbox, or person supplied the information?
- What output or decision moved the case forward?
- How did the next person know it was their turn?
- Did the case leave the normal path? Why?

Do not introduce the expected Ophi workflow. Draw what they describe.

### 12–18 minutes: inspect the exception

- Where did someone search, wait, copy, re-enter, correct, or ask again?
- What did the dentist have to judge or phrase personally?
- Was the initial payer response actionable?
- Who owned the next action and where was it tracked?
- What happened to scheduling and to the patient?

### 18–22 minutes: contrast with a smooth case

> Think of a similar case that moved unusually smoothly. What was different?

Look for reliable documents, team experience, carrier behavior, system integration, a checklist, clear
ownership, or the case simply not requiring an exception.

### 22–27 minutes: concept test

Show one low-fidelity Ophi case, not a polished sales demo. Ask the participant to narrate what they
think each element means.

- What would you verify before trusting this flag?
- What is missing from your current decision?
- What must remain under human review?
- Where would this enter the current sequence?
- What existing step, if any, would disappear?
- What error would make the product unsafe or not worth using?

### 27–30 minutes: evidence and next step

- Which aggregate count could the clinic verify from a report?
- Who else must be involved in a workflow observation or pilot decision?
- Is the participant willing to review one fictional case, permit a no-PHI observation, share aggregate
  counts, or discuss a defined shadow pilot?

Record the commitment actually made, not a general expression of interest.

## Joint debrief

Show the dentist and administrator the two process maps without identifying one as correct. Ask them to
reconcile:

- where the case officially starts and ends;
- who owns the next action while waiting;
- how often the dentist is interrupted;
- how submission status returns;
- where clinical judgment is recorded;
- whether a negative or delayed case is resubmitted, changed, or lost;
- which single handoff they would change first.

Disagreement is a finding. Do not average it away.

## Research basis

- [Pew Research Center: Writing Survey Questions](https://www.pewresearch.org/writing-survey-questions/)
- [Pew Research Center: Forced-choice versus select-all formats](https://www.pewresearch.org/methods/2019/05/09/when-online-survey-respondents-only-select-some-that-apply/)
- [CDC: Cognitive interviewing](https://www.cdc.gov/nchs/ccqder/question-evaluation/cognitive-interviewing.html)
- [AHRQ: Critical Incident Technique](https://psnet.ahrq.gov/issue/critical-incident-technique)
- [AAPOR: Consent and confidentiality](https://aapor.org/standards-and-ethics/institutional-review-boards/)
- [AAPOR: Condemned survey practices](https://aapor.org/standards-and-ethics/condemned-survey-practices/)
- [Schmidt & Bijmolt: Accurately measuring willingness to pay](https://doi.org/10.1007/S11747-019-00666-6)
- [Health Canada: CDCP preauthorization resources](https://www.canada.ca/en/services/benefits/dental/dental-care-plan/providers/preauthorization.html)
- [CDA: Dental plans guide](https://www.cda-adc.ca/_files/oral_health/talk/For_Dentists_Dental_Plans_Dentist_Guide_EN_Print.pdf)
- [CDA: CDAnet/ITRANS FAQ](https://www.cda-adc.ca/for-dental-professionals/programs-amp-services/cdanet-and-itrans/faqs)
- [Qualtrics: Survey Flow](https://www.qualtrics.com/support/survey-platform/survey-module/survey-flow/survey-flow-overview/)
- [Qualtrics: Choice Randomization](https://www.qualtrics.com/support/survey-platform/survey-module/question-options/choice-randomization/)
