# How Ophi learns from past crown decisions

*A plain-language explainer of the outcomes-learning system, written for someone new to machine learning,
and good enough to present to an investor. The technical plan is
[plan/05-outcomes-learning.md](plan/05-outcomes-learning.md). Figures are from the 2026-09-26 run.*

**In one sentence:** Ophi checks each new crown request against Sun Life's written rules, uses two models
trained on past approvals and denials to estimate how likely it is to be denied and why, then tests each
possible fix to see which ones lower that risk most.

The most important fact to lead with: **every number below comes from synthetic data** (600 made-up
requests from our own generator). The system shows that the method works. It does not yet show how Sun
Life behaves. We need real decisions before any clinic relies on it.

---

## 1. What machine learning is

A normal program follows rules someone wrote: "if the X-ray is older than 12 months, flag it."

Machine learning works the other way. You show the program many examples with the answer attached, and it
works out the rules for itself.

- **Example:** one past crown request (films, perio chart, note, tooth, and so on).
- **Label:** what happened to it (approved, or denied for a given reason).
- **Model:** a formula with many adjustable numbers, called weights.
- **Training:** the model guesses the label, measures how wrong it was, and nudges its weights to be a
  bit less wrong. It repeats this thousands of times.
- **Testing:** you score it on examples it has **never seen**. That score is the only honest measure. A
  model can memorize its training data and still fail on new cases.

You can take accountability for a model when you can answer three questions: what data it learned from,
how it was tested, and what it is allowed to change.

---

## 2. The problem

- A crown under CDCP needs pre-approval from Sun Life. Only about 37% of crown requests are approved.
- Roughly 30% of denials are paperwork: a missing X-ray, a stale perio chart, a retired lab code. The
  rest are clinical, for example "the tooth isn't extensively restored" or "the root canal hasn't healed."
- Many denial letters don't say why ("does not meet the CDCP criteria").
- By law, Sun Life can only deny for reasons written in the CDCP guide, about 18 of them. We already
  encoded those in the **rule pack** (`packs/cdcp/2026-01-26/pack.yaml`).

---

## 3. The system has four parts

```
note text ──► Laya (reads the note) ──► 7 yes/no answers ─┐
                                                         ├─► LightGBM ──► denial risk + what's driving it
chart, dates, codes, rule-pack checks ───────────────────┘
                                                                  │
                                                                  ▼
                                                   Fixer: "what if we fixed X?" → ranked fixes
```

### Part 1: the rule pack (no ML)
- This is the written rules, turned into code. If the bitewings are missing, that is a fact, not a guess.
- It has the final say on what the requirements are. **No model output changes a requirement or a
  verdict.** Every fix Ophi suggests cites a clause in the pack.
- Its limit: three criteria can only be judged from the free-text note: extensively restored,
  restorable, and endo healed. On all 630 requests, the rules came back "can't tell" on those three. That
  gap is Laya's job.

### Part 2: Laya (reads the note)
- **What it is:** an open-source language model from Convai Innovations (Apache 2.0 licence, 421 million
  weights, built on ModernBERT). It doesn't write text. It reads text and answers multiple-choice
  questions with probabilities.
- **How it reads:** it turns the note into numbers that capture meaning. For example, "MODB composite,
  fractured" ends up close to "large restoration, structure lost."
- **Pre-trained vs fine-tuned:** out of the box, Laya has general reading skill but knows nothing about
  CDCP. Untrained, it scores *below* a simple guess. **Fine-tuning** means we keep training it on our own
  examples so it gets good at our specific questions.
- **What we taught it** (`ophi/outcomes/laya_questions.py`):
  - 7 yes/no questions about the note. Examples: "Has the tooth lost a cusp?", "Is the root canal
    recent?", "Is fillings or scaling still pending?", "Is the margin below the gum?"
  - 1 multiple-choice question: "What will Sun Life decide?" The options are approved, one of 16 denial
    reasons, or "other."
- **Calibration (temperature):** after fine-tuning, a model tends to be overconfident. It might say "99%
  yes" when it is right 80% of the time. We fit one correction factor per question type on clinics kept
  out of training, so that "70%" really means 70%.

### Part 3: LightGBM, a gradient-boosted tree model (weighs everything)
- **A decision tree** is a flowchart of yes/no splits. "Periapical older than 12 months? → Bleeding at
  the tooth? → push risk up by 0.04." The computer picks the splits that best separate approved cases
  from denied ones.
- **Leaves hold numbers, not yes/no.** Each leaf is a small correction, positive (more likely denied) or
  negative (less likely), on a scale called log-odds, where corrections can be added up safely.
- **One tree is crude.** Boosting builds many small trees one after another. Each new tree focuses only
  on the mistakes the trees before it still make.
- **Scoring a request:** start from the base rate (about 64% denied in training), add the leaf value
  the request lands in on every tree, then convert the total back to a probability between 0% and 100%.
- **The "gradient" part** is the method for measuring "the mistakes so far," so each new tree knows what
  to correct.
- **Our settings** (`scripts/risk-tree.py`): small trees (15 end points each), each tree allowed only a
  small correction, and training stops once the score on unseen clinics stops improving.
