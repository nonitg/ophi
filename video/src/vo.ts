import voData from "./vo.json";
import { FPS } from "./theme";

import layout from "./layout.json";

// How each narrator section's measured lines sit in time (src/layout.json). Scene length is derived from
// this, so re-running scripts/video-vo.py re-times the whole video.
type Layout = { lead: number; gaps: number[]; tail: number };
const LAYOUT = layout.narration as Record<string, Layout>;

type RawWord = { w: string; s: number; e: number };
type RawLine = { id: string; text: string; file: string; dur: number; words: RawWord[] };
const raw = voData as unknown as { sections: Record<string, { lines: RawLine[] }> };

export type Word = { w: string; from: number; to: number };
export type VoLine = { id: string; text: string; file: string; from: number; frames: number; words: Word[] };

const f = (s: number) => Math.round(s * FPS);

// Lines of one section with frame offsets relative to the section start.
export const voLines = (section: string): VoLine[] => {
  const lines = raw.sections[section]?.lines ?? [];
  const lay = LAYOUT[section];
  if (!lay) return [];
  let t = lay.lead;
  return lines.map((l, i) => {
    const from = t;
    t += l.dur + (lay.gaps[i] ?? 0);
    return {
      id: l.id,
      text: l.text,
      file: l.file,
      from: f(from),
      frames: f(l.dur),
      words: l.words.map((w) => ({ w: w.w, from: f(from + w.s), to: f(from + w.e) })),
    };
  });
};

// Seconds a narrated section needs: lead + lines + gaps + tail.
export const voSeconds = (section: string): number => {
  const lines = raw.sections[section]?.lines ?? [];
  const lay = LAYOUT[section];
  if (!lay) return 0;
  return lay.lead + lines.reduce((n, l, i) => n + l.dur + (lay.gaps[i] ?? 0), 0) + lay.tail;
};

const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9$%]/g, "");

// A cue that no longer matches the narration (after a script edit) throws in strict mode
// (REMOTION_STRICT_CUES=1, used for final renders), so it fails loudly instead of silently mistiming a
// visual. Otherwise it warns and falls back to the line start, so one scene mid-rebuild can't break the bundle.
const STRICT = typeof process !== "undefined" && process.env?.REMOTION_STRICT_CUES === "1";
const miss = (msg: string, fallback: number) => {
  if (STRICT) throw new Error(msg);
  console.warn(`[cue] ${msg}`);
  return fallback;
};

// Frame (relative to section start) where a word is spoken: wordAt("cold", 1, "half").
// `nth` picks a later repeat of the same word in that line.
export const wordAt = (section: string, line: number, word: string, nth = 0, edge: "from" | "to" = "from"): number => {
  const l = voLines(section)[line];
  if (!l) return miss(`No line ${section}-${line}`, 0);
  const hits = l.words.filter((w) => norm(w.w) === norm(word));
  const hit = hits[nth];
  if (!hit) return miss(`Word "${word}" not in ${section}-${line}: ${l.text}`, l.from);
  return hit[edge];
};

// Start / end frame of a whole line.
export const lineAt = (section: string, line: number) => {
  const l = voLines(section)[line];
  if (!l) {
    const end = voLines(section).at(-1);
    const at = miss(`No line ${section}-${line}`, end ? end.from + end.frames : 0);
    return { from: at, to: at };
  }
  return { from: l.from, to: l.from + l.frames };
};
