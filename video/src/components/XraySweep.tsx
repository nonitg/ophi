import React from "react";
import { AbsoluteFill } from "remotion";
import type { TransitionPresentation, TransitionPresentationComponentProps } from "@remotion/transitions";
import { ease } from "../theme";

const W = 1920;
const LEAD = 90; // px of glow ahead of the beam
const TRAIL = 420; // px of fresh-exposure glow behind it

// Beam x-position for a 0..1 progress: starts just off the left edge, ends just off the right.
const beamX = (p: number) => -LEAD + ease.inOut(Math.max(0, Math.min(1, p))) * (W + LEAD + TRAIL);

// The light itself: a bright core, a halation bloom, and a trailing "fresh exposure" that fades out,
// like a panoramic unit's arm building its image left to right.
export const XrayBeam: React.FC<{ progress: number; tint?: string }> = ({ progress, tint = "230,238,228" }) => {
  if (progress <= 0 || progress >= 1) return null;
  const x = beamX(progress);
  const fade = Math.min(1, progress * 8, (1 - progress) * 8);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: fade, mixBlendMode: "screen" }}>
      {/* trailing exposure */}
      <div
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: x - TRAIL,
          width: TRAIL,
          background: `linear-gradient(90deg, rgba(${tint},0) 0%, rgba(${tint},0.10) 55%, rgba(${tint},0.38) 100%)`,
        }}
      />
      {/* faint scan lines inside the trail */}
      <div
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: x - TRAIL * 0.6,
          width: TRAIL * 0.6,
          opacity: 0.35,
          background: `repeating-linear-gradient(0deg, rgba(${tint},0.10) 0px, rgba(${tint},0.10) 1px, rgba(${tint},0) 1px, rgba(${tint},0) 4px)`,
          maskImage: "linear-gradient(90deg, transparent, black)",
          WebkitMaskImage: "linear-gradient(90deg, transparent, black)",
        }}
      />
      {/* halation bloom */}
      <div
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: x - 70,
          width: 70 + LEAD,
          background: `linear-gradient(90deg, rgba(${tint},0) 0%, rgba(${tint},0.55) 44%, rgba(${tint},0.55) 50%, rgba(${tint},0) 100%)`,
          filter: "blur(14px)",
        }}
      />
      {/* core */}
      <div
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: x - 3,
          width: 6,
          background: `rgba(255,255,252,0.95)`,
          boxShadow: `0 0 18px 6px rgba(${tint},0.85), 0 0 60px 18px rgba(${tint},0.35)`,
        }}
      />
    </AbsoluteFill>
  );
};

// Standalone: reveal `to` over `from` as the beam passes.
export const XraySweep: React.FC<{ progress: number; from: React.ReactNode; to: React.ReactNode }> = ({ progress, from, to }) => {
  const x = Math.max(0, Math.min(W, beamX(progress)));
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ clipPath: `inset(0 0 0 ${x}px)` }}>{from}</AbsoluteFill>
      <AbsoluteFill style={{ clipPath: `inset(0 ${W - x}px 0 0)` }}>{to}</AbsoluteFill>
      <XrayBeam progress={progress} />
    </AbsoluteFill>
  );
};

// @remotion/transitions presentation: <TransitionSeries.Transition presentation={xraySweep()} timing={...} />
type SweepProps = Record<string, never>;
const SweepPresentation: React.FC<TransitionPresentationComponentProps<SweepProps>> = ({
  children,
  presentationDirection,
  presentationProgress,
}) => {
  const x = Math.max(0, Math.min(W, beamX(presentationProgress)));
  if (presentationDirection === "exiting") {
    return <AbsoluteFill style={{ clipPath: `inset(0 0 0 ${x}px)` }}>{children}</AbsoluteFill>;
  }
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ clipPath: `inset(0 ${W - x}px 0 0)` }}>{children}</AbsoluteFill>
      <XrayBeam progress={presentationProgress} />
    </AbsoluteFill>
  );
};

export const xraySweep = (): TransitionPresentation<SweepProps> => ({ component: SweepPresentation, props: {} });
