# Pitch video v1: review and fix list

Reviewed 2026-09-27 against `video/out/ophi-pitch-v1.mp4` (5:00, 1080p30, −14 LUFS). Method: per-section contact
sheets (`scripts/video-review-sheets.sh`, one frame every 2 s), full-resolution frames at key beats and on both
sides of every cut, and per-section loudness (`scripts/video-mix-check.sh`). A fresh-context critic agent stalled
twice on large images, so this review is the main session's own.

## What works (keep)

- The cold open: the field-guide plate, the turning tooth, then the 46-in-100 grid.
- The problem: "$13 billion" front page → stall pipeline → stat cards → Health Canada quote → rework loop →
  X-ray sweep into "ophi.".
- The value section: ROI bar where 4 × $199 fills just under one $884 crown, then "Paid for."
- The market map and the "× $199 × 12 = $42.6M" math.
- The vision: roots growing into the payer tree with a running tally, then public rules vs private decisions →
  flywheel → moat ring → intelligence layer.
- Audio: narrated sections sit at −16 to −17.7 LUFS before mastering, true peak ≤ −1.9 dBFS, music ducks under
  the voice.

## Fix list (pass 2)

| # | Where | Problem | Fix | Status |
|---|---|---|---|---|
| 1 | Demo, throughout | The stage rail and callout chips sit on top of app text (e.g. 1:23 "Every check cites…" over the Grid rows) | Reserve a band under the app window for the rail and callouts; callouts never cover UI text | done in v4 demo |
| 2 | Vision end, 4:06–4:09.8 | "The intelligence layer" diagram is on screen for about 3.7 s before the cut to black | Longer vision tail (layout.json: 0.9 → 2.9 s) | done (holds ~4.7 s) |
| 3 | Market → vision, 3:20.1 | Hard cut from ivory paper to dark film | X-ray exposure/sweep from market's last frame into vision | done (X-ray sweep in) |
| 4 | Patient, 0:25–0:28 | "A preauthorization" sheet sits empty for about 3 s before the list | Draw four ghost rows as soon as the sheet lands; fill each on its word | done |
| 5 | Market, 3:18 | "1,100+ clinics. One rollout." They are two groups | "1,100+ clinics. Two decisions." | done |
| 6 | Demo, 1:07–1:12 | The opening board shot is small; its text is unreadable | Push in to legible scale sooner | done in v4 demo |

## Factual flag for the team

The narration says Ophi "reads each chart straight from the practice software". The demo runs on recorded
and mock case data. The ABELDent read works in the lab. Fine for a product pitch; know it if a judge asks.

All six fixes landed in the v4 rebuild (script v4, narration ~18% faster than v1).
