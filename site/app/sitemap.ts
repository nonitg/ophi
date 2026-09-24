import type { MetadataRoute } from "next";
import { guides } from "@/lib/guides";

// Everything crawlers should know about. The /guides pages have no in-page links —
// this sitemap is how search engines discover them.
export default function sitemap(): MetadataRoute.Sitemap {
  const guideEntries: MetadataRoute.Sitemap = guides.map((g) => ({
    url: `https://ophi.app/guides/${g.slug}`,
    lastModified: new Date(),
    changeFrequency: "monthly",
    priority: 0.7,
  }));
  return [
    { url: "https://ophi.app/", lastModified: new Date(), changeFrequency: "weekly", priority: 1 },
    { url: "https://ophi.app/guides", lastModified: new Date(), changeFrequency: "monthly", priority: 0.8 },
    ...guideEntries,
  ];
}