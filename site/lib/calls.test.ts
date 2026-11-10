import { describe, expect, it } from "vitest";
import { demoCall, moment, recordedOn, recordings, type Recording } from "@/lib/calls";

const rec: Recording = {
  slug: "slow-down",
  duration: 20,
  recordedAt: "2026-11-10",
  turns: [
    { who: "ophi", start: 0.3, end: 3, text: "Hi, I'm Ophi." },
    { who: "caller", start: 4, end: 6, text: "Could you slow down?" },
    { who: "ophi", start: 7.5, end: 12, text: "Of course. I'll go slower." },
  ],
  actions: [
    { t: 6.8, tool: "set_pace", args: { pace: "slower" }, result: { pace: "slower" } },
    { t: 12.5, tool: "end_call", args: { summary: "x" }, result: { ended: true } },
  ],
  proposals: [],
  summary: "Caller asked Ophi to slow down.",
  peaks: { rate: 20, caller: Array(400).fill(0.25), ophi: Array(400).fill(1) },
};

describe("demo calls", () => {
  it("puts each note before the reply it led to and sizes the trace", () => {
    const call = demoCall(rec);
    expect(call.title).toBe("“Could you slow down?”");
    expect(call.src).toBe("/calls/slow-down.mp3");
    // end_call is the summary, not a note.
    expect(call.notes).toEqual([{ t: 6.8, before: 2, text: "Slowed its speech, and now waits longer before replying" }]);
    expect(call.bars.ophi).toHaveLength(120);
    expect(call.bars.caller[0]).toBe(0.5);
  });

  it("finds the moment a skill shows", () => {
    // From the caller's request, so the listener hears what set it off.
    expect(moment(rec, "set_pace")).toEqual({ t: 3.7, quote: "Of course. I'll go slower." });
    expect(moment(rec, "transfer_to_staff")).toBeNull();
  });

  it("names the day the calls were recorded", () => {
    expect(recordedOn(rec)).toBe("November 10, 2026");
  });

  it("ships only complete recordings, each with a title", () => {
    for (const recording of recordings) {
      const call = demoCall(recording);
      expect(call.title, recording.slug).not.toBe(recording.slug);
      expect(recording.turns.at(-1)!.end, recording.slug).toBeLessThanOrEqual(recording.duration);
      expect(recording.peaks.ophi.length, recording.slug).toBe(recording.peaks.caller.length);
    }
    expect(recordings[0].proposals.length).toBeGreaterThan(0);
  });
});
