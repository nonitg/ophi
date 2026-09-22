# Ophi site: enamel tooth promoted, window light and paper across the site

## Goals

1. The owner picked "Real enamel" from the tooth material lab and liked its cast shadow. The plan's
   "After pick" step: promote it, delete the lab and the old tooth path, update DESIGN.md.
2. The owner's clarified request: "add a texture and effect to the whole site … shadows across the whole
   site … more dynamic than just the flat background … add texture and life".

## What shipped

- The enamel tooth is the only tooth. The lab route, the ceramic look and the classic renderer and
  asset are deleted. `scripts/build-tooth.mjs` now builds the smoothed, indexed model (`public/tooth.bin`).
  "Show outline" became an "X-ray" toggle (aria-pressed, constant label).
- The whole site sits in one light:
  - afternoon window light from the upper left, the same direction as the tooth's key light;
  - window-bar and leaf shadows in a fixed transparent layer that the paper scrolls beneath;
  - faint cotton-paper grain;
  - section rules drawn as creases;
  - one daylight fade-in on load.
- The art is procedural (`scripts/build-room.mjs`). DESIGN.md has a "Light and material" section.
  The social image was regenerated.

## Fresh-context review

A fresh-context review agent checked the slice against both goals, the plan and CLAUDE.md. Its
verdict: goal 2 met; goal 1 partly met. Every finding was fixed:

| Severity | Finding | Fix |
|---|---|---|
| High | The tooth's cast shadow was sliced by a hard line at the canvas edge on phones and tablets | Shadow alpha fades out before the canvas edges (clip-space fade in the floor shader) |
| Medium | Muted text fell to 4.30–4.46:1 under the deepest shade | `--muted` changed to `#5c6557` (4.67:1 worst case); literal copies now use the token; `scripts/site-contrast.py` added |
| Medium | The artwork-failure check asserted before the model request failed | It now waits for the failed request, then asserts the fallback and that no canvas exists |
| Medium | aria-pressed combined with a label that flipped between states | Constant "X-ray" label with a pressed style |
| Low | Browsers without `lvh` dropped the whole background | `vh` declared first, `lvh` as an override |
| Low | Lab leftovers: `StudioLook`, a boolean→look→boolean hop, camera framing split across two files | `setXray(on, instant)`; camera framing lives in the renderer only |
| Low | Stale README, build-script and generator comments; DESIGN.md claims about the seam, the X-ray crossfade and the wedge | Rewritten to match the code |
| Low | The multiply blend cost a full-viewport blend on every scroll frame; the warm tint shifted sage toward khaki | Plain transparent shade; brand colours render exactly |
| Nit | The X-ray film touched the controls; the crease colour was repeated three times; pane coordinates were unrounded; nothing checked that the X-ray changes the canvas | Plate moved down; `--crease` token; coordinates rounded; canvas-change assertion added |

## Verification

- `pnpm build`, `tsc --noEmit`, `pnpm lint` and `pnpm test` (6/6) pass.
- `scripts/site-screens.py` passes at 1440, 1024, 768, 390 and 320 px with no overflow or page errors,
  including the real artwork-failure path and the JavaScript-disabled render.
- `scripts/site-states.py` passes: rotation, X-ray toggle, dialogs, signup states, no page errors.
- `scripts/site-light.py` viewport captures are in `outputs/site-light/`.

## Known and accepted

- Full-page captures at aspect ratios where the art is taller than the viewport (for example 768×1024)
  show a seam at the viewport height. Visitors never see it.
- The compositing cost on low-end Android is not measured on a device.
- Another session's entry-row variants share `globals.css` and `page.tsx`; they are outside this review.
