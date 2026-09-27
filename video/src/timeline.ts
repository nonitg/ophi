import { FPS } from "./theme";
import { voSeconds } from "./vo";
import layout from "./layout.json";

export type SectionKind = "narrator" | "founder" | "card";

export type Section = {
  id: string;
  title: string;
  kind: SectionKind;
  seconds: number;
};

// Order and founder-cam lengths follow docs/pitch/af-hacks-script.md (v3). Narrated sections take their
// length from the measured voiceover (vo.ts); the end card absorbs the remainder so the cut is 5:00.
const RUNTIME = layout.runtime;
const FOUNDER = layout.founder;
const narrated = ["cold", "patient", "problem", "demo", "value", "market", "vision"];
const narratedSeconds = narrated.reduce((n, id) => n + voSeconds(id), 0);
const END = Math.max(4, RUNTIME - narratedSeconds - FOUNDER.team - FOUNDER.close);

export const sections: Section[] = [
  { id: "cold", title: "Cold open", kind: "narrator", seconds: voSeconds("cold") },
  { id: "patient", title: "The patient", kind: "narrator", seconds: voSeconds("patient") },
  { id: "problem", title: "The problem", kind: "narrator", seconds: voSeconds("problem") },
  { id: "demo", title: "Demo", kind: "narrator", seconds: voSeconds("demo") },
  { id: "value", title: "What a clinic gets", kind: "narrator", seconds: voSeconds("value") },
  { id: "market", title: "The market", kind: "narrator", seconds: voSeconds("market") },
  { id: "vision", title: "Vision and moat", kind: "narrator", seconds: voSeconds("vision") },
  { id: "team", title: "Team, traction, plan", kind: "founder", seconds: FOUNDER.team },
  { id: "close", title: "Close", kind: "founder", seconds: FOUNDER.close },
  { id: "end", title: "End card", kind: "card", seconds: END },
];

export const sec = (s: number) => Math.round(s * FPS);

export const framesOf = (s: Section) => sec(s.seconds);

export const totalFrames = sections.reduce((n, s) => n + framesOf(s), 0);

// Frame offset where each section starts in the full Pitch.
export const offsets: Record<string, { from: number; frames: number }> = (() => {
  let at = 0;
  const out: Record<string, { from: number; frames: number }> = {};
  for (const s of sections) {
    out[s.id] = { from: at, frames: framesOf(s) };
    at += framesOf(s);
  }
  return out;
})();

export const section = (id: string) => {
  const s = sections.find((x) => x.id === id);
  if (!s) throw new Error(`Unknown section ${id}`);
  return s;
};

// Timecode (m:ss) of a section start, for founder-cam hand-off notes.
export const timecode = (frame: number) => {
  const t = Math.round(frame / FPS);
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
};
