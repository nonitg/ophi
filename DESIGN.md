# Ophi — public site design

Updated 2026-09-22. Supersedes the radiograph lightbox and the earlier multi-section landing-page draft.
Public brand: **Ophi**, wordmark **ophi.**, domain **ophi.app**. The existing internal code/package paths
are not part of the public brand and were not migrated in this design task.

## Intent

A compact editorial poster for a company taking dental paperwork seriously. The page should feel
warm, curious and deliberate. One composition contains the entire first impression: “Good care.
Less paperwork.”, an original enamel sculpture, a brief statement of purpose and signup.

The user liked the ivory/forest/orange language and sculpture but rejected the conventional
headline → facts → chart → call-to-action stack. Keep the language; break the layout pattern.

## Structure and purpose

- Lowercase wordmark: identify Ophi without an invented registered-trademark claim.
- “In the making”: establish pre-launch status once.
- Headline: express the company’s aspiration without promising payer outcomes.
- Tooth: anchor the subject in dentistry; tactile interaction gives the page a memorable physical quality.
- Introduction: identify who the company is building for.
- “Why Ophi?”: a native modal with plain-language context and one cited volume statistic. Evidence is
  available without turning the homepage into a report. No decorative graph or implied approval comparison.
- Inline signup: make the next step immediately available to any interested visitor.
- Clinic software: one optional custom listbox under the email field (native select before hydration), with a separate exit for non-clinic readers.
- Privacy: an on-demand explanation of the exact data collected and email purpose.

The signup includes a short note about progress and launch updates. A compact three-question FAQ
below it covers audience, the initial product focus, and availability with native expandable answers.
No repeated geography, manifesto, empty specimen labels, fake customers, or ornamental metric rows.

## Visual system

- Ivory `#f4f2e9`, forest `#193a30`, orange `#ef865b`, sage `#e4e7d9`.
- Newsreader for display typography (replaced Fraunces, whose hooked lowercase f read as odd), DM Sans for controls and text. Fonts are self-hosted by Next.js.
- Deliberately staggered display lines; the tooth and type share space rather than occupy boxed columns.
- Orange marks the wordmark period, pre-launch indicator and signup action.
- Thin rules and generous space. The signup band is the one panel on the page. No glass cards, gradient headings, sticky signup overlays, scroll hijacking or continuous motion.
- Mobile rearranges the composition while preserving readable type, natural scrolling and visible controls.

## Light and material (2026-09-22)

The owner asked for texture and light across the whole site, not one flat colour. The page is a sheet
of cotton paper in a sunlit room:

- One light source. Afternoon window light enters from the upper left. The tooth's key light, its cast
  shadow and the page light all agree on that direction.
- Paper: a faint tiled grain (`public/paper.svg`) that scrolls with the content.
- Window light: one fixed layer (`.room-light`) drawn over everything printed on the page with plain
  transparency, not a blend mode, so scrolling stays cheap.
  - The sunlit panes are fully clear, so every brand colour shows exactly as printed.
  - Shade is a cool dark `#232a2e` at 10% opacity, never green, so sage surfaces keep their colour.
    It falls in the window-bar and leaf shadows; the wide composition adds a soft wedge at the far left.
  - `--muted` text holds AA contrast even in the deepest shade (`scripts/site-contrast.py`).
  - The layer stays put while the paper scrolls beneath it, so the page changes as you move through it
    without any autonomous motion.
  - Wide and tall compositions (`light-wide.svg`, `light-tall.svg`) switch at a 1:1 aspect ratio.
- The art fades to clear at its bottom edge. Full-page captures show no seam when the art fits the
  viewport height (1440×900, 1024×768 and phones). On other aspect ratios the art is cropped at the
  viewport, so captures show a seam at that height. Visitors never see this seam.
- Dialogs sit in the top layer above the light, like sheets lifted into it.
- Section rules are creases: a hairline with light catching its lower lip.
- One page-load moment: the daylight fades in with the headline and sculpture. Reduced motion shows it at once.
- Printed things (type, outlines, rules) stay flat ink; the tooth is the object that casts a shadow.

