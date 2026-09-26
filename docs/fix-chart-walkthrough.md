# How the Fix chart panel works: Laya, LightGBM and the fixer

*A walkthrough of the case page's **Fix the chart** step, using Teresa Kowalchuk's crown on #46 as the example.
It covers how the order of fixes is chosen, how the fine-tuned Laya model reads the note, how LightGBM turns
everything into a denial risk, and how each fix is re-scored to see how much risk it removes. For the
investor-level background (what ML is, results, limits), see [outcomes-explainer.md](outcomes-explainer.md). For
the full technical plan, see [plan/05-outcomes-learning.md](plan/05-outcomes-learning.md). Figures are from the
2026-09-26 models.*

---

## The short version

1. The **rule engine** (no ML) checks the chart against the CDCP rule pack and lists the gaps: a stale
   periapical, a 4-point perio chart where a 6-site one is needed, and so on.
2. **Laya**, fine-tuned on past crown requests, reads the request text (mostly the clinical note) and answers 7
   yes/no questions, each as a probability.
3. **LightGBM** takes the rule engine's findings, the raw chart values (film ages, depths, bleeding) and Laya's 7
   answers, and outputs **P(denied)**.
4. The **fixer** makes one copy of the request per fix, applies that fix to the copy, and scores every copy
   again. The drop in P(denied) for each copy decides the order. It also scores one copy with *all* fixes
   applied, which gives the "After these fixes" level.
5. All of this runs **offline**, and the result is saved as JSON. The web app never loads a model. It shows the
   saved plan only if the chart still matches the one that was scored.

