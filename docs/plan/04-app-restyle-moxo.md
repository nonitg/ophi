# Internal app restyle in Moxo's design language: plan

Status: implemented 2026-09-24 as a full redesign that goes past this restyle (structure changed too).
`docs/reviews/2026-09-24-app-redesign.md` records what shipped and where it departs from this plan.
Scope: `ophi/web` (Queue, Case Review, Packet, Look-Back, Settings). The public site (`site/`, `DESIGN.md`)
is untouched.

Reference: moxo.com, mainly `/lp/prior-authorization`. The owner loves this look. Screenshots of Moxo and of
the current app were captured into the session scratchpad and are not committed.

## 1. What we are taking from Moxo

Moxo's page is a marketing page (Persuade). Ophi's app is a working tool (Operate). We take the look and one
structural idea. We do not take the marketing devices.

| Moxo trait | In Ophi's app |
|---|---|
| Quiet, light grotesk type (ABC Diatype, weight ~375), warm near-black `#3e3c3a` | Adopt. Light weight for display sizes only; body stays at 400 for legibility at 14px |
| White page, warm stone/beige panels | Adopt. Replaces the cool grey `#f6f7f9` page and blue-grey borders |
| Near-black primary button, outlined secondary | Adopt. Replaces the blue `#0b5fff` primary |
| Step rows tagged with **who does each step** (AI agent / referring office / human) | Adopt as the **case trail**, the core new component (§4) |
| Final "HANDS OFF TO → Clinician review" row with a person | Adopt. Sign-off by the treating dentist is always the last row. Initials monogram, no photos |
| Small-caps micro labels, monospace timestamps | Adopt for labels, dates, codes and hashes |
| Status pills with time-in-state ("FLAGGED · 2.9 DAYS") | Adopt the pill style. Time-in-state is not tracked, so see open question 2 |
| UI cards on marble/onyx textures | **Do not adopt.** In an operating tool the real UI is the card. Texture is decoration here |
| Logo wall, G2 badge, case-study carousel | Not applicable |
| Light-grey body text (~3.5:1) | **Do not copy.** Fails WCAG AA. Muted ink stays ≥ 4.5:1 |

Rules that stay binding: colour still means status only (the current stylesheet rule), the copy law, the
15-second-glance contract from `docs/reviews/2026-09-21-ui-glance-redesign.md`, and nothing functional lost.

## 2. Tokens

Contrast was measured against white / card `#f7f6f3` / frame `#efebe3`.

| Token | Now | Proposed | Contrast |
|---|---|---|---|
| `--bg` (page) | `#f6f7f9` | `#ffffff` | — |
| `--surface` (card) | `#fff` | `#f7f6f3` | — |
| `--frame` (new: beige panel behind the hero verdict) | — | `#efebe3` | — |
| `--border` | `#e3e6ea` | `#e8e5de` | — |
| `--border-strong` | `#c9cfd6` | `#d3cfc6` | — |
| `--ink` | `#14171a` | `#3e3c3a` | 10.98 / 10.16 / 9.24 |
| `--muted` | `#5f6b76` | `#6b6862` | 5.55 / 5.14 / 4.67 |
| `--accent` (links, focus) | `#0b5fff` | `#3e3c3a` for buttons; links underline in ink; focus ring `#2f6fd6` | — |
| `--blocked` / `--ready` | unchanged | unchanged | 5.62 / 5.07 on white |
| `--needs` | `#b26a00` | **`#9a5b00`** | the current value is 4.24:1 on white, which already fails for small text |
| `--radius` | 8px | 10px for cards, 999px for pills, 6px for chips | — |
| `--font` | system stack | **Geist** (self-hosted woff2), 400 body / 350 display | — |
| `--mono` | system mono | **Geist Mono** | — |

The fonts must be self-hosted in `ophi/web/static/fonts/`, not loaded from a CDN, because the app runs on a
practice server with outbound HTTPS only. See open question 1.

Type scale: page h1 28px/350, verdict h2 28px/375, hero gap title 21px/450, body 14px/400, micro labels
11px/500 in small caps with +.06em tracking, mono 12px.

## 3. Shared components (`macros.html`, `app.css`)

1. **Pill** (`verdict_badge`): a tinted pill in small caps (`BLOCKED`, `NEEDS INPUT`, `COMPLETE`, `SIGNED`) with an
   optional mono suffix after a middle dot (`BLOCKED · 3D TO APPT`). The same macro serves every screen, as it
   does now.
2. **Actor tag** (new macro `actor_tag(kind, name)`): right-aligned, muted. It covers four kinds:
   - `chart` for evidence found in the PMS
   - `ophi` for a check or draft Ophi made
   - `staff` for the coordinator
   - `dentist` for the treating dentist
   Ophi gets a small mark, like Moxo's agent glyph. People get an initials monogram (`PL`).
3. **Trail row** (new macro `trail_row`): a status mark, a step label, an optional clause chip, an actor tag and a
   mono timestamp or date. This is the unit of the case trail.
4. **Micro label** (`.label`): small caps in muted ink. Replaces `sec-title` and `h3` for section labels.
5. **Buttons**: primary is a charcoal fill with white text; secondary is outlined `--border-strong`. Focus
   ring stays visible.

## 4. The case trail (new, Case Review)

This is Moxo's hero card rebuilt from real engine output. Every row comes from data Ophi already has:

- `RequirementResult.evidence` / `satisfied_via` for chart rows
- `Action` for Ophi's flags
- the assertion records and audit log for people rows
- the sign-off state for the last row

