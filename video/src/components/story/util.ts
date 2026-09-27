import { interpolate, spring } from "remotion";
import { ease, springs } from "../../theme";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// 0→1 eased progress starting at `at` over `dur` frames.
export const prog = (frame: number, at: number, dur = 18, easing = ease.out) =>
  interpolate(frame, [at, at + dur], [0, 1], { ...clamp, easing });

// 1→0 eased fade starting at `at`.
export const fadeOut = (frame: number, at: number, dur = 12) => 1 - prog(frame, at, dur, ease.inOut);

// Spring from `at` with a named preset.
export const pop = (frame: number, at: number, fps: number, cfg: keyof typeof springs = "critical") =>
  spring({ frame: frame - at, fps, config: springs[cfg] });

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

// Deterministic shuffle so the same cards light every render.
export const seeded = (seed: number) => {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 2 ** 32;
  };
};

export const shuffle = <T,>(arr: T[], seed: number): T[] => {
  const r = seeded(seed);
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(r() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
};