```
                         OFFLINE (GPU box, scripts/laya-demo-predict.py)
 ┌──────────────────────────────────────────────────────────────────────────────────────┐
 │ chart (Case) ─► case_export.to_export ─► request as "sent"                           │
 │                                            │                                         │
 │            ┌───────────────────────────────┼──────────────────────────┐              │
 │            ▼                               ▼                          ▼              │
 │   rule engine: gaps + actions     copy + fix 1 … copy + fix N    copy + ALL fixes    │
 │            │                               │                          │              │
 │            └──────► every copy: Laya (7 note answers) ─► LightGBM ─► P(denied)       │
 │                                            │                                         │
 │                  fixer: risk_drop per fix, sort, levels, "what's left"               │
 │                                            ▼                                         │
 │              cases/demo/laya/<case_id>.json  (plan + SHA-256 of the request text)    │
 └──────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                         ONLINE (web app, no torch, no lightgbm)
 ┌──────────────────────────────────────────────────────────────────────────────────────┐
 │ GET /cases/{id} ─► readout.load ─► hash of today's chart == saved hash?              │
 │                        yes ─► present.fix_panel ─► case.html (numbered rows, levels) │
 │                        no  ─► "The chart changed after Ophi last compared it…"       │
 └──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Where the case comes from: the chart becomes a "request"

Both models were trained on past crown requests in the export shape Sun Life's data comes in
(`fixtures/cdcp_crowns`, 600 synthetic requests). A live chart from the PMS is a `Case`, which is a different
shape. `ophi/outcomes/case_export.py` converts the `Case` into that same export shape: the latest periapical of
the tooth and its date, the bitewing pair (dated by its older side), the perio chart (marked "complete" only if
every present tooth has 6 sites), the treatment plan, prior crowns on the tooth, and the notes about the tooth.

This matters because the models only know that format. Converting keeps a clinic's case and a training example
identical in form, so the model sees nothing unfamiliar.

---

## 2. Laya: the fine-tuned note reader

**What it is.** Laya is an open-source 421M-parameter ModernBERT model from Convai Innovations (Apache 2.0). It
doesn't generate text. You give it a text and a multiple-choice question, and it returns a probability for each
option.

**What it reads.** `training_set.request_text` renders the request as a short text: a structured header ("Crown
27201 on tooth 46 (molar). Films: periapical N days old; bitewings …. Perio: psr only chart …") followed by
the clinic's note. Training and run time use this same function, so Laya always sees one consistent format.

**What it answers.** The 7 note questions in `ophi/outcomes/training_set.py` (`NOTE_QUESTIONS`) cover what the
rules can't read from structured fields:

| Question key | Asks |
|---|---|
| `structure_lost` | Has the tooth lost a cusp or incisal edge? |
| `extensively_restored` | Does it meet CDCP's "extensively restored" definition? |
| `endo_not_healed` | Is a root canal recent or not yet healed? |
| `pending_basic` | Are fillings or scaling still to do elsewhere? |
| `subgingival_margin` | Is the margin below the gum, or is crown lengthening needed? |
| `uncovered_indication` | Is the crown for a crack, sensitivity or appearance? |
| `poor_support` | Is there furcation or poor bone support? |

It was also trained on an eighth question, "What will Sun Life decide?" (approved, or one of 16 reasons). The
risk model doesn't use that question, but training on it helps Laya learn the task.

**How it was fine-tuned** (`scripts/laya-finetune.py`, run by `make laya-train`):

- **Labels.** The note-question labels come from the synthetic generator's answer key (`_generator_truth`). The
  decision label comes from the denial letter, and only when the letter names a reason. Vague "doesn't meet
  criteria" letters are kept out of training, because real data would give no reason for them either.
- **Split by clinic.** 27 clinics are used for training, 5 for calibration and 8 for the final test. No clinic
  appears in two splits, so the model can't score well by recognizing a clinic's writing style.
- **Loss.** Soft cross-entropy on the option logits, over 4 epochs with AdamW. It keeps the epoch with the lowest
  loss on the calibration clinics.
- **Calibration.** After training, one temperature per question size is fitted on the calibration clinics, so
  that "0.7 yes" is right about 70% of the time. This is what makes the fixer's `FLAG = 0.5` cut point meaningful.
- **Pinning.** The base checkpoint revision, a SHA-256 of the training data and the training date are written into
  `var/models/laya-cdcp/rl_agent_config.json`. That is the source of the `laya-cdcp 2026-09-26 data d8f8c71bc46c`
  string on the page.

**Teresa's answers** (from `cases/demo/laya/kowalchuk.json`):
`structure_lost 0.996, extensively_restored 0.970, endo_not_healed 0.033, pending_basic 0.233,
subgingival_margin 0.160, uncovered_indication 0.013, poor_support 0.104`. The note clearly supports "extensively
restored" and raises no clinical concern, so no clinical item shows up for the dentist.

---

## 3. LightGBM: the denial-risk model

**What it is.** A gradient-boosted tree model. It is a sum of many small decision trees, each one correcting the
errors the earlier trees still make. The output is a log-odds score, which a sigmoid turns into P(denied).

**Inputs** (`training_set.features` plus `risk.with_note_answers`):

- `req_*`: the rule engine's status for each requirement (satisfied, missing, unknown, and so on).
- Raw values the rules don't weigh: `pa_age_days`, `bw_sides`, `perio_age_days`, `perio_complete`, `max_psr`,
  `max_depth_at_tooth`, `bleeding_at_tooth`, `furcation_class`, `prior_crown_months`, `note_chars`,
  `has_narrative`, and others.
- Context: `tooth_class`, `age_band`, `channel` and `clinic_denial_rate`.
- `laya_*`: Laya's 7 probabilities.

A value that wasn't sent stays missing (NaN), so the model learns what an absent document means.

**How it was trained** (`scripts/risk-tree.py --laya … --save`): on the same clinic split as Laya, using small
trees (15 leaves, learning rate 0.03) and early stopping on the calibration clinics. It is trained twice, once
without Laya's answers and once with them. On the 8 test clinics, AUC is 0.722 on structured data alone and 0.769
with Laya's answers. The combined model is saved to `var/models/risk-tree/model.txt`, and its SHA-256 is the
`risk-tree 2026-09-26 581e0edc6f82` label.

**Drivers.** `RiskModel.score` also asks LightGBM for `pred_contrib`, the SHAP-style contribution of each input to
this one request's log-odds. For Teresa as charted, the largest push is `pa_age_days` (+0.58): her periapical is
about 34 months old. Next come the rule check's overall verdict (+0.17) and the PA requirement itself (+0.10).

**Levels, not percentages.** `fixer.level` maps P(denied) to a level: below 0.45 is **Low**, 0.45 to 0.70 is
**Medium**, and 0.70 or above is **High**. On held-out clinics, Low requests were denied 14% of the time, Medium
62% and High 77%. The raw number is never shown on screen.

---

## 4. The fixer: re-scoring each fix to rank them

Code: `ophi/outcomes/fixer.py`, `plan_fixes`.

### 4.1 Build candidate fixes (rules first, never the model)

Every candidate fix comes from a **rule-engine action**, so each one points to a clause in the rule pack. The
fixer turns each action into a `Fix` with a **kind** and a **patch**:

| Kind | Who | Example | Patch (what the what-if copy changes) |
|---|---|---|---|
| `auto` | Ophi | Swap retired lab code | `lab_codes` → current codes |
| `task` | office (MOA) | Take a periapical; complete the perio chart; finish pending fillings | adds an attachment **dated today**, or marks treatment completed |
| `draft` | dentist approves | Narrative | a narrative built only from facts already in the chart |
| `dentist` | dentist | "Tooth meets extensively restored" | none: paperwork can't change a clinical fact |

Laya shapes the dentist-side items. For example, when `endo_not_healed ≥ 0.5`, the fix becomes "Wait for the root
canal to heal, then take a new periapical", a timing task. When the note reads fine, the item is labelled "Laya's
reading of the note raises no concern here."

### 4.2 The what-if: re-score each patched copy

```python
[now] = model.score([base])                                   # the request as it stands
copies = [with_fixes(base, [f]) for f in patched]             # one copy per fix, that fix applied
copies.append(with_fixes(base, patched))                      # plus one copy with every fix applied
scores = model.score(copies)                                  # one batched Laya + LightGBM pass
f.risk_drop = max(0, now.p_denied - score_for_f.p_denied)     # per fix
```

`with_fixes` applies a patch the same way a real resubmission is applied in the training data
(`training_set.resubmitted`). A new periapical replaces the old one with today's date, and a new perio chart
becomes "complete". Each copy then goes through the **whole pipeline again**. Its request text changes (for
example, "periapical 0 days old"), so Laya re-reads it. Its features change (`pa_age_days` drops to 0, and the rule
engine now marks `req_radiograph_pa` satisfied), so LightGBM re-scores it.

Two assumptions to keep in mind:

- **A new document shows nothing new.** The copy doesn't know what the new film will show. "After these fixes" is
  therefore the best case, not a promise.
- **A fix can't add risk.** A small tree can score a fix as slightly *raising* risk. That is noise, so the drop is
  floored at 0. A zero drop means the model can't see an effect in past decisions. It does not mean the rule
  doesn't require the fix.

### 4.3 Order

```python
fixes.sort(key=lambda f: (f.kind != "auto",          # free fixes Ophi can make go first
                          f.risk_drop is None,       # scored fixes before unscored ones
                          -(f.risk_drop or 0.0),     # biggest drop in P(denied) first
                          KIND_ORDER[f.kind]))       # ties: auto, task, draft, dentist
