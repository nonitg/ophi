import { describe, expect, it } from "vitest";
import sitemap from "./sitemap";
import { guides } from "@/lib/guides";

describe("sitemap", () => {
  it("lists the homepage and every guide so crawlers find them", () => {
    const urls = sitemap().map((e) => e.url);
    expect(urls[0]).toBe("https://ophi.app/");
    for (const g of guides) {
      expect(urls).toContain(`https://ophi.app/guides/${g.slug}`);
    }
  });
});