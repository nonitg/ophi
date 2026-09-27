import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { color, ease, font, springs, type } from "../theme";

// DM Mono typewriter with a blinking caret. `start` is the frame typing begins; `cps` characters/second.
export const TypeOn: React.FC<{
  text: string;
  start?: number;
  cps?: number;
  size?: number;
  color?: string;
  caret?: boolean;
  style?: React.CSSProperties;
}> = ({ text, start = 0, cps = 28, size = type.label, color: c = color.forest, caret = true, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const n = Math.max(0, Math.min(text.length, Math.floor(((frame - start) / fps) * cps)));
  const done = n >= text.length;
  const blinkOn = Math.floor(frame / (fps * 0.5)) % 2 === 0;
  return (
    <span style={{ fontFamily: font.mono, fontSize: size, color: c, whiteSpace: "pre-wrap", letterSpacing: "0.02em", ...style }}>
      {text.slice(0, n)}
      {caret && frame >= start && (!done || blinkOn) ? (
        <span style={{ display: "inline-block", width: "0.55em", height: "1.05em", verticalAlign: "-0.15em", background: c, opacity: 0.85, marginLeft: 2 }} />
      ) : null}
    </span>
  );
};

// Rolling number with thousands separators. Eases from `from` to `to` between `start` and start+duration.
export const Counter: React.FC<{
  to: number;
  from?: number;
  start?: number;
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  style?: React.CSSProperties;
}> = ({ to, from = 0, start = 0, duration = 45, decimals = 0, prefix = "", suffix = "", style }) => {
  const frame = useCurrentFrame();
  const v = interpolate(frame, [start, start + duration], [from, to], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease.out });
  const s = v.toLocaleString("en-CA", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  return (
    <span style={{ fontVariantNumeric: "tabular-nums", ...style }}>
      {prefix}
      {s}
      {suffix}
    </span>
  );
};

// Source line, bottom-left, fading in at `start` and out at `end`.
export const Footnote: React.FC<{ text: string; start?: number; end?: number; dark?: boolean; bottom?: number }> = ({ text, start = 0, end = Infinity, dark = false, bottom = 48 }) => {
  const frame = useCurrentFrame();
  const o = Math.min(
    interpolate(frame, [start, start + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
    Number.isFinite(end) ? interpolate(frame, [end - 12, end], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 1,
  );
  return (
    <div
      style={{
        position: "absolute",
        left: 72,
        bottom,
        maxWidth: 1200,
        opacity: o,
        fontFamily: font.sans,
        fontSize: type.foot,
        lineHeight: 1.35,
        color: dark ? "rgba(230,236,227,0.7)" : color.muted,
      }}
    >
      {text}
    </div>
  );
};

// Persistent pill over product footage: the demo is never mistaken for real patient data.
export const DemoTag: React.FC<{ label?: string; start?: number }> = ({ label = "Demo data · fictional patients", start = 0 }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [start, start + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div
      style={{
        position: "absolute",
        top: 36,
        right: 40,
        opacity: o,
        padding: "8px 16px",
        borderRadius: 999,
        background: "rgba(25,58,48,0.9)",
        color: color.ivory,
        fontFamily: font.sans,
        fontWeight: 500,
        fontSize: 18,
        letterSpacing: "0.01em",
        boxShadow: "0 6px 18px rgba(15,36,29,0.18)",
      }}
    >
      {label}
    </div>
  );
};

// Lowercase "ophi." — letters rise in sequence, then the orange period pops with overshoot.
export const Wordmark: React.FC<{ start?: number; size?: number; ink?: string }> = ({ start = 0, size = 220, ink = color.forest }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const letters = "ophi".split("");
  const dotAt = start + letters.length * 4 + 6;
  const dot = spring({ frame: frame - dotAt, fps, config: springs.overshoot });
  return (
    <div style={{ fontFamily: font.display, fontSize: size, color: ink, lineHeight: 1, display: "flex", alignItems: "baseline", letterSpacing: "-0.02em" }}>
      {letters.map((l, i) => {
        const p = spring({ frame: frame - start - i * 4, fps, config: springs.critical });
        return (
          <span key={i} style={{ display: "inline-block", transform: `translateY(${(1 - p) * size * 0.35}px)`, opacity: p, clipPath: "inset(-20% -10% -30% -10%)" }}>
            {l}
          </span>
        );
      })}
      <span style={{ display: "inline-block", color: color.orange, transform: `scale(${dot})`, transformOrigin: "50% 80%" }}>.</span>
    </div>
  );
};
