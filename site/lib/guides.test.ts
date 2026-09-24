import { describe, expect, it } from "vitest";
import { findGuide, guides } from "./guides";

describe("guides", () => {
  it("provides unique slugs with complete content", () => {
    const slugs = guides.map((g) => g.slug);
    expect(new Set(slugs).size).toBe(slugs.length);
    for (const g of guides) {
      expect(g.title.length).toBeGreaterThan(10);
      expect(g.lede.length).toBeGreaterThan(0);
      // Meta descriptions should stay in SERP-display range.
      expect(g.description.length).toBeLessThanOrEqual(165);
      expect(g.keywords.length).toBeGreaterThan(0);
      expect(g.sections.length).toBeGreaterThan(0);
      for (const s of g.sections) {
        expect(s.heading.length).toBeGreaterThan(3);
        expect(s.paragraphs.length).toBeGreaterThan(0);
      }
    }
  });

  it("covers the target search terms across titles and descriptions", () => {
    const text = guides.map((g) => `${g.title} ${g.description}`.toLowerCase()).join(" ");
    expect(text).toContain("preauthoriz");
    expect(text).toContain("clinic");
    expect(text).toContain("cdcp");
  });

  it("only links guides that exist", () => {
    for (const g of guides) {
      for (const slug of g.related) {
        expect(findGuide(slug), `${g.slug} links to missing ${slug}`).toBeDefined();
      }
    }
  });

  it("finds a guide by slug, unknown slugs come up empty", () => {
    expect(findGuide("ophi-for-dental-clinics")?.title).toContain("Ophi");
    expect(findGuide("missing")).toBeUndefined();
  });
});