```
┌ Prior authorization | Kowalchuk · 27211 crown #46 ─────────────── 7 OF 12 ┐
│ ✓ Proposed crown read               27211 · #46          CHART  Sep 17 │
│ ✓ Bitewings R+L, current            Matrix PA+BW          CHART  Mar 04 │
│ ✕ Periapical of #46 is 1038 days old Matrix PA ≤12mo       OPHI flagged  │
│ ✕ Perio chart has 4 sites, needs 6   Matrix fn 7           OPHI flagged  │
│ ? 9 clinical criteria               —                  (PL) Dr. Lau     │
│ ─ HANDS OFF TO ─────────────────────────────────────────────────────── │
│   Sign-off and submit via PMS        Ophi never transmits (PL) Dr. Lau  │
└────────────────────────────────────────────────────────────────────────┘
```

The sketch is illustrative. The Kowalchuk gap rows match the demo case; the chart rows' dates are placeholders.

Placement: this replaces the "Before this can go out" numbered list's visual shell, not its content.

- The rank-1 action stays the hero. It becomes the first open row, expanded to show its "why" at 17px, as now.
- The full 13-row requirement list stays in its fold.
- The trail shows only the rows that matter: found evidence, flagged gaps, pending people steps, and the hand-off.
- Proposal confirm/reject buttons live inside the row they belong to.

Code: a new presenter `case_trail(view) -> list[dict]` in `ophi/web/present.py`, beside `gap_groups`. It
reuses `gap_groups` and `segments`; it does not re-derive them. One happy-path test in `tests/`, per CLAUDE.md.

## 5. Screen-by-screen

1. **Chrome (`base.html`)**
   - Keep the demo banner, in charcoal instead of black.
   - The topbar becomes white with a hairline border. Nav links are plain; the active one is underlined in ink.
   - The "Acting as" select is restyled as an outlined control with a monogram.
2. **Queue (`queue.html`)**
   - The headline sentence stays. It takes a two-tone treatment like Moxo's homepage: the count in ink, "$6,125 of treatment at risk" in muted.
   - Rows sit in one `--surface` card with hairline dividers.
   - The pill goes in column 1. Appointment dates move to mono. The mini segment bar and fee stay.
   - The "+4 more" becomes a quiet mono count.
3. **Case Review (`case.html`)**
   - The header facts line moves to mono for codes and dates.
   - The verdict strip sits on the `--frame` beige panel (Moxo's hero panel), with the bar on the right as now.
   - The case trail (§4) replaces the gap list's look.
   - The folds keep their order and get micro labels.
   - The assertions table gets actor monograms and small-caps column labels.
4. **Packet (`packet.html`)**
   - The sign-off card becomes the trail's final "Hands off to" row, expanded: monogram, name, licence, attestation, and the primary charcoal button.
   - The signed record renders as trail rows with mono hashes.
   - The PDF frame gets a `--frame` border.
5. **Look-Back (`lookback.html`)**
   - The four-number chain keeps its numbers at 44px/350 in Geist.
   - The anchor tile keeps its red tint.
   - The table gets small-caps headers and mono dates and fees.
6. **Settings (`settings.html`)**
   - The audit log renders as trail rows (actor monogram · event · mono timestamp) instead of a dense table.
   - CSV export is unchanged.

## 6. Order of work and verification

| Step | Work | Verify | Est. |
|---|---|---|---|
| 0 | Before screenshots of all 6 screens, desktop 1440 + mobile 390, via `scripts/demo-screens.py` | files exist | 15 min |
| 1 | Tokens + self-hosted Geist in `app.css` / `base.html` | contrast script on every text/background pair; no layout shift at 390px | 1 h |
| 2 | Shared macros: pill, actor tag, trail row, micro label, buttons | the same macro renders on every screen | 1.5 h |
| 3 | Queue | screenshot vs. before; 15-second glance still reads | 1 h |
| 4 | Case trail presenter + test, Case Review template | `make test` green; trail rows match the engine for all 6 demo cases | 3 h |
| 5 | Packet, Look-Back, Settings | Playwright flow: confirm proposal → record assertions → sign off → download → queue shows Signed | 2 h |
| 6 | Final pass | `make test`, `make eval` (45/45, false-ready gate), impeccable detector on changed files, copy-law test, one batched desktop+mobile screenshot round | 1 h |

Total: about 1.5 days. Steps 1–2 alone (tokens and components, no structural change) deliver most of the look
in about 2.5 hours, and are a sensible first cut if the owner wants to see it before the trail is built.

## 7. Open questions for the owner

1. **Font.** Decided 2026-09-24: **Geist** and Geist Mono. Geist is free (OFL) and the closest match to ABC
   Diatype, which would need a paid Dinamo licence.
2. **Time-in-state on pills.** Ophi does not record when a case entered its current state, so we can't show
   "Blocked · 2.9 days" without new tracking. Options:
   - (a) show the appointment countdown instead (`BLOCKED · 3D TO APPT`), which needs no new data. Recommended.
   - (b) add state-change timestamps to the service store.
3. **Stone texture.** Recommendation: none in the app. A flat `--frame` beige behind the verdict gets the warmth
   without decoration. The textured, illustrative case card belongs on the public site at launch, when the
   stealth posture lifts.

## 8. Out of scope

- The public site and `DESIGN.md`.
- Any change to engine output, copy, or the five-screen contract.
- Dark mode (the app is light-only today).
