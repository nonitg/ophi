import type { Metadata } from "next";
import Link from "next/link";
import { JsonLd } from "@/components/json-ld";
import { guides } from "@/lib/guides";

export const metadata: Metadata = {
  title: "Ophi: guides for dental clinics and preauthorization",
  description:
    "Ophi’s guides on dental preauthorization for Canadian dental clinics — CDCP treatment preauthorization, wait times, and less paperwork.",
  alternates: { canonical: "/guides" },
};

export default function GuidesIndex() {
  return (
    <main className="mx-auto w-full max-w-2xl px-6 py-12 sm:py-16">
      <nav aria-label="Breadcrumb" className="mb-8 text-[12px]">
        <ol className="flex flex-wrap gap-x-2 text-muted">
          <li><Link href="/" className="hover:underline">Ophi</Link></li>
          <li aria-hidden="true">/</li>
          <li aria-current="page">Guides</li>
        </ol>
      </nav>
      <h1 className="text-[34px] leading-[1.1] tracking-[-1.2px] sm:text-[42px]">Guides for dental clinics</h1>
      <p className="mt-4 max-w-[54ch] text-[15px] leading-[1.7] text-muted">
        A few short guides on the paperwork dental clinics handle most — preauthorization, the CDCP, and how the process works.
      </p>
      <ul className="mt-10 grid gap-4">
        {guides.map((g) => (
          <li key={g.slug}>
            <Link href={`/guides/${g.slug}`} className="block rounded-[8px] border border-line bg-paper p-5 transition-[background] hover:bg-sage">
              <h2 className="text-[19px] leading-[1.3] tracking-[-.3px]">{g.title}</h2>
              <p className="mt-1.5 text-[13px] leading-[1.6] text-muted">{g.description}</p>
            </Link>
          </li>
        ))}
      </ul>
      <p className="mt-10 text-[13px] leading-[1.7] text-muted">
        Staying ahead of preauthorization paperwork?{" "}
        <Link href="/#join" className="text-ink underline decoration-pill-line underline-offset-4 hover:decoration-ink">Join the Ophi waitlist</Link>.
      </p>
      <JsonLd data={{ "@context": "https://schema.org", "@type": "CollectionPage", name: "Ophi: guides for dental clinics and preauthorization", url: "https://ophi.app/guides" }} />
      <JsonLd data={{ "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: [
        { "@type": "ListItem", position: 1, name: "Ophi", item: "https://ophi.app/" },
        { "@type": "ListItem", position: 2, name: "Guides", item: "https://ophi.app/guides" },
      ] }} />
    </main>
  );
}