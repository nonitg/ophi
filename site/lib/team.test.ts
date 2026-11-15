import { expect, test } from "vitest";
import { APPROVAL, EVENTS, teamAt } from "./team";

test("every event and the approval move a patient along and count toward the day", () => {
  const before = teamAt(0, false), after = teamAt(EVENTS.length, true);
  expect(after.tally.updates).toBeGreaterThan(before.tally.updates);
  expect(after.tally.booked).toBeGreaterThan(before.tally.booked);
  expect(after.latest).toBe(EVENTS.at(-1)!.id);
  const held = (rows: typeof after.rows) => rows.find(({ id }) => id === APPROVAL.id)!;
  expect(held(before.rows).ask).toBe(true);
  expect(held(after.rows)).toMatchObject({ ask: undefined, marks: APPROVAL.patch.marks });
});
