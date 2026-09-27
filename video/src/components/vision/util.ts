import { interpolate } from "remotion";
import { ease } from "../../theme";

// 0..1 progress between two frames, eased and clamped.
export const ramp = (frame: number, a: number, b: number, e: (t: number) => number = ease.out) =>
  interpolate(frame, [a, Math.max(a + 1, b)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: e });

// Fade in over [a, a+len] and out over [b-len, b].
export const window01 = (frame: number, a: number, b: number, len = 12) =>
  Math.min(ramp(frame, a, a + len), 1 - ramp(frame, b - len, b));

// Sub-range of a 0..1 progress value (no frame-based minimum span), clamped.
export const seg = (t: number, a: number, b: number) => Math.max(0, Math.min(1, (t - a) / (b - a)));

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

// Film palette used across the vision scene: bone ink, orange "metal" accents on dark film.
export const film = {
  bone: "#e6ece3",
  boneDim: "rgba(230,236,227,0.55)",
  boneFaint: "rgba(230,236,227,0.22)",
  metal: "#ef865b",
  metalGlow: "rgba(239,134,91,0.55)",
  ink: "#0e1f19",
} as const;
