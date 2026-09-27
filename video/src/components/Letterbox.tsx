import React from "react";
import { AbsoluteFill } from "remotion";

// Documentary framing: black bars that slide in to a 2.39:1 frame at open=1.
export const Letterbox: React.FC<{ open: number; color?: string }> = ({ open, color = "#050807" }) => {
  const bar = (1080 - 1920 / 2.39) / 2; // ≈138px
  const h = bar * Math.max(0, Math.min(1, open));
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: h, background: color }} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: h, background: color }} />
    </AbsoluteFill>
  );
};
