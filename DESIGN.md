# Ophi — public site design

Updated 2026-11-12 (one system; see below). Earlier: 2026-09-22, which superseded the radiograph lightbox and the earlier multi-section landing-page draft.
Public brand: **Ophi**, wordmark **ophi.**, domain **ophi.app**. The existing internal code/package paths
are not part of the public brand and were not migrated in this design task.

## Intent

A compact editorial poster for a company taking dental paperwork seriously. The page should feel
warm, curious and deliberate. One composition contains the entire first impression: “Good care.
Less paperwork.”, an original enamel sculpture, a brief statement of purpose and signup.

The user liked the ivory/forest/orange language and sculpture but rejected the conventional
headline → facts → chart → call-to-action stack. Keep the language; break the layout pattern.

## One system (2026-11-12, second pass)

The owner rejected the first vision site as "messy, hard to understand and read" and asked for "one cohesive
experience" with direction. Its fault was the rule it was built on: every section invented its own kind of picture
(cards, a bar chart, a tree, a pinned phone scene, a dot field, a staircase, struck-through lines), under window-light
shadows, in four type styles. Thirteen screens of patchwork. This pass keeps the story and replaces the patchwork with
one system. Where this section and older ones disagree, this one wins.

**The rule: one motif, one card, one type scale, one way to open a section.**

- **Motif: the thread.** A patient's care as a line of steps marked done, booked, planned or waiting
  (`components/thread.tsx`, marks in `care-mark.tsx`). Every picture is that thread seen from somewhere: each patient's
  care in the hero card, the record vs. what Alex knows, the memory in the diagram, the personal page in the story, one mini thread
  per patient in the clinic view, and the front desk's stops laid on their side.
- **Surfaces.** Plain ivory page (no grain, no window light). One card: warm white `#fffdf8`, radius 28, soft shadow
  from above (`card` in `components/type.ts`). Sage for quiet inner surfaces and the signup panel. Forest for the
  story band and the Ophi node only. Orange for actions and "next / waiting".
- **Type.** Newsreader for headings and Ophi's spoken words, DM Sans for everything else. Six roles in
  `components/type.ts`; nothing under 14px. No monospace, no staggered or italic headline tricks.
- **Sections** open the same way (`components/section-head.tsx`): one heading that carries the idea, one sentence
  under it, then one picture. Left-aligned on one 1240px frame, one gap above each (`section` in `type.ts`), never
  padding below, so neighbours can't double up.
- **One patient, one source.** Every picture of Alex is cut from the story's data (`lib/story.ts` `frameAt`), and the
  clinic view's patients from `lib/team.ts`, so names, steps and dates always agree. The hero's three conversations
  (`lib/hero.ts`) reuse both; `lib/hero.test.ts` holds them to the clinic view.
- **Motion.** Blocks rise in once as they arrive (`components/reveal.tsx`, `.js [data-reveal]`); the product
  pictures work while on screen (the hero's patients take turns, the system diagram plays its moments, the gap's
  fixes arrive, the story plays, clinic rows update). Reduced motion shows every final state.

