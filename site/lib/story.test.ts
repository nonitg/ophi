import { expect, test } from "vitest";
import { STEPS, frameAt, lastBeat } from "./story";

test("the story ends with the crown finished, paid for and the next cleaning planned", () => {
  const last = STEPS.length - 1;
  const { care, record, tap } = frameAt(last, lastBeat(last));
  const state = Object.fromEntries(care.map(({ id, state }) => [id, state]));
  expect(state).toMatchObject({ cleaning: "done", prep: "done", lab: "done", fitting: "done", balance: "done", recall: "planned" });
  expect(record.at(-1)).toMatchObject({ kind: "PAYMENT", fresh: true });
  expect(tap).toBe("done");
});

test("a step that has just begun shows earlier steps in full and nothing of its own", () => {
  const { care, lines, record } = frameAt(1, -1);
  expect(care).toEqual([expect.objectContaining({ id: "cleaning", state: "waiting", changed: false })]);
  expect(lines).toEqual([]);
  expect(record.every(({ fresh }) => !fresh)).toBe(true);
});