```

This is the order behind the **1, 2** numbers on the page.

### 4.4 "Now" and "After these fixes"

- **Now** is the level of `now.p_denied`.
- **After these fixes** is the level of the all-fixes copy, with two overrides (plan §5.1). If a clinical concern
  remains, it says so, because paperwork can't clear it. If only a timing concern remains (for example, waiting
  for a root canal to heal), the level is capped at Medium, because waiting resolves it.
- **"Most of what's left: …"** is the strongest input still pushing risk *up* on the all-fixes copy. Inputs no one
  can change before sending (tooth type, age, the clinic's history, the channel) are skipped. So are note answers
  that sit on the no-concern side but still push up, since reading those aloud would invent a problem.

### 4.5 Teresa's numbers

| | P(denied) | Level |
|---|---|---|
| As charted | 0.798 | **High** |
| + new periapical only | 0.666 (drop **0.132**) | |
| + complete perio chart only | no drop (floored at 0) | |
| + narrative only | no drop | |
| + all fixes together | 0.614 | **Medium** |

"Most of what's left: bleeding at the tooth": after all the fixes, bleeding at #46 is the largest input still
raising the score that the office can act on.

---

## 5. How the web app shows it

### 5.1 Offline, then cached (`scripts/laya-demo-predict.py`)

The models need torch and a GPU, so the web app never loads them. After retraining, this script runs once. For
each demo case it:

1. Builds the case from the PMS fixture and runs `plan_fixes`.
2. If Ophi has safe fixes of its own (`ophi/fixes.py`, today only the lab-code swap), plans a second state with
   those applied too, so the page still has a plan after staff press **Apply**.
3. Writes `cases/demo/laya/<case_id>.json` with each plan and a **SHA-256 of the request text** it scored.

### 5.2 On every page load (`ophi/web/app.py` → `present.py`)

- `GET /cases/{id}` calls `readout.load(case_id)` and `present.fix_panel(...)` while the case is at the **Fix
  chart** stage.
- `Readout.matching(case)` rebuilds today's request text from the **live** chart and compares hashes. If the chart
  changed since scoring (for example, staff took the new periapical in the PMS), no plan matches. The page then
  says "The chart changed after Ophi last compared it…" and falls back to the rule engine's gaps in the engine's
  order. This is why **Check the chart again** is just a reload: the rule engine re-reads the chart every time, and
  a stale risk is never shown.
- `fix_panel` builds the staff rows:
  - It keeps only **auto** and **task** fixes the office does, in the fixer's order. It drops any fix whose
    requirement the live chart now satisfies (`_still_open`).
  - Each row uses the **rule engine's gap** for its title and facts ("Take a periapical of #46 at the Sep 20
    appointment", "Last one Nov 14, 2023, 34 months old"). The plan supplies the order and the effect.
  - Effect words come from `risk_drop`, and the number itself never reaches the screen:
    - the largest drop → **"Lowers denial risk the most"**
    - a drop below 0.01 → **"No clear effect on denial risk in past decisions. Still required by CDCP."**
    - anything else → "Lowers denial risk a little"
  - Engine gaps the plan didn't score are added at the end with "Not scored against past decisions."
- Narratives, and dentist items with a clinical or timing concern, go to the **For Dr. Priya Lau** box instead of
  the staff list.
- The `risk_block` macro shows **Denial risk: Now → After these fixes**, the "what's left" line, and the model
  labels. It always carries the disclaimer that this is *a guide from past decisions in synthetic training data,
  not Sun Life's answer*.
- The board card uses the same panel through `present.board_risk`. The card's next action is the plan's first
  fix, not the engine's.

The rest of the panel doesn't come from the models. The red banner ("sooner than Sun Life's usual 7 days") comes
from `present.timing`, and **Skip gaps to test** is a test-run shortcut (`POST /cases/{id}/test-skip`).

### 5.3 What the models can't do

- They can't change a requirement or a verdict. The rule pack decides what's required, and every fix cites it.
- They can't write to the PMS. Staff make the fix in their PMS, and Ophi re-reads the chart.
- They can't show a risk for a chart they didn't score. A hash mismatch hides the risk.

---

## 6. Current state and caveats

- **Synthetic data.** Both models learned our generator's version of Sun Life, which is why the page says so. We
  need real decisions before a clinic relies on these numbers.
- **Pre-computed only for the demo cases** (`cases/demo/laya/*.json`). A new or edited chart shows the rule
  engine's gaps without a risk until `laya-demo-predict.py` runs again. Live scoring would need a model server.
- **"After these fixes" is the best case.** It assumes the new film or chart shows nothing new.
- **Laya is a specialist.** On questions outside its 8, it leans toward "no". Don't use it as a general Q&A
  model (debug with `make laya-ask`).
- **Accuracy vs explanation.** Laya's own decision answer (AUC 0.773) scores about as well as trees + Laya
  (0.769). The trees earn their place through the per-fix what-if and the drivers, not through extra accuracy.

## Commands

| Command | Does |
|---|---|
| `make setup-ml` | Install CUDA torch, laya and LightGBM, and fetch the pinned Laya weights |
| `make laya-train` | Fine-tune Laya, evaluate on held-out clinics, train and save LightGBM |
| `.venv/bin/python scripts/laya-demo-predict.py` | Re-score the demo cases into `cases/demo/laya/` for the web app |
| `make fix-plan ID=PA-SYN-300010` | Print a fix plan for one training request |
| `make laya-ask` | Interactive: one request through the rules, Laya, LightGBM and the fixer |