Motion: one language, in `components/motion.tsx` (springs, the soft ease, `Swap`/`Fade` for text changing in place,
the call's voice bars and text bubbles). Things morph rather than switch: the old leaves before the new arrives, text
crossfades in place, and the care mark (`components/care-mark.tsx`) springs between states. Fixed heights, so nothing
shifts; paused off screen; reduced motion shows a finished still.

Reading order:

1. **Hero.** "The front desk, handled." (2026-11-20, owner: the whole front desk is the first thing the page says;
   voice is one part of it. Was "One assistant for every patient.") Non-breaking spaces keep "The front desk," on
   one line; `display` tops out at 80px so it fits beside the stage. Plain sentence naming the whole job, Get early access plus "See how it works" (jumps to How,
   which plays as it comes into view), "Built in Canada" (the pilot-status line was removed by the owner,
   2026-11-14). Beside it, a phone on a sage disc (`components/hero-stage.tsx`, data in `lib/hero.ts`): four patients
   take turns, each a different front-desk job (Alex calls to move "it", Priya texts to ask if soreness after her
   filling is normal and is answered from Dr. Shah's notes, Chloé books from her page, Owen calls about his insurance
   estimate). Priya is the one hero patient not in the clinic view.
   A floating card reads "X's care, from your records" and a dark toast says what Ophi wrote back. The old screen
   leaves before the new one rises in; the stage is a fixed height, so nothing below moves. (2026-11-14: picked by
   the owner over a tabless card; replaced the tabbed hero card. The "Hear Ophi take a real call" button was removed
   the same day: both voices in that recording are generated, so it isn't a real call. The owner picked "See how it
   works" over an inline email field and a list of reassurances.)
2. **Front desk.** "Every job at the front desk." The old roadmap, moved up and told in the present tense (owner,
   2026-11-20: "make it sound like we have all of it"; voice is one way a patient reaches the clinic, not the
   product). A row of door chips (Phone call, Text, Their own page), then the thread on its side with five jobs: New
   patients (lead follow-up), Questions (answered from the chart), Scheduling, Insurance, Follow-up (after treatment,
   then the next recommended treatment). Each has a dark done mark; then what stays with the team
   (`components/front-desk.tsx`). The clinic view's Nadia is now a website enquiry Ophi followed up.
3. **How.** "Call, text or tap. It all lands in one place." Straight after the hero, so the page says what Ophi is
   before it argues why (owner, 2026-11-12: "take the focus back to Ophi"). One big card, "Alex's care"
   (`components/how-thread.tsx`, states from `lib/story.ts`): five steps of the crown in large serif type on the
   thread. Each door arrives as a small object (their page, the clinic's records, a text, a call), docks beside the
   step it changes (from the side on wide screens, from above on narrow ones) and folds into it; the mark springs to
   its new state, the step keeps that door's icon, and the card's footer ticks "Saved to your record system".
   (2026-11-14: the owner picked this over an app-window product shot; it replaced a patients → Ophi box → records
   diagram that read as "too much… not visually appealing". Box-and-line diagrams were rejected as not beautiful
   enough.)
4. **Why.** "Care takes many steps. Today, your patient sees one." "What Alex knows today": the same plan with all
   but one step out of focus ("To learn the rest, Alex has to call.") (`components/gap.tsx`). Then 31 in 100 calls
   (dots) and 1 in 5 adults (people), each with a "With Ophi" card under it. The "with Ophi" plan card was cut when
   How started showing every step with its door.
5. **One patient.** The dark band, fits a 900px screen. Six moments of Alex's crown as a step list beside Alex's
   phone; it plays itself while on screen, a picked moment plays and stays, and it can be paused. Under 900px the
   phone comes first, then the moment and a dot bar. The real recording plays from the call screen.
6. **For clinics.** "Your team sees every patient. You decide what needs a yes." The clinic table with tallies,
   rows that change, and a working Approve.
7. Signup panel, questions, footer wordmark.

**Reader tests (2026-11-12, second pass: an office manager on desktop, an owner-dentist on a phone, a design critic,
a Web Interface Guidelines audit).** What changed because of them: Alex's four pictures disagreed on step names and
dates (now one source); the story was taller than the screen and changed off-screen on phones; grey placeholder bars
read as "still loading" (now blur); "Not a phone bot, a reminder tool and a portal" read as the opposite; orange did
six jobs; the privacy pop-up contradicted itself; live regions announced the self-playing demos; the sticky header
covered focused controls; Approve dropped focus. Still missing for both readers, and waiting on the owner: who is
behind Ophi, price or pilot terms, a real clinic.

Removed: the tooth and X-ray mode (the files stay in `components/` for the owner to restore or delete), the window
light and paper grain, "What Ophi is not" (its one useful line is an FAQ answer), the separate "Works with" section
(folded into How), the left-to-right doors diagram and then the tasks/patient panels (both replaced by the system
diagram), the record-system name chips (the FAQ answers which software works).

**Claims.** The page presents Ophi as the whole front desk (owner, 2026-11-20), including things not true of the
product today: lead follow-up, post-treatment follow-up, chart-based answers to symptom questions, insurance
estimates, preauthorizations and claims; record systems other than ABELDent
are not connected, though the FAQ says Ophi works inside the clinic's own; and the FAQ says patient data lives in Canada
under Canadian health privacy law, while the demo server is in the US. Revisit both before the site is public.

Checks: `scripts/site-widths.py` (20 widths: overflow, text leaving its section, the 14px floor),
`scripts/site-vision-flow.py` (door tabs, story autoplay, real call, step buttons, Approve, FAQ) and
`scripts/site-phone-flow.py` (390x750 touch: menu, hero holds still, How and the story each fit one screen, swipe,
all clinic patients, Approve).

### Phones and tablets (2026-11-15)

The rule: a phone gets the same story, the same pictures and the same content as a desktop, rearranged so each moving
picture fits one phone screen (about 690px under the header), so the reader sees cause and effect together.

- **Header.** Below 1100px the section links fold into a menu button beside Get early access
  (`components/site-menu.tsx`): big serif links drop under the header; a pick, a tap outside or Escape closes it.
- **Hero.** Under 480px the two buttons stack full width at 52px. The patient dots return under the cards.
- **How.** Below 1240px the doors' waiting room is shorter (200px, 176px on phones) and each door's object rests on
  the card's top edge, growing upward. Phone rows are 64px, so the doors, every step and "Saved" fit one screen. The
  thread is measured from the first mark to the last, so any row height works.
- **Story.** Under 900px it reads like a story on a phone: the six bars, the moment's words (no number; the bars count),
  then Alex's phone. A sideways swipe on the phone changes moment; vertical drags still scroll.
- **Clinic.** Phones show all six patients (two of the four live events land on the last two). Below 1100px "What
  Ophi did" sits ticked under each row's next step instead of in its own column.

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
- Newsreader for display typography (replaced Fraunces, whose hooked lowercase f read as odd), DM Sans for controls and text. Fonts are self-hosted by Next.js. Newsreader ships only its weight-400 instance (upright and italic, optical size kept), so display type stays at 400; another weight would need its own file.
- Deliberately staggered display lines; the tooth and type share space rather than occupy boxed columns.
- Orange marks the wordmark period, pre-launch indicator and signup action.
- Thin rules and generous space. The signup band is the one panel on the page. No glass cards, gradient headings, sticky signup overlays, scroll hijacking or continuous motion.
- Mobile rearranges the composition while preserving readable type, natural scrolling and visible controls.

## Styling (2026-09-23)

Tailwind v4 utilities in the markup. `site/app/globals.css` holds the tokens, element defaults, keyframes, the
window light and the custom variants: `wide` (≥1600px), `tablet` (≤1100px), `phone` (≤700px), `phablet`
(480–700px), `narrow` (≤479px), `small` (≤360px), `tiny` (≤345px) and `xray`. Secondary pills share
`site/components/pill.ts`. A few semantic class names stay in the markup as hooks for scripts and code. Refactors
that should not change the look are checked with `scripts/site-parity.py` (every breakpoint edge and state).

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
  The X-ray button sits in the site header, left of the launch status. Notes stay beside the tooth (top right on desktop; on phones beside “Less”, above “paperwork.”) in a `role="status"` region and clear when X-ray turns off.
- Tokens flip in `site/app/xray.css` under `:root[data-xray]`, which also holds the page-level film (body,
  lightbox, cursor, sweep). Each component's own X-ray look is an `xray:` utility in its markup. A paper-only
  colour (an arbitrary value or a static `@theme` colour) needs an `xray:` counterpart, or it prints dark on the
  film. Contrast is checked by `scripts/site-contrast.py`.
  Screens and behaviour checks: `scripts/site-xray.py`.

## Artwork provenance and performance

The tooth mesh is generated locally with implicit ellipsoid surfaces and marching cubes using Three.js,
Taubin-smoothed, with baked occlusion and wall thickness, plus a separate pulp and canal mesh for the X-ray.
The enamel is procedural: an ivory crown that shifts into a warmer root at a scalloped cervical line,
smooth-shaded with faint translucency at thin edges. No per-pixel bump detail: at screen density it aliased into visible squares. A soft shadow falls on an invisible floor.
No third-party scan, photo, patient data or external 3D asset was used. The SVG fallback is also original.
See `site/scripts/build-tooth.mjs` (shapes in `tooth-field.mjs`) for the reproducible source. The model is
stylized, not anatomical guidance. The room's paper and window light are also procedural, generated by
`site/scripts/build-room.mjs`. So are the X-ray film grain and herringbone; the skeletal hand cursor
(`site/public/xray-hand.svg`) is an original drawing. The renderer is imported lazily, capped at 1.75 device pixels, draws only
when necessary and disposes GPU resources. The mesh ships quantized and gzipped (about 170 KB) and downloads alongside three.js.

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
questions on phones. It follows the questions in the markup, so screen readers and Tab reach it after them; on
wide screens focus then steps back left to it, under the heading.

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
its arrow leaves and returns. A first signup also gets a welcome email
(`site/lib/confirmation-email.ts`) that repeats the survey invitation. It is deliberately unbranded: a plain note from a
named person, with a text link and no layout, colour or button, so Gmail files it in Primary rather than Promotions.
Phones split the band differently; see Phone layout.

## Phone layout (2026-09-22)

Stacked on a phone (≤700px), the two-column band read as intro, secondary pill, then a heading mid-card.
Phones now follow reading order. Wider screens are unchanged, pixel for pixel.

- Headline, then standfirst: the introduction and “Why Ophi?” sit on bare paper right under “Less
  paperwork.”, aligned to the page frame. The sage band holds the signup alone, heading first.
- FAQ: heading, questions, then “Anything else? Write to us.” and the copy pill.
- Footer: privacy pill left, back-to-top as a round 40px button right (its label stays for screen
  readers), copyright last. The two pills used to stack unevenly at 360px and below.
- Fields show their prompts whole once the page hydrates (before that, the native select shows the long
  prompt). Typed email stays 16px (no iOS zoom) while its placeholder is 14px. The clinic-software
  trigger shows “Your clinic’s software (optional)”. At 345px and below the join arrow drops and the
  trigger tightens.
- “Less” sits over “paperwork.” at every phone width. In X-ray the tooth's notes sit beside “Less”,
  where the film is bare. The gap under the headline now belongs to the introduction.
- Short paragraphs use `text-wrap: pretty`, so they don't end on a single word.

The owner picked this (“a”) from four live phone variants. The others: one band with the signup first,
the form in reading order with a full-width join button, and a right-set second headline line. Checks:
`scripts/site-mobile-fit.py` (prompts fit at every width 320–700px), `scripts/site-mobile-a11y.py` (names,
tap size, focus order, X-ray band), `scripts/site-xray-note.py` (notes clear the headline and introduction),
`scripts/site-faq-overlap.py` (questions stay above the copy pill at 701–780px), `scripts/site-diff.py`
(before/after pixel diff per width). A fresh-context review caught the note clash, a 361px clip and the
701–770px paint order; all three are fixed.

## Control language (2026-09-22)

Every control is round. Primary: the orange join pill. Secondary actions (Why Ophi?, copy email, back to
top, privacy): an outlined pill ending in a sage tag that holds the icon. The source citation is a small sage
chip. No straight underline links. Icons are one drawn SVG family (`site/components/icons.tsx`, 1.4 stroke,
round caps); no Unicode glyph icons. Focus is a sage ring (`#6b8062`), never a dark outline. No visible scrollbars (owner preference). Motion is
short and settles with `--ease-out`: the listbox fades and rises into place, chevrons and plus icons rotate,
arrows nudge, back-to-top scrolls smoothly. Reduced motion removes all of it.

