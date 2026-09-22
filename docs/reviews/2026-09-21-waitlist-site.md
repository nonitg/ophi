# Review record: waitlist site (`site/`), 2026-09-21

Slice: public stealth waitlist page. Next.js App Router, shadcn base-nova re-cut, Resend, Vercel.
Direction: The Radiograph Lightbox (Impeccable seed 08a97fd0, chosen from the safer hand after
two user re-rolls). Contract in `.impeccable/surfaces/site-app-page-tsx.md`; product truth in
`PRODUCT.md`.

## Finish review (Impeccable finish reviewer, fresh context)

First pass, disposition **fix**, seven material items: film read as a glowing card, statement not
at display scale, footer contact omitted instead of marked, mobile orphaned "37.", ID dot read as a
bead, error state broke row alignment, source URL unconfirmed. All seven applied in one batch and
recaptured (desktop 1440, mobile 390, error and success states).

Verdict pass: **all seven resolved, no regressions, disposition ship.** Scope of the ship: the
seven scored fixes and the recaptures, not a fresh whole-surface review.

## Code review (feature-dev code reviewer, fresh context)

- **Important, fixed:** honeypot field named `website` is autofilled by browsers and password
  managers, which would flag real visitors as bots and silently drop their signup. Renamed to
  `hp_ref` (`HONEYPOT_FIELD` in `site/lib/subscribe.ts`), comment explains the constraint.
- **Coverage, fixed:** the server action had no test. Added `site/app/actions.test.ts` with Resend
  and `next/headers` mocked: happy path stores email plus PMS property; bot path returns success
  without calling Resend. `vitest.config.ts` mirrors the `@/` alias.
- Confirmed correct: Resend SDK 6.x `contacts.create` shape (no deprecated `audienceId`), no key
  exposure to the client, no-JS form post works, copy law holds in `lib/copy.ts`.
- Accepted as known limits: in-memory rate limiter does not evict; duplicate-contact error text
  matched by regex, unverified against Resend's actual message.

## Mechanical checks

Impeccable detector over all seven UI files: no findings. Design hook: no findings on any edit.
`tsc`, `eslint`, `vitest` (5 tests) and `next build` all pass.

## Owed before publish

Footer mailing address (CASL), Resend contact property `pms`, public domain, Vercel Pro plan.
