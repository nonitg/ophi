# Ophi — AF Hacks: Growing Canada — pitch video script (v4)

Runtime 5:00 · 1920×1080 · narrator = ElevenLabs voice "David – Deep Documentary Narrator" (audition a),
sped up and steadied · founder segments = black screen, founders' own footage dropped in later.

Concept: **"A field guide to the Canadian preauthorization."** A nature-documentary narrator observes the
rarest creature in Canadian dentistry, then plays it straight: the problem, the product, what it's worth to
a clinic, how big it gets, and why the data makes it defensible. The vision is an evolutionary tree growing
from the tooth's roots. Theme: Canada already paid for the coverage; Ophi makes sure it buys treatment,
not paperwork.

Judging has no technical component, so the narration never explains the model. It says what the clinic
gets, how big the market is, and why the data is a moat.

Patient: **Teresa Kowalchuk, 64, fictional**. She is the app's in-chair demo case: a crown on #46. A "Demo
data · fictional patients" tag stays on screen through every product shot.

Format: `## start–end · title` sections, `[Visual]` directions, `> ` spoken lines. Check fit with
`scripts/script-timing.py docs/pitch/af-hacks-script.md --wpm 176` (the narrator runs about 176 wpm at the v4 speed).

---

## 0:00–0:13 · Cold open (narrator)

[Visual: letterboxed documentary frame on warm ivory paper. The 3D enamel tooth turns under a spotlight
like a museum specimen. A field-guide label types on: *Praeauctorizatio approbata · the approved
preauthorization · status: rare*. Faint clinic ambience: a phone, a printer, a distant drill.]

> Here, at the front desk of a Canadian dental clinic, we observe one of the rarest creatures in the country: the approved preauthorization.

[Visual: the tooth pulls back into a grid of 100 request cards. 46 light up, one by one, then stop.]

> Fewer than half make it.

[Footnote: 46% of complete CDCP preauthorization requests approved, Mar 1 – May 31, 2026 · Health Canada via
Oral Health Group]

## 0:13–0:32 · The patient (narrator)

[Visual: a paper ID card slides in: *Teresa, 64 · fictional*. A counter behind her rolls to 7,500,000.]

> Meet Teresa. Her dentist says she needs a crown. She's one of seven and a half million Canadians enrolled in the Canadian Dental Care Plan.

[Visual: a checklist draws itself, one item per beat: treatment plan · recent x-rays · full gum chart ·
proof the tooth meets the written criteria. A stamp hovers over it: *Sun Life review*.]

> But before the clinic can book it, Sun Life, which runs the plan, must approve a preauthorization: a treatment plan, recent x-rays, a full gum chart, and proof her tooth meets the written criteria.

[Footnote: 7,535,054 enrolled since launch, as of Aug 31, 2026 · canada.ca CDCP statistics]

## 0:32–1:04 · The problem (narrator)