- **Inputs:** the rule pack's result for each requirement, film ages, pocket depths, bleeding, furcation,
  tooth type, age band, the clinic's past denial rate, and Laya's 7 note answers.
- **Output:** a probability of denial, plus **drivers**, meaning how much each input pushed the risk up
  or down for this specific case. This is what makes it explainable: "risk is high mainly because the
  periapical is 14 months old."
- **Why use trees and not Laya alone:** they train in seconds, work well with a few hundred examples, and
  handle numbers and dates well. They also act as an honest baseline that Laya has to beat.

### Part 4: the fixer (turns risk into action)
Code: `ophi/outcomes/fixer.py`
1. Score the request as it is now.
2. For each possible fix, make a copy of the request with that fix applied and score it again.
3. Rank the fixes by how much risk each one removes, then sort them by who does the work:
   - **auto:** Ophi does it. Today that is only swapping a retired lab code.
   - **task:** the office does it, for example taking a new X-ray or completing a perio chart.
   - **draft:** a narrative written only from facts already in the chart. The dentist approves it.
   - **dentist:** a clinical judgment that no paperwork can change.
4. The screen shows levels, not percentages: *"Now: High · After fixes: Low."*

---

## 4. How training works, and why the test is honest

1. **Data:** 600 synthetic crown requests from 40 fictional clinics. When a clinic resubmitted after a
   denial, the resubmission counts as its own example.
2. **Split by clinic, not by request:** 27 clinics train the models, 5 are used to tune and calibrate,
   and 8 are locked away for the final test. Each clinic has habits (terse notes, stale fee tables). If
   one clinic appeared in both training and test, the model could recognize the clinic instead of
   learning the rules, and the score would look better than it really is.
3. **Laya trains** for a few passes over the data and keeps the version that scored best on the 5 tuning
   clinics (`scripts/laya-finetune.py`).
4. **LightGBM trains** twice on the same split: once without Laya's answers and once with them. Comparing
   the two shows whether Laya adds anything.
5. **Everything is pinned:** the base Laya download is checked against a hash, the training data is
   hashed, and each saved model records its date, data hash and settings.

---

## 5. Results on the 8 test clinics (142 requests)

**How to read AUC:** take one denied request and one approved request at random. AUC is how often the
model ranks the denied one as riskier. 0.5 is a coin flip; 1.0 is perfect.

| Model | AUC |
|---|---|
| Trees, structured data only | 0.722 |
| Trees + Laya's note answers | 0.769 |
| Laya's "what will Sun Life decide" answer alone | 0.773 |

- **Note questions:** after fine-tuning, Laya beats both its untrained version and a base-rate guess on
  every question. For "extensively restored" it is right 94% of the time, vs 62% untrained and 77% for a
  base-rate guess.
- **Risk levels hold up on held-out clinics:** requests rated Low were denied 14% of the time, Medium
  62%, High 77%.
- **Worked example, `PA-SYN-300010`:** the fixer suggests the lab code swap (auto), adding bitewings
  (task), and "the note doesn't show the tooth is extensively restored" (dentist). The generator's answer
  key says the real reason was not extensively restored, so the fixer found it even though the letter
  was vague.

---

## 6. Limits you should state out loud

1. **Synthetic data.** The models learned our generator's version of Sun Life. This proves the
   pipeline, not the payer.
2. **The labels for the note questions come from the generator's answer key.** Real data has no answer
   key. There, labels would come from the dentist confirmations the app already records.
3. **Recovering the reason behind a vague letter is weak:** it gets the top reason right 33% of the time.
   The letters it learns from mostly name paperwork reasons, while vague letters are mostly clinical, so
   it starts from the wrong mix.
4. **It ranks fixes; it doesn't promise outcomes.** On real resubmissions, the risk after a fix only
   weakly predicted Sun Life's second decision (AUC 0.65, 40 cases).
5. **Laya alone scores about the same as trees + Laya.** The trees add explainability (the drivers), not
   accuracy. Be ready for an investor to ask "why two models?"
6. **The fine-tuned Laya is a specialist.** Asked anything outside its 8 questions, it leans toward "no."
   Don't present it as a general assistant.

---

## 7. Answers for investors

- **"Is the AI deciding anything?"** No. The written rules decide. The models estimate risk and rank
  fixes. Only lab code swaps happen without a person, and each fix cites a rule.
- **"Why not ChatGPT or Claude?"** Laya learns this payer's behaviour from outcomes, gives calibrated
  probabilities, answers the same way every time, takes about 30 ms per check, and runs on our own
  hardware in Canada, so patient notes never leave.
- **"How do you know it works?"** It is tested on clinics it has never seen, and we compare it against
  simple baselines it has to beat.
- **"What's the moat?"** Real outcome data. Every approval or denial a clinic receives becomes a
  training example. The more clinics use Ophi, the better the model gets.

---

## Try it

`make fix-plan ID=PA-SYN-300010` prints the fix plan for the worked example, using the trained models in
`var/models/`. To retrain from scratch: `make setup-ml`, then `make laya-train`.
