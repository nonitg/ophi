import React from "react";
import { Audio, Sequence, staticFile, interpolate } from "remotion";
import sfxFiles from "./sfx.json";
import { voLines, wordAt } from "./vo";
import { offsets, sections } from "./timeline";
import { FPS } from "./theme";

// Narration for one section; drop inside that section's scene so per-scene previews are voiced too.
export const Narration: React.FC<{ section: string; volume?: number }> = ({ section, volume = 1 }) => (
  <>
    {voLines(section).map((l) => (
      <Sequence key={l.id} from={l.from} durationInFrames={l.frames + 2} name={`VO ${l.id}`} layout="none">
        <Audio src={staticFile(l.file)} volume={volume} />
      </Sequence>
    ))}
  </>
);

const SFX = sfxFiles as Record<string, string>;

// A sound effect at a frame. Silently absent until the file exists (scripts/video-audio-prep.sh lists them),
// so scenes can declare their sounds before every effect is generated.
export const Sfx: React.FC<{ name: string; at: number; volume?: number; trim?: number }> = ({ name, at, volume = 0.5, trim }) => {
  const file = SFX[name];
  if (!file) return null;
  return (
    <Sequence from={Math.round(at)} durationInFrames={trim} name={`SFX ${name}`} layout="none">
      <Audio src={staticFile(file)} volume={volume} />
    </Sequence>
  );
};

// Absolute frames where narration is speaking, for ducking the music under it.
const voiceSpans: [number, number][] = sections.flatMap((s) =>
  voLines(s.id).map((l) => [offsets[s.id].from + l.from, offsets[s.id].from + l.from + l.frames] as [number, number]),
);

const RAMP = 10; // frames to duck in / out
const duckAt = (abs: number) => {
  let d = Infinity;
  for (const [a, b] of voiceSpans) {
    if (abs >= a && abs <= b) return 1;
    d = Math.min(d, abs < a ? a - abs : abs - b);
  }
  return interpolate(d, [0, RAMP], [1, 0], { extrapolateRight: "clamp" });
};

type Cue = { file: string; from: number; frames: number; startFrom?: number; level: number; ducked: number; fadeIn: number; fadeOut: number };

const at = (id: string) => offsets[id].from;
const endOf = (id: string) => offsets[id].from + offsets[id].frames;
const s = (x: number) => Math.round(x * FPS);

// Cue C's swell (54 s into the cue) lands on "moat" (vision line 3 in script v4).
const moatAbs = at("vision") + wordAt("vision", 3, "moat");
const cueCStart = moatAbs - s(54);

const CUES: Cue[] = [
  // Documentary strings: cold open through the Ophi reveal (its resolve lands near the wordmark).
  { file: "music/cue-a.wav", from: 0, frames: endOf("problem") - 0 + s(0.6), level: 0.42, ducked: 0.16, fadeIn: s(0.8), fadeOut: s(1.4) },
  // Product underscore: demo, value, market.
  { file: "music/cue-b.wav", from: at("demo"), frames: endOf("market") - at("demo") + s(0.8), level: 0.34, ducked: 0.13, fadeIn: s(1.0), fadeOut: s(1.6) },
  // Vision build, aligned so the swell hits "moat".
  {
    file: "music/cue-c.wav",
    from: Math.max(at("vision") - s(0.4), cueCStart),
    startFrom: Math.max(0, at("vision") - s(0.4) - cueCStart),
    frames: endOf("vision") - Math.max(at("vision") - s(0.4), cueCStart) + s(1.2),
    level: 0.5,
    ducked: 0.2,
    fadeIn: s(0.6),
    fadeOut: s(1.8),
  },
  // A low bed under the founders so the cut doesn't fall silent; they can lower it in their edit.
  { file: "music/cue-b.wav", from: at("team"), frames: endOf("close") - at("team"), startFrom: s(2), level: 0.09, ducked: 0.09, fadeIn: s(1.5), fadeOut: s(1.5) },
  { file: "music/cue-end.wav", from: at("end") - s(0.3), frames: s(9), level: 0.55, ducked: 0.55, fadeIn: 1, fadeOut: s(1.0) },
];

export const MusicBed: React.FC = () => (
  <>
    {CUES.map((c, i) => (
      <Sequence key={i} from={c.from} durationInFrames={c.frames} name={`Music ${c.file}`} layout="none">
        <Audio
          src={staticFile(c.file)}
          startFrom={c.startFrom ?? 0}
          volume={(f) => {
            const env = Math.min(
              interpolate(f, [0, c.fadeIn], [0, 1], { extrapolateRight: "clamp" }),
              interpolate(f, [c.frames - c.fadeOut, c.frames], [1, 0], { extrapolateLeft: "clamp" }),
            );
            const duck = duckAt(c.from + f);
            return env * (c.level + (c.ducked - c.level) * duck);
          }}
        />
      </Sequence>
    ))}
  </>
);