## Interaction and access

Tooth: drag horizontally (mouse can also tilt vertically), use arrow keys, or press Home to reset. The
“X-ray” toggle (aria-pressed; the label never changes) turns the whole page into a radiograph; see X-ray mode.
Native dialogs support Escape, modal focus handling and close buttons. Email has an accessible label,
announced errors, preserved values on failure, a disabled pending button and an announced success state.
Motion honors the OS preference; important copy is never gated behind an animation.

## X-ray mode (2026-09-22)

The owner asked for the X-ray button to change the look of the whole site and to hide easter eggs in it.
The page becomes a radiograph on a lightbox, built on one rule: density decides brightness.

- Film: the forest ink turned to film base (`#0e1f19`). Printed matter is radiopaque bone (`#e6ece3`). The
  orange accents become metal, the brightest marks on the film, as restorations are on a real radiograph.
- Display type (headline, footer wordmark) renders like the tooth: faint mass, density building toward the
  outline, a bright rim and halation (`site/components/xray-filters.tsx`). The headline adds light where
  it crosses the tooth, like superimposed structures.
- Room: film grain replaces the cotton grain, and a lightbox glows behind the film instead of window light
  falling on it. The signup band becomes a soft-tissue shadow. Layout, copy and controls never change.
- Entry: a panoramic sweep. A bright beam carries the new exposure across the page from left to right, the way
  a panoramic unit's arm builds its image (View Transitions, 950 ms). Exit: the film fades away in 350 ms.
  Reduced motion or no View Transition support: instant.
- Easter eggs, found by play and never required:
  - A skeletal hand replaces the pointer cursor on clickable things.
  - Leaving the tooth's back to the viewer means the film went in backwards. Its lead backing prints a
    herringbone over the film, with the note “Film’s in backwards. That’s its lead backing.”
  - Five exposures within 20 seconds bring the dentist's radiation rule: “Five exposures. Dentists keep doses
    as low as reasonably achievable.”
  The X-ray button sits in the site header, left of the launch status. Notes stay beside the tooth (top right on desktop, below it on phones) in a `role="status"` region and clear when X-ray turns off.
- Styles live in `site/app/xray.css` under `:root[data-xray]`. A colour added to `globals.css` needs a token
  or a matching X-ray rule, or it prints dark on the film. Contrast is checked by `scripts/site-contrast.py`.
  Screens and behaviour checks: `scripts/site-xray.py`.

## Artwork provenance and performance

The tooth mesh is generated locally with implicit ellipsoid surfaces and marching cubes using Three.js,
Taubin-smoothed, with baked occlusion and wall thickness, plus a separate pulp and canal mesh for the X-ray.
The enamel is procedural: an ivory crown that shifts into a warmer root at a scalloped cervical line, fine
growth ridges and faint translucency at thin edges. A soft shadow falls on an invisible floor.
No third-party scan, photo, patient data or external 3D asset was used. The SVG fallback is also original.
See `site/scripts/build-tooth.mjs` (shapes in `tooth-field.mjs`) for the reproducible source. The model is
stylized, not anatomical guidance. The room's paper and window light are also procedural, generated by
`site/scripts/build-room.mjs`. So are the X-ray film grain and herringbone; the skeletal hand cursor
(`site/public/xray-hand.svg`) is an original drawing. The renderer is imported lazily, capped at 1.75 device pixels, draws only
when necessary and disposes GPU resources.

## Research applied

