import React from "react";
import { AbsoluteFill } from "remotion";
import { XraySweep } from "../XraySweep";
import { ease } from "../../theme";

const W = 1920;
const beamX = (p: number) => -90 + ease.inOut(Math.max(0, Math.min(1, p))) * (W + 90 + 420);

// The shared X-ray sweep, made visible on ivory: the freshly exposed strip behind the beam reads as dark
// film for a moment, then develops into the new scene.
export const SweepOnPaper: React.FC<{ progress: number; from: React.ReactNode; to: React.ReactNode }> = ({ progress, from, to }) => {
  const x = beamX(progress);
  return (
    <AbsoluteFill>
      <XraySweep progress={progress} from={from} to={to} />
      <AbsoluteFill
        style={{
          pointerEvents: "none",
          background: `linear-gradient(90deg, rgba(14,31,25,0) ${x - 520}px, rgba(14,31,25,0.55) ${x - 90}px, rgba(14,31,25,0.9) ${x - 6}px, rgba(14,31,25,0) ${x}px)`,
        }}
      />
      <AbsoluteFill style={{ pointerEvents: "none", background: `linear-gradient(90deg, rgba(255,255,250,0) ${x - 3}px, rgba(255,255,250,0.95) ${x}px, rgba(255,255,250,0) ${x + 3}px)`, filter: "blur(1px)" }} />
    </AbsoluteFill>
  );
};
