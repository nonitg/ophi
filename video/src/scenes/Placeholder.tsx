import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Paper } from "../components";
import { section, sections } from "../timeline";
import { color, ease, font, type } from "../theme";

// Stand-in until the scene is built: section number, title and slot length.
export const Placeholder: React.FC<{ id: string }> = ({ id }) => {
  const frame = useCurrentFrame();
  const s = section(id);
  const n = sections.findIndex((x) => x.id === id) + 1;
  const p = interpolate(frame, [0, 24], [0, 1], { extrapolateRight: "clamp", easing: ease.out });
  return (
    <Paper>
      <AbsoluteFill style={{ padding: "0 160px", justifyContent: "center" }}>
        <div style={{ fontFamily: font.mono, fontSize: type.label, color: color.muted, letterSpacing: "0.08em", opacity: p }}>
          {String(n).padStart(2, "0")} · {s.kind.toUpperCase()} · {s.seconds}s
        </div>
        <div style={{ fontFamily: font.display, fontSize: type.h1, color: color.forest, marginTop: 18, transform: `translateY(${(1 - p) * 30}px)`, opacity: p }}>
          {s.title}
        </div>
      </AbsoluteFill>
    </Paper>
  );
};

// Founder segments are pure black: the founders' own footage is laid over them in the edit.
export const FounderBlack: React.FC = () => <AbsoluteFill style={{ background: "#000" }} />;