- [NN/g: Homepage usability](https://www.nngroup.com/articles/113-design-guidelines-homepage-usability/):
  recognizable identity, clear purpose and a small set of meaningful actions. These are usability
  principles, not a prescribed section template.
- [web.dev: High-performance animation](https://web.dev/articles/animations-guide): transform/opacity
  for small entrance transitions; no constant layout animation.
- [web.dev: Reduced motion](https://web.dev/articles/prefers-reduced-motion): no entrance motion or
  rotational easing when the visitor requests reduced motion.
- [Three.js documentation](https://threejs.org/docs/): physical material, environment lighting and resource disposal.

## Publication dependencies

No public mailing address is available, per the owner. Resolve sender information before live launch.
Resend contact storage and the production domain must be configured and verified separately from local UI verification.

The social sharing image (`site/app/opengraph-image.png`) is an export of this same original
sculpture and page typography, captured locally with `scripts/site-social.py`; no external media was used.

## Footer refinement

The owner requested the oversized footer back. The public page now ends with a large lowercase
Ophi wordmark and the orange asterisk, plus a compact contact row, back-to-top link and privacy control.
The contact action copies hello@ophi.app directly; it never opens a form or mail client. The same copy
control sits with the FAQ (“Anything else? Write to us.”): under the heading on wide screens, after the
questions on phones. It follows the questions in the markup, so reading and focus order match both layouts.

## Signup band (2026-09-22)

The introduction and signup share one sage band below the poster, so the one action reads as one unit.
Two columns on shared grid rows: the introduction and “Why Ophi?” on the left; the heading, note and form
on the right, with the pill aligned to the email field. Controls inside the band take the paper tone.
Contact moved out of the band into the FAQ, keeping the band to a single action. The owner chose this
from seven live layouts (single column, standalone band, sentence form, two columns, and band combinations).

After joining (2026-09-22, owner pick from three live variants): the result takes over the email pill in place, level
with “Why Ophi?”. The orange join button closes into a circle, ink fills it from the centre and a check draws: the
“Copied” done tag, earned. The typed address fades out; “You’re on the list.” writes in where it sat. Below: “We’ll write to you at
…” with the address (true for repeat signups too, so the page never reveals who is already listed), then one secondary pill to the clinic survey. With the first action done, the survey is the
band’s one next step, and it keeps the band close to its signed-out height. While joining, the join pill stays solid and
its arrow leaves and returns. A first signup also gets a welcome email in the same paper, ink and orange
(`site/lib/confirmation-email.ts`) that repeats the survey invitation.
Phones split the band differently; see Phone layout.

## Phone layout (2026-09-22)

Stacked on a phone (≤700px), the two-column band read as intro, secondary pill, then a heading mid-card.
Phones now follow reading order. Wider screens are unchanged, pixel for pixel.

- Headline, then standfirst: the introduction and “Why Ophi?” sit on bare paper right under “Less
  paperwork.”, aligned to the page frame. The sage band holds the signup alone, heading first.
- FAQ: heading, questions, then “Anything else? Write to us.” and the copy pill.
- Footer: privacy pill left, back-to-top as a round 40px button right (its label stays for screen
  readers), copyright last. The two pills used to stack unevenly at 360px and below.
- Fields show their prompts whole. Typed email stays 16px (no iOS zoom) while its placeholder is 14px.
  The clinic-software trigger shows “Your clinic’s software (optional)”. At 345px and below the join
  arrow drops and the trigger tightens.
- Short paragraphs use `text-wrap: pretty`, so they don't end on a single word.

The owner picked this (“a”) from four live phone variants. The others: one band with the signup first,
the form in reading order with a full-width join button, and a right-set second headline line. Checks:
`scripts/site-mobile-fit.py` (prompts fit at 320–430px), `scripts/site-mobile-a11y.py` (names, tap
size, focus order, X-ray band), `scripts/site-diff.py` (before/after pixel diff per width).

## Control language (2026-09-22)

Every control is round. Primary: the orange join pill. Secondary actions (Why Ophi?, copy email, back to
top, privacy): an outlined pill ending in a sage tag that holds the icon. The source citation is a small sage
chip. No straight underline links. Icons are one drawn SVG family (`site/components/icons.tsx`, 1.4 stroke,
round caps); no Unicode glyph icons. Focus is a sage ring (`#6b8062`), never a dark outline. No visible scrollbars (owner preference). Motion is
short and settles with `--ease-out`: the listbox fades and rises into place, chevrons and plus icons rotate,
arrows nudge, back-to-top scrolls smoothly. Reduced motion removes all of it.

