import { expect, test } from "vitest";
import { MOMENTS, lastHeroBeat, shownAt } from "./hero";
import { teamAt } from "./team";

test("each hero patient ends answered, with their care read and what Ophi did shown", () => {
  for (const moment of MOMENTS) {
    const { lines, rows, did } = shownAt(moment, lastHeroBeat(moment));
    expect(rows.length).toBeGreaterThan(0);
    expect(did).toBe(true);
    if (!moment.page) expect(lines.some(({ who }) => who === "ophi")).toBe(true);
  }
});

test("Alex's fitting moves to the time the clinic view shows, and Chloé books the time it shows", () => {
  const rows = new Map(teamAt(3, false).rows.map((row) => [row.id, row]));
  const alex = shownAt(MOMENTS[0], lastHeroBeat(MOMENTS[0]));
  expect(alex.rows.at(-1)).toMatchObject({ label: "Crown fitting", note: "Fri Dec 4, 1:00 pm", changed: true });
  expect(rows.get("alex")?.next).toContain("Fri 1:00 pm");
  const chloe = shownAt(MOMENTS[2], lastHeroBeat(MOMENTS[2]));
  expect(rows.get("chloe")?.next).toContain(chloe.rows[0].note);
  expect(chloe.tap).toBe("done");
});
