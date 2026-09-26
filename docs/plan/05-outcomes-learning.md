# Learning from past preauth outcomes

*Goal: use past approved and denied CDCP crown preauthorizations to raise the approval odds of a new
request, by telling the clinic what to fix before it is sent and applying the safe fixes automatically.*

## 0. The commitment this keeps

The rule pack still produces the verdict ([02-reasoning.md](02-reasoning.md) §0). What past outcomes add:

- a reading of the free-text note, which the rules can't do;
- a ranking of which fix matters most, learned from how Sun Life actually decided;
- the risk that remains after the fixes, and what is causing it.

No model output changes a requirement or a verdict. Every suggested fix is tied to a rule-pack clause.

## 1. What Sun Life actually does (research, 2026-09)

| Finding | Source |
|---|---|
| Crowns are about **37% approved** (complete submissions, May 2026). Overall preauth approval is 46%. | Health Canada via [Oral Health Group](https://www.oralhealthgroup.com/dental-governance-regulations/cdcp-update-less-than-half-of-dental-preauthorization-requests-approved-as-new-trends-emerge-1003996608/) |
| Incomplete submissions are roughly **30% of denials**. The rest are clinical, duplicate or ineligible. | Derived from HC figures (41.7% approval including incomplete requests vs 52.2% excluding them) |
| Crowns have "fewer complete submissions" than other services | [Oral Health Group](https://www.oralhealthgroup.com/dental-governance-regulations/half-of-complex-dental-claims-denied-health-canada-responds-to-concerns-over-cdcp-1003988136/) |
| **Sun Life publishes no denial-reason catalogue.** Only N05 ("not covered") is public, and dentists report letters "without any details". | [cdcp-rules.md](../research/cdcp-rules.md) §4, §6 |
| Seniors are 87% of members treated (2024–25) | [HC annual report](https://www.canada.ca/en/health-canada/services/publications/health-system-services/canadian-dental-care-plan-2024-2025.html) |
| No public data on resubmission success | — |

**Crown denial patterns.** Each maps to Guide §6.3.5 or the documentation matrix:

- missing, stale or wrong-type radiograph;
- no complete perio chart, or a gum-score (PSR) result that forces one;
- untreated caries or perio elsewhere in the mouth;
- the tooth is not "extensively restored": a posterior tooth without a root canal needs 5 surfaces, an anterior needs incisal-edge loss;
- the root canal hasn't healed;
- active perio, poor bone support or furcation at the tooth;
- insufficient ferrule, or crown lengthening needed;
- a cracked-tooth, sensitivity or cosmetic rationale;
- an ineligible third molar;
- frequency or age limits;
- a duplicate request;
- a retired lab code.

**The reason set is closed by law.** A consultant can deny only on grounds written in the Guide and
the benefit grid. That is about 18 reasons, all encoded in `packs/cdcp/2026-01-26/pack.yaml`. What varies
is whether the letter names the reason.

## 2. The data

### 2.1 Datasets
| Folder | Records | What it is |
|---|---|---|
| `fixtures/cdcp_approvals/`, `fixtures/cdcp_denials/` | 60 + 60 | The original synthetic set covering 9 codes. Documents are dropped at random, so there is no clinical signal. |
| `fixtures/cdcp_crowns/` | 600 | Realistic crown set from `scripts/gen-cdcp-crowns.py` (seed 2026). 36% approved, 36% of denials are incomplete submissions, 29% of letters are vague. |

### 2.2 How `gen-cdcp-crowns.py` builds a request
1. **Hidden clinical state:**
   - Tooth: molars 51%, premolars 30%, anteriors 17%, third molars 2%.
   - Root canal (about half), and whether it is recent or has a lesion.
   - Surfaces restored, cusp or incisal-edge loss, the stated indication.
   - Gum scores per sextant, pocket depths and bleeding at the tooth, bone loss, furcation.
   - Margin below the gum, pending basic treatment, a prior crown.
2. **Clinic habits:** 40 fictional Ontario clinics, each with its own documentation care, note style (terse, standard or detailed), channel, and whether it runs a stale fee table.
3. **Rendering:** dated attachments, a perio summary, a treatment plan (sent by careful clinics), a free-text note, and sometimes a boilerplate narrative that may not be true.
4. **Simulated consultant:**
   - Acts on problems it can *see*. For example, active perio is hidden if no complete chart was sent.
   - Acts on 80% of what it sees, and denies 4% of clean requests anyway.
   - Clinical denials get a vague letter half the time.
   - Fixable denials are resubmitted 45% of the time, with what was re-sent and the outcome recorded.

### 2.3 One record (schema `cdcp-preauth-export/2`)
| Section | Contents |
|---|---|
| `member` | Age band, province, income band, co-pay. No names. `member_id` is hashed on ingest. |
| `provider` | Clinic ID, specialty |
| `services[0]` | Procedure code, tooth (FDI), fee, lab codes |
| `attachments[]` | Type, count and `captured_date` for each document |
| `perio_summary` | Complete or PSR-only chart; PSR per sextant; 6 site depths at the tooth; bleeding; furcation class |
| `treatment_plan` | Pending and completed codes, with the root canal date |
| `clinical_notes`, `narrative` | Free text |
| `prior_history` | Prior crown on the tooth, earlier request IDs |
| `decision` | Status, `reason_code` (`UNSPECIFIED` when the letter is vague), letter text, the documents a gap letter asks for (`missing_documents`), amount |
| `followup` | Resubmission: which problem it fixed, what was sent differently (`changes`: added attachments, completed treatment, corrected lab code or rewritten note), its outcome, and the second letter's reason when denied again |
| `_generator_truth` | The answer key: true violations, what the consultant could see, what it acted on, and the reason each denial letter would have named had it not been vague (`denial_reason`, `resubmission_denial_reason`). **No model or feature may read it**, except as labels for the note-question training in §4.2. |

Worked example, `PA-SYN-300010`:
- Crown on #25. The note reads *"#25 MODB composite. Tooth fractured, unrestorable with direct restoration."*
- No bitewings were sent, and the lab code is 99222.
- Denied with *"does not meet the CDCP criteria"*.
- The true reason is that the tooth isn't extensively restored: 4 surfaces, no root canal, no cusp lost.

## 3. What the rule pack contributes

`packs/cdcp/2026-01-26/pack.yaml` (the same file as `docs/cdcp-pack.yaml`) contains:

- **The schedule:** which codes need preauthorization, frequency limits, retired codes.
- **14 cited requirements:** the documentation checklist and what satisfies each one.
- **Special paths:** a PSR can stand in for a full chart, but only as "at risk", and a PSR escalation forces the full chart.
- **Criteria the dentist confirms:** crown-to-root ratio, ferrule, furcation, endo healed, extensively restored.

Its roles in this system:
1. **Certain answers.** A documentation gap is a fact. No model is needed, and each gap cites its clause.
2. **Features.** Each requirement's status (met, missing, unknown) becomes a model input.
3. **Guardrail.** No fix may break a rule, and every fix cites a clause.
4. **The reason list.** Laya's denial reasons are the pack's requirements plus "other".
5. **Where the rules end.** On all 630 crown requests assessed, `restorability`, `extensively_restored` and `endo_healed` were indeterminate. That evidence lives in the note, and it is Laya's job.

## 4. Models: Laya and a tree model

```
note ──► Laya (fine-tuned) ──► yes/no answers (0.0–1.0) ─┐
                                                          ├─► tree model ──► denial risk + drivers
chart, dates, codes, rule-pack statuses ──────────────────┘
```

### 4.1 Tree model (gradient-boosted trees)
- **Inputs:**
  - rule-pack status for each requirement;
  - film ages; perio depths, bleeding and furcation; age band; tooth class;
  - lab code validity; channel;
  - the clinic's past denial rate, computed only from earlier requests;
  - Laya's note answers.
- **Output:** probability of denial, plus how much each input contributed.
- **Why it's used:** it trains in seconds, works on a few hundred rows, handles numbers and dates well, and serves as the honest baseline Laya has to beat.

### 4.2 Laya (Convai Innovations, Apache 2.0, 421M parameters, ModernBERT)
- Open-weight clone of Jev, released 2026-09-18. It answers typed questions: **Noul** (P(yes)), **Choice** (a distribution over options) and **Score** (a position on ordered levels). Install with `pip install laya`.
- **It must be fine-tuned.** Untrained, it scores 0.36 on the typed-decisions benchmark, below a trivial baseline, and it is over-confident until a temperature is fitted.
- **Context is 512 tokens:** the note plus a short structured summary.
- **Note questions (Noul).** Each is a separate yes/no, so several can be true at once:
  - lost cusp or incisal edge documented;
  - recent root canal, or a lesion remains;
  - pending fillings or scaling mentioned;
  - crown lengthening, or a margin below the gum;
  - cracked-tooth, sensitivity or cosmetic rationale;
  - furcation or bone loss mentioned;
  - the note describes the tooth at all, as opposed to "needs crown".
- **Reason question (Choice):** approved, or one of the rule-pack denial reasons, or "other".
  - Trained on letters that name a reason.
  - Applied to vague letters to infer the likely reason.
- **What it gives that general gen AI can't:**
  - it learns this payer's behaviour from outcomes;
  - probabilities you can trust once calibrated;
  - the same output every time;
  - about 30 ms per check, on local hardware, so notes stay in Canada.
- **What it can't do:** write prose. Claude, or a template, writes the wording, using only facts from the chart.
- **Why not Jev:** it can't be fine-tuned, and its data is hosted in the US with no Canadian residency.

### 4.3 Reasons outside the list
1. Every Choice question includes "none of these / other". That answer routes to a person.
2. Each reason is also its own Noul question, so no reason is forced to win.
3. When probability is spread across reasons, the output is "unclear" and goes to a person.
4. Denials the model didn't expect collect on `/outcomes`. The rules editor adds a reason or rule, and the model is retrained.

## 5. From probabilities to next steps

1. **Diagnose:** score the request as written.
2. **What-if:** build a copy for each candidate fix, re-score it, and rank fixes by how much risk they remove.
3. **Act:**
   - ⚙️ **Automatic, safe fixes:** swap retired lab codes; attach films or charts the PMS already has.
   - 📎 **Tasks:** take a periapical, or complete the perio chart.
   - ✍️ **Drafts, which the dentist approves:** note or narrative wording built only from chart facts.
   - 🦷 **Dentist decides:** clinical problems no paperwork fixes. Show the covered alternative, e.g. a large filling instead of a crown.

### 5.1 Risk level: now and after fixes
There is no percentage on screen. It shows *"Now: High · After fixes: Low"* plus one line on what remains. What matters is the risk left after the fixes:

| After fixes | Meaning | Admin action |
|---|---|---|
| High → Low | The problems were paperwork, and they're fixed | Submit |
| High → High (clinical) | A problem no paperwork fixes | Dentist considers the covered alternative, or tells the patient the likely cost |
| High → Medium (timing) | Root canal too recent | Wait and resubmit, instead of taking a denial |
| Low | Nothing to do | Send now; work first on requests fixes can turn around |

## 6. Already built

| Piece | Where |
|---|---|
| Export → `Case` adapter: dates, perio, plan, endo, lab codes; hashed IDs | `ophi/outcomes/adapter.py` |
| Denial reason → requirement map, edited by the rules editor | `packs/cdcp/2026-01-26/denial_map.yaml`, `ophi/outcomes/denial_map.py` |
| Outcomes schema: RLS, private schema, lift and blind-spot views | `supabase/migrations/0001_outcomes.sql`, `ophi/outcomes/store.py` |
| Ingest and per-requirement denial lift → weights file | `ophi/outcomes/ingest.py`, `ophi/outcomes/weights.py`, `ophi outcomes ingest|stats` |
| Weights break ties between equal-ranked actions; their hash is recorded on each assessment | `ophi/engine/assess.py` `rank_actions` |
| `/outcomes` page for the rules editor | `ophi/web/templates/outcomes.html`, `ophi/outcomes/report.py` |
| Realistic crown dataset | `scripts/gen-cdcp-crowns.py`, `fixtures/cdcp_crowns/` |
| One-command local run: Postgres in Docker, ingest, stats, screenshots | `scripts/outcomes-local.sh [--shot]` |
| Laya pinned download + provenance check (HF revision, signed PyPI wheel) | `make setup-ml`, `scripts/laya-download.sh`, `scripts/laya-provenance.sh` |
| Training set: what was sent → text and features, resubmissions as their own examples, split by clinic | `ophi/outcomes/training_set.py`, `ophi/outcomes/laya_questions.py` |
| Fine-tune, score against base checkpoint and base rates, LightGBM with and without Laya | `make laya-train` (`scripts/laya-finetune.py`, `laya-eval.py`, `risk-tree.py`) |
| Risk scorer: Laya note answers + saved LightGBM → P(denied) and drivers | `ophi/outcomes/risk.py` (`RiskModel`) |
| What-if fixer: fixes from engine actions and Laya's reading, ranked by risk removed; Now / After fixes | `ophi/outcomes/fixer.py` (`plan_fixes` → `FixPlan`), `make fix-plan ID=… CHECK=--check` |

## 7. Build plan (about 1 day)

1. **Laya baseline.** Install it and run it untrained on 50 notes against the answer key. About 30 min.
   → verify: record accuracy per question; expect it to be poor.
2. **Split and tree baseline.** Split 80/20 by clinic, so no clinic appears in both halves. Train gradient-boosted trees on structured fields only. About 1 h.
   → verify: AUC and calibration (Brier score) on the 20%.
3. **Fine-tune Laya.** Train the note questions and the reason question, then fit a temperature on part of the 80%. About 2–3 h, mostly training.
   → verify: per-question accuracy vs step 1; calibration error.
4. **Combine and compare.** Tree on structured fields alone vs tree plus Laya's answers, on the same 20%. About 1 h.
   → verify: the combined model beats the tree alone on AUC. If it doesn't, report that.
5. **What-if fixer and screen.** Rank fixes; show "Now / After fixes"; auto-fix lab codes and attachments; draft the note from chart facts. About 3 h.
   → verify: on `PA-SYN-300010`, the fixes are the lab code swap, the bitewings, and the extensively-restored decision.
6. **Browser check.** Playwright on demo cases, desktop and phone widths; copy check for banned wording. About 1 h.

### 7.1 Results (2026-09-26, 8 held-out clinics, 142 requests)
- Note questions, fine-tuned vs untrained vs base-rate guess: every question beats both on accuracy and Brier. For example, extensively restored scores 94% / 62% / 77%.
- Denial risk AUC: tree on structured fields 0.722; tree + Laya notes 0.769; Laya's decision head 0.773.
- Reason recovery on vague letters: top-1 33%. Named letters are mostly documentation gaps and vague ones mostly clinical, so a model trained on named letters starts from the wrong mix.
- Fixer, 254 calibration + test requests: low 14% denied, medium 62%, high 77%.
- Fixer on real resubmissions: the clinic's actual fix lowers the risk by about 0.12 whether or not Sun Life then approved. The after-fix risk separates the second decisions only weakly (AUC 0.65, 40 cases). It ranks fixes; it doesn't predict their outcome.
- `PA-SYN-300010` (step 5's check): lab code swap (auto), bitewings (task), "the note doesn't show the tooth is extensively restored" (dentist, clinical). The true reason behind its vague letter is CLIN_NOT_EXT_RESTORED.

## 8. Limits
- The data is synthetic, so the models learn the generator. This proves the approach, not Sun Life's behaviour. Real decisions are needed before any clinic relies on it.
- Labels for the note questions come from `_generator_truth`. With real data they come from the dentist confirmations the app already records.
- Laya's context is 512 tokens. Long notes need a summary first.
- Hosted Supabase (ca-central-1) has not been migrated yet.

## 9. Serving

The models run in the Python reasoning core, never in a web front end. PLAN.md already puts a JSON-over-HTTPS contract between the core and the Next.js web tier.
- **Why not in Next.js.** The fine-tuned Laya is 840 MB (fp16), too large for a serverless function bundle or a browser download. The notes it reads are patient information and stay in the Canadian-hosted core. `site/` is the public waitlist and never sees chart data.
- **Contract.** The web tier asks the core for a case's `FixPlan` (`ophi/outcomes/fixer.py`, pydantic, JSON as is) and renders levels, never scores. Only `auto` fixes are applied without a person, and each fix cites its pack clause.
- **Runtime.** Training needs PyTorch and a GPU. Serving doesn't: export the fine-tuned model with `torch.onnx.export`, using the inputs `laya.ONNXAgent` feeds (`input_ids, attention_mask, marker_pos, marker_mask, qtype` → `logits, act_logits`). Run it on CPU with ONNX Runtime; int8 quantization would roughly halve the size and speed CPU inference. LightGBM loads its `model.txt` directly and needs no conversion.
- **Demo.** The demo app never loads the models. `scripts/laya-demo-predict.py` scores the demo cases offline and commits one plan per case (`cases/demo/laya/`), so it runs without PyTorch.