[Visual: "$13 billion over five years" lands like a headline. Stat cards stack: "1.1M+ preauthorization
requests in the first benefit period" · "~1.9M a year at the spring 2026 pace" · "≈ 2 a week for the average
clinic".]

> Canada committed thirteen billion dollars to this plan, and preauthorization is where it stalls. Close to two million requests a year now. That's two a week for the average clinic.

[Visual: quote card, set in serif: *"The most common reasons for denials are incomplete submissions, such as
missing X-rays, insufficient evidence that the clinical criteria has been met…"* — Health Canada, to CBC,
May 2026.]

> Health Canada says the most common reason for a denial is an incomplete submission. The clinic only finds out after the patient has gone home. The fix goes to the back of the queue, and gets reviewed twice, on public money.

[Visual: a request card loops: sent → denied → back of the queue → sent again, as a clinic clock drains.
Then an X-ray sweep wipes to the wordmark **ophi.**]

> Ophi shows clinics what's missing while the patient is still in the chair.

## 1:04–2:17 · Demo (narrator, over the real app) — v4

[Visual: Ophi's board, full screen. Push in quickly to a readable scale, then glide across the columns: Needs
the patient · Paperwork · Dentist review · Ready to send · With Sun Life · Decision back. A tech label draws
in: *Practice software database · read-only · re-read within 15 s of a chart edit*.]

> Here, every CDCP request in the clinic gathers on one board, sorted by who acts next. Ophi reads each chart straight from the practice software's database.

[Visual: cursor opens *Before Teresa leaves · In the chair now*. Case page, "7 of 12 documented". Zoom on a
requirement row and its citation *Guide 6.3.5*. Label: *Rule engine · 14 requirements · 31 cited clauses*.]

> Teresa's still in the chair, and Ophi has already checked her chart against every requirement in CDCP's guide.

[Visual: the periapical row with the film-timeline card (34 months vs the 12-month window), then "4-point
chart on file".]

> Her x-ray of that tooth is almost three years old; CDCP wants one from the last year. Her gum chart is incomplete too.

[Visual: the fix plan, "Denial risk: Now High → After these fixes Medium". An AI chip: *✦ Risk model ·
gradient-boosted trees · trained on 720 past requests (simulated)*.]

> Ophi's risk model ranks the fixes by how much each one lowers the chance of a denial. The x-ray comes first.

[Visual: two quick *Mark taken* clicks, toasts, the card slides to Dentist review.]

> The hygienist pounces. Two captures before Teresa reaches the door.

[Visual: dentist view, "Laya pre-filled the other 7 from the chart and the note". AI chip: *✦ Laya · 421M-
parameter language model, fine-tuned on dental notes · runs in about 30 ms*. Zoom on the amber "4 of the 5
surfaces required" row.]

> Ophi's language model has read Dr. Lau's notes and pre-filled seven of nine criteria. If the tooth falls short, she can offer another plan today, not after a denial.

[Visual: the packet fans in, signature, "Send to Sun Life", "Mark as sent".]

> Ophi assembles the request, the dentist signs, and staff send it from the software they already use.

[Visual: With Sun Life. "Waiting on Sun Life · Sun Life processes most requests within 7 days". A monitor line
pulses between Ophi and the PMS: *Watching the claim status*. A second card flips to "Sent 8 days ago · Check
your CDAnet mailbox".]

> Then Ophi keeps watching. It checks the practice software for Sun Life's answer, and flags any request past the usual seven days.

[Visual: a letter drops in, "Read the letter". AI chip: *✦ Letter reader · reads Sun Life's words into one of
16 reasons*. "Ophi read Sun Life's reason as …", then the rule it points to. Split: approved, "Book the crown
by Sep 17, 2027"; denied, "Send a new request" / "Ask for reconsideration: by …".]

> When the letter arrives, Ophi's AI reads it, names Sun Life's reason, and sets the next step: book the crown before the approval expires, or fix and resubmit.

[Visual: "Crown booked for Thursday Oct 15", stamp.]

> The request is one step. The goal is Teresa's crown.

## 2:17–2:57 · What a clinic gets (narrator, motion graphics) — v4

[Visual: four pillars in turn, each with one number, then the ROI meter: $199/month against one $884 crown.]

> Why would a clinic pay? One: treatment that happens. A single CDCP crown is worth about eight hundred and eighty dollars to an Ontario clinic, and a complete request keeps that patient moving toward care.

> Two: hours back. No chart hunting, no retyping, no second visit. Three: rules that keep up. The guide changed twice in ten months; Ophi checks it every week.

[Visual: the Past denials page: "10 past denials were never resubmitted · $11,455 of crowns that haven't
happened", each row with Sun Life's words and "Draft what to say". Footnote: *demo clinic, fictional data*.]

> Four: money already on the table. Ophi finds past denials that were never resubmitted, and drafts the call to each patient. In this demo clinic, that's over eleven thousand dollars of crowns.

> At a hundred and ninety-nine dollars a month, one more crown every four months pays for it.

[Footnotes: Crown 27211, Ontario GP grid 2026, $884.15 before lab fee · Guide changes Dec 7, 2025 and Apr 1,
2026]

## 2:57–3:18 · The market (narrator)

[Visual: a dot map of Canada fills with clinics, counter rolling to 17,857. The math writes itself: 17,857
clinics × $199 × 12 = **$42.6M a year**. Two clusters pulse: dentalcorp ~630 · 123Dentist ~510.]

> Nearly every active dental provider in Canada now treats CDCP patients, across almost eighteen thousand clinics. At a hundred and ninety-nine dollars a month, that's a forty-three-million-dollar-a-year market for our first product alone. And groups like dentalcorp and 123Dentist can roll it out to over a thousand clinics at once.

## 3:18–4:24 · Vision, wedge and moat (narrator) — v4

[Visual: X-ray exposure sweep from the market map into the film look. The X-ray tooth. Then three stacked
layers light up under it, the platform: *Reads the chart* (practice-software database, read-only) · *Knows
every rule* (CDCP guide as code, clause by clause) · *Learns what the payer decides* (decisions as labelled
data). Three spokes (clinic · patient · payer) converge on one chart.]

> [warmly] And so, the species evolves. Why start with preauthorization? Because it's the one moment when the clinic, the patient and the payer all look at the same chart. To get it right, Ophi has to read the whole chart, know every rule, and learn what the payer decides. That's the foundation for everything else.

[Visual: the tooth's roots grow into the tree. Nodes light on their words with numbers: every CDCP
treatment → NIHB ($380M dental a year) → provincial plans → private insurers ($12.6B dental claims, 2024) →
every claim before it's sent → claims already paid (audits). The running tally grows.]

> The same engine grows into every CDCP treatment, then federal programs like NIHB, provincial plans, and private insurers, who paid twelve point six billion dollars in dental claims in 2024. Then every claim before it's sent, and every claim already paid, before an audit does.

[Visual: "What no one can copy". Public rules (guide page) vs private decisions (sealed envelope). Envelopes
from clinics flow into the core; chips: what was sent · what came back · why. The flywheel spins up.]

> Here's what no one can copy. The rules are public. The decisions aren't. Every request Ophi checks, and every answer that comes back, becomes a labelled example tied to the exact chart that was sent: a proprietary dataset that sharpens our models with every clinic.

[Visual: the moat ring locks; it morphs into the intelligence-layer band between Canada's clinics (17,857) and
the payers. Hold for 3 s.]

> That's our moat. It makes Ophi the intelligence layer between Canada's clinics and their payers, knowing what's missing before anything is sent.

## 4:24–4:59 · Team, traction, plan (FOUNDER CAM, black screen)

> **Nonit:** I'm Nonit Gupta. I've spent two years building health tech.
> **Jinay:** I'm Jinay Patel, our lead integration engineer. I build the low-level systems that read practice software directly, and I led software for a world-championship robotics team.
> **Nonit:** Two clinics have already booked demos. On Monday we start a ten-week field plan: free reviews of Ontario clinics' recent denials. By December, forty cases reviewed and two design partners signed.
> **Jinay:** And a clear test. If more than twenty percent of those denials could have been turned around, we build. Under eight percent, we rethink.

## 4:59–5:09 · Close (FOUNDER CAM, black screen)

> Canada already paid for the coverage. Ophi makes sure that money buys treatment, not paperwork, one clinic at a time.

## 4:52–5:00 · End card (no voice)

[Visual: Teresa's card stamps *Crown booked*. Wordmark **ophi.** · ophi.app · Nonit Gupta · Jinay Patel ·
AF Hacks: Growing Canada 2026. Sources in small type.]

---

## Sources (on-screen footnotes)

| On screen | Source |
|---|---|
| 46% of complete preauthorization requests approved (Mar 1 – May 31, 2026) | Health Canada via Oral Health Group, 2026-06-18 |
| 7,535,054 enrolled since launch (as of Aug 31, 2026) | canada.ca CDCP statistics |
| 1.1M+ preauthorization requests, first benefit period | Health Canada, CDCP Annual Report 2024–25 |
| ~1.9M a year (480,000 complete requests, Mar 1 – May 31, 2026, ×4) | Health Canada via Oral Health Group; annualized by us |
| ≈ 2 a week per clinic (1.9M ÷ 17,857 clinics ÷ 52) | derived |
| $13B over five years, $4.4B ongoing | Budget 2023, Department of Finance |
| "The most common reasons for denials are incomplete submissions…" | Health Canada spokesperson to CBC, 2026-05-27 |
| Crown 27211 ≈ $884 (Ontario GP, 2026, before lab fee) | Sun Life CDCP Ontario benefit grid 2026 |
| Guide changed Dec 7, 2025 and Apr 1, 2026 | CDCP Dental Benefits Guide, previous and current versions |
| "Close to 100% of active dentists … caring for patients covered under the CDCP" | Health Canada, 2026-04-17 |
| 17,857 dental clinics (employer establishments, NAICS 6212) | ISED Canadian Industry Statistics, 2025 |
| dentalcorp 650+ practices (≈630 in Canada); 123Dentist 510 clinics | dentalcorp 2026-07-21; 123Dentist clinic map |
| $12.6B dental claims paid by private insurers, 2024 | CLHIA Canadian Life and Health Insurance Facts, 2025 edition |
| $379.9M NIHB dental, 2023–24 | Indigenous Services Canada |
| Model results | Synthetic data only (docs/outcomes-explainer.md) |

## Changes in v3 (from the team's review)

- "Approved crown" is now "approved preauthorization", with the 46% overall figure instead of 37% for crowns.
  Crowns appear only as Teresa's treatment in the demo.
- "Why clinics pay" moved from founder cam to narrator plus motion graphics, as three reasons and an ROI meter,
  so the value shows on screen.
- Vision and moat grew to 45 s. The proprietary dataset of real decisions is stated plainly, with a flywheel.
- Model internals are cut from the narration, because judging is not technical.
- The team line is now filled: Nonit has two years in health tech. Jinay is the lead integration engineer, a
  low-level systems specialist, and led software for a world-championship robotics team.

## Changes in v4 (team review 2)

- Narration is 15% faster (stretch 1.25 → 1.44), which frees about 30 s.
- Vision now answers "why is preauthorization the wedge": the one moment clinic, patient and payer share a
  chart, which forces the three capabilities (read the chart, know every rule, learn what the payer decides)
  that every later product needs. Expansion is spelled out: every CDCP treatment → NIHB → provincial plans →
  private insurers → every claim → audits of paid claims.
- AI and proprietary parts are named on screen: the risk model, Laya (421M-parameter fine-tuned language
  model), the letter reader, the weekly rules watch, the rule engine (31 cited clauses), read-only database
  access, and the proprietary outcome dataset.
- New in the demo: follow-up monitoring after send, and the letter read into a named reason and next step.
- New value pillar: past denials never resubmitted, with a drafted call to each patient.
- Pass-2 fixes from docs/reviews/2026-09-27-pitch-video-v1.md go in with the rebuild.
