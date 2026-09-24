import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { JsonLd } from "@/components/json-ld";
import { findGuide, guides } from "@/lib/guides";

// Static, zero-JS semantic HTML: renders in every browser, crawler and reader alike.
export const dynamicParams = false;

export function generateStaticParams() {
  return guides.map((g) => ({ slug: g.slug }));
}

type Props = { params: Promise<{ slug: string }> };

const canonical = (slug: string) => `https://ophi.app/guides/${slug}`;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const guide = findGuide(slug);
  if (!guide) return {};
  const url = canonical(guide.slug);
  return {
    title: guide.title,
    description: guide.description,
    keywords: guide.keywords,
    alternates: { canonical: url },
    openGraph: { title: guide.title, description: guide.description, url, type: "article" },
    twitter: { card: "summary_large_image", title: guide.title, description: guide.description },
  };
}

export default async function GuidePage({ params }: Props) {
  const { slug } = await params;
  const guide = findGuide(slug);
  if (!guide) notFound();
  const url = canonical(guide.slug);
  const related = guide.related.map(findGuide).filter((g) => g !== undefined);
  return (
    <main className="mx-auto w-full max-w-2xl px-6 py-12 sm:py-16">
      <nav aria-label="Breadcrumb" className="mb-8 text-[12px]">
        <ol className="flex flex-wrap gap-x-2 text-muted">
          <li><Link href="/" className="hover:underline">Ophi</Link></li>
          <li aria-hidden="true">/</li>
          <li><Link href="/guides" className="hover:underline">Guides</Link></li>
          <li aria-hidden="true">/</li>
          <li aria-current="page">{guide.title}</li>
        </ol>
      </nav>
      <article>
        <h1 className="text-[34px] leading-[1.1] tracking-[-1.2px] sm:text-[42px]">{guide.title}</h1>
        <p className="mt-4 text-[15px] leading-[1.75] text-ink-soft">{guide.lede}</p>
        {guide.sections.map((section) => (
          <section key={section.heading} className="mt-9">
            <h2 className="text-[22px] leading-[1.25] tracking-[-.4px]">{section.heading}</h2>
            {section.paragraphs.map((p, i) => (
              <p key={i} className="mt-3 text-[15px] leading-[1.75] text-ink-soft">{p}</p>
            ))}
          </section>
        ))}
        {guide.faq && (
          <section className="mt-10 border-t border-line pt-7">
            <h2 className="text-[22px] leading-[1.25] tracking-[-.4px]">A few quick answers</h2>
            {guide.faq.map(({ q, a }) => (
              <details key={q} className="border-line not-first:border-t">
                <summary className="flex min-h-12 list-none items-center py-3 text-[14px]">{q}</summary>
                <p className="pb-4 text-[13px] leading-[1.7] text-muted">{a}</p>
              </details>
            ))}
          </section>
        )}
        <div className="mt-10 rounded-[8px] bg-sage p-6">
          <h2 className="text-[19px] leading-[1.3] tracking-[-.3px]">Hear when Ophi is ready</h2>
          <p className="mt-1.5 text-[13px] leading-[1.7] text-muted">
            Join the waitlist for a first look at what we’re building for dental teams.
          </p>
          <Link className="mt-4 inline-block rounded-full bg-ink px-4 py-2 text-[12px] text-paper" href="/#join">Join the waitlist</Link>
        </div>
        {related.length > 0 && (
          <nav className="mt-10" aria-label="Related guides">
            <h2 className="text-[13px] font-medium tracking-wide text-muted uppercase">Keep reading</h2>
            <ul className="mt-3 grid gap-2">
              {related.map((g) => (
                <li key={g.slug}>
                  <Link href={`/guides/${g.slug}`} className="text-[14px] underline decoration-pill-line underline-offset-4 hover:decoration-ink">{g.title}</Link>
                </li>
              ))}
            </ul>
          </nav>
        )}
      </article>
      <JsonLd data={{ "@context": "https://schema.org", "@type": "Article", headline: guide.title, description: guide.description, url, inLanguage: "en-CA", author: { "@type": "Organization", name: "Ophi" }, publisher: { "@type": "Organization", name: "Ophi", url: "https://ophi.app/" } }} />
      <JsonLd data={{ "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: [
        { "@type": "ListItem", position: 1, name: "Ophi", item: "https://ophi.app/" },
        { "@type": "ListItem", position: 2, name: "Guides", item: "https://ophi.app/guides" },
        { "@type": "ListItem", position: 3, name: guide.title, item: url },
      ] }} />
      {guide.faq && (
        <JsonLd data={{ "@context": "https://schema.org", "@type": "FAQPage", mainEntity: guide.faq.map(({ q, a }) => ({ "@type": "Question", name: q, acceptedAnswer: { "@type": "Answer", text: a } })) }} />
      )}
    </main>
  );
}