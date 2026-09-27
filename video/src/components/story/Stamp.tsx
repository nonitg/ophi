import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { color, font } from "../../theme";
import { pop } from "./util";

// Rubber stamp that drops onto the page at `at`: comes in large and soft, lands with a small jolt.
export const Stamp: React.FC<{ at: number; lines: string[]; rotate?: number; ink?: string; size?: number; style?: React.CSSProperties }> = ({
  at,
  lines,
  rotate = -8,
  ink = color.orange,
  size = 1,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < at - 6) return null;
  const hover = interpolate(frame, [at - 6, at], [0, 1], { extrapolateRight: "clamp" });
  const land = pop(frame, at, fps, "snappy");
  const scale = frame < at ? interpolate(hover, [0, 1], [1.6, 1.25]) : interpolate(land, [0, 1], [1.25, 1]);
  const jolt = frame >= at && frame < at + 6 ? Math.sin((frame - at) * 2.4) * (6 - (frame - at)) * 0.6 : 0;
  return (
    <div
      style={{
        position: "absolute",
        transform: `translate(${jolt}px, ${jolt * 0.5}px) rotate(${rotate}deg) scale(${scale * size})`,
        transformOrigin: "center",
        opacity: frame < at ? hover * 0.5 : 0.92,
        border: `5px solid ${ink}`,
        borderRadius: 12,
        padding: "14px 26px 12px",
        color: ink,
        fontFamily: font.mono,
        fontWeight: 500,
        textAlign: "center",
        letterSpacing: "0.12em",
        lineHeight: 1.25,
        mixBlendMode: "multiply",
        filter: frame < at ? "blur(2px)" : "none",
        ...style,
      }}
    >
      {lines.map((l, i) => (
        <div key={i} style={{ fontSize: i === 0 ? 34 : 22 }}>
          {l}
        </div>
      ))}
    </div>
  );
};
