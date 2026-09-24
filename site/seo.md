# Ophi SEO plan

Goal: rank for **Ophi**, **preauthorization**, **dental clinics**, and combinations of those,
without changing a word the reader sees on the landing page. Everything below is metadata, structured
data, or new pages the landing page never links to.

## What changed (invisible to users)

| Change | Location | Why |
| --- | --- | --- |
| Keyword-rich `<title>` and meta description | `lib/copy.ts` → `app/layout.tsx` | SERP/tab title now targets "Ophi · dental preauthorization · clinics" |
| `keywords`, `application-name`, `robots: index, follow` | `app/layout.tsx` | Explicit crawl/index signals for every page |
| OG + Twitter image tags | `app/layout.tsx` | Share cards now include the 1200×630 `opengraph-image.png` |
| Homepage JSON-LD | `app/page.tsx` via `components/json-ld.tsx` | `Organization`, `WebSite`, `SoftwareApplication`, and `FAQPage` (built from the visible FAQ, so rich results stay honest) |
| `robots.txt` | `app/robots.ts` | Allows crawling, points at the sitemap |
| `sitemap.xml` | `app/sitemap.ts` | Lists the homepage + every guide (this is how crawlers discover the hidden pages) |
| Web manifest | `app/manifest.ts` | Site identity for mobile/installed contexts |

**One visible-browser exception (flagged):** the `<title>` changed, so the browser tab now reads
"Ophi — Dental preauthorization for clinics" instead of "ophi.". Landing-page text is untouched —
the logo/wordmark is hardcoded in `app/page.tsx` and was not edited.

## Hidden `/guides` pages (no links from the visible site)

Route `app/guides/[slug]/page.tsx` + hub `app/guides/page.tsx`, content in `lib/guides.ts`.
Crawlers reach them via the sitemap; users can't navigate to them from the landing page.
They cross-link each other and funnel to `/#join` (the existing waitlist).

Every guide is static, zero-JS, semantic HTML (works in all browsers, crawler or reader), with
per-page `generateMetadata` (title, description, keywords, canonical, OG/Twitter) and JSON-LD:
`Article`, `BreadcrumbList`, and `FAQPage` where the page has FAQ. Unknown slugs return 404.

| Slug | Target terms |
| --- | --- |
| `/guides/dental-preauthorization` | dental preauthorization |
| `/guides/dental-preauthorization-for-clinics` | dental preauthorization + dental clinics |
| `/guides/cdcp-treatment-preauthorization` | CDCP / treatment preauthorization / Canada |
| `/guides/dental-preauthorization-wait-times` | preauthorization + wait times |
| `/guides/preauthorization-vs-predetermination` | preauthorization vs predetermination |
| `/guides/ophi-for-dental-clinics` | Ophi + dental clinics + preauthorization |
| `/guides/dental-clinic-administration` | dental clinic + administration + preauthorization |
| `/guides` (hub) | Ophi + guides index |

Content rules: factual, pre-launch honest. The only statistic reused is the CDCP figure already
cited on the homepage (`lib/copy.ts` `source`); nothing was invented.

## Honest tradeoffs (decided)

1. **Hidden pages get little link equity.** No dead link "leaks" the real tradeoff out to users:
   pages with no internal links rank slower than linked ones. Mitigations used: sitemap, guide-to-guide
   links, hub page, static prerendering. A footer "Guides" link would help rankings but adds visible UI —
   punted, per the no-visible-change requirement.
2. **Doorway-page risk.** Pure keyword pages can read as doorway pages. This content is genuine and
   consistent with the site's stated problem domain, which reduces that risk.
3. **Tab title change** was accepted as the one visible tradeoff (see above).

## Verification

- `pnpm typecheck` (requires `.next/types` — run `pnpm exec next typegen` first)
- `pnpm lint`, `pnpm test`, `pnpm build`
- Tests: `lib/guides.test.ts` (slugs unique, content complete, related links exist, SERP-safe
  descriptions, target terms covered), `app/sitemap.test.ts` (home + every guide listed)
- Browser (Playwright): landing page text byte-identical, guides render at desktop + mobile, HTML
  contains full metadata. `robots.txt`, `sitemap.xml`, `manifest.webmanifest` all serve.

## Maintenance

- New guide: add an entry to `lib/guides.ts`; the page, metadata, sitemap, JSON-LD, and tests pick it up.
- Changing the visible FAQ: keep `lib/copy.ts` `faq` in sync with `app/page.tsx` so `FAQPage` markup
  never describes different text than the page shows.
- Baseline commands that must stay green: `pnpm typecheck && pnpm lint && pnpm test && pnpm build`.