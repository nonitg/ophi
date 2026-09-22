# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Public site (`site/`): Next.js (App Router) on Vercel, shadcn/ui heavily customized, Resend for
waitlist contacts and newsletter sends. User declined Cloudflare (no Pages, no Turnstile) and
Buttondown. Bot defence is a honeypot field plus a server-side rate limit. The product app
(`colombus/web`, Flask + Jinja) is internal and not public.

## Users

Product users: office managers and treatment coordinators at Canadian dental clinics who assemble
CDCP preauthorizations, and the dentist-owners who sign them and carry the liability.

Waitlist site readers (confirmed 2026-09-21): a broad audience. Office managers, dentist-owners,
clinic staff, investors, and anyone interested in the CDCP preauthorization problem. The page must be
legible to a reader with no dental background.

## Product Purpose

Ophi is a CDCP preauthorization copilot. It reads the proposed crown and the patient's chart
from the practice management system, checks them against CDCP documentation rules, finds the
evidence already in the chart, names what is missing or stale with the clause that requires it, and
assembles the submission packet. Staff review and submit; Ophi never transmits. Success is fewer
incomplete submissions and fewer resubmissions per clinic.

## Positioning

Documentation completeness against a cited rule, never a prediction of payer behaviour. Every
finding points at a CDCP clause and a chart entry. A human is always the sender of record; CDAnet
prohibits non-certified software from submitting.

## Operating Context

Canadian dental clinics submit CDCP preauthorizations to Sun Life. Staff recall which codes need
preauth, hunt the chart for radiographs and perio charting, judge recency, write the narrative, and
assemble attachments. A resubmission goes to the back of the queue as a new request. Practice
management systems in play: ABELDent (dev sandbox only), ClearDent, Open Dental, Dentrix, Tracker,
others.

## Capabilities and Constraints

- v1 scope: crowns (27xxx) only. Endodontics next. Dentures out of scope.
- Local read-only agent on the practice server plus Canadian cloud. Outbound HTTPS only.
- No patient information anywhere public. The waitlist stores an email and an optional practice
  management software answer, nothing else.
- CASL applies to every send: express consent at signup, sender identity in the footer, unsubscribe
  link in every email.
- Undecided: launch timing, pricing, first paid PMS integration (waitlist PMS answers inform this).

## Brand Commitments

- Name: **Ophi**, standalone (renamed 2026-09-22). Public domain: **ophi.app**. No parent company shown. Ophi is the newsletter sender identity; public sender contact information is not yet available.
- Public posture pre-launch: **stealth** (confirmed 2026-09-21). Public surfaces state the problem
  only. No mechanism, no feature list, no screenshots, no claims about what the product does.
- Copy law, binding everywhere: never say approved, will be approved, eligible, or covered. Never
  state or imply an approval-rate improvement. Every number is cited to its public source.
- Public wordmark: lowercase **ophi.**, with an orange period. Public design: ivory, forest, orange, Newsreader and DM Sans; see `DESIGN.md`. The internal app’s utility skin is separate from the public identity.

## Evidence on Hand

- Health Canada CDCP preauthorization figures for Mar 1 to May 31 2026, as reported by Oral Health
  Group: 480,000 complete requests; 46% approved overall; crowns about 37%; root canals 44%; partial
  dentures over 76%; more than 95% processed within 7 days. Source confirmed 2026-09-21 (article by
  Dina Al-Shibeeb, 2026-06-18): https://www.oralhealthgroup.com/dental-governance-regulations/cdcp-update-less-than-half-of-dental-preauthorization-requests-approved-as-new-trends-emerge-1003996608/
- About 20% of submissions arrive incomplete. Health Canada and Sun Life name missing radiographs,
  insufficient clinical notes, and absent periodontal charting as causes (`PLAN.md`).
- Absent, must not be fabricated: customers, testimonials, pilots, partner logos, pricing, launch
  date, approval-rate outcomes, product screenshots.

## Product Principles

1. Say only what a cited rule or a public source supports.
2. The human stays the sender; the tool never acts on the payer.
3. Stealth hides the mechanism, not the problem: state the problem plainly enough for an outsider.
4. Collect the minimum: an email, and one optional answer that changes a product decision.
5. Every send is CASL-clean by construction.
