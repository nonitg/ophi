import React from "react";
import { AbsoluteFill, Easing, interpolate, Sequence, useCurrentFrame } from "remotion";

export type Enter = "none" | "fade" | "zoom" | "whip" | "rise" | "push" | "flip";
export type Exit = "none" | "zoom" | "flip" | "fade";

const out = Easing.bezier(0.16, 1, 0.3, 1);
const inE = Easing.bezier(0.7, 0, 0.84, 0);

// One shot of the demo: a window of frames with its own entrance and exit, so consecutive shots
// overlap into a transition (zoom-through, whip, card flip) instead of hard-cutting.
export const Cut: React.FC<{
  from: number;
  to: number;
  enter?: Enter;
  exit?: Exit;
  enterDur?: number;
  exitDur?: number;
  // Frames to stay invisible before entering (a flip waits for the outgoing half-turn).
  delay?: number;
  name?: string;
  children: React.ReactNode;
}> = ({ from, to, enter = "fade", exit = "none", enterDur = 14, exitDur = 12, delay = 0, name, children }) => (
  <Sequence from={from} durationInFrames={to - from} name={name}>
    <CutBody len={to - from} enter={enter} exit={exit} enterDur={enterDur} exitDur={exitDur} delay={delay}>
      {children}
    </CutBody>
  </Sequence>
);

const CutBody: React.FC<{ len: number; enter: Enter; exit: Exit; enterDur: number; exitDur: number; delay: number; children: React.ReactNode }> = ({
  len,
  enter,
  exit,
  enterDur,
  exitDur,
  delay,
  children,
}) => {
  const f = useCurrentFrame();
  const p = enter === "none" ? 1 : interpolate(f, [delay, delay + enterDur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: out });
  const q = exit === "none" ? 0 : interpolate(f, [len - exitDur, len], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: inE });
  if (f < delay) return null;

  let opacity = 1;
  let transform = "";
  let filter = "";
  switch (enter) {
    case "fade":
      opacity *= p;
      break;
    case "zoom":
      opacity *= Math.min(1, p * 1.6);
      transform += ` scale(${1.07 - 0.07 * p})`;
      break;
    case "whip":
      opacity *= Math.min(1, p * 2);
      transform += ` translateX(${(1 - p) * 1500}px)`;
      filter += ` blur(${(1 - p) * 16}px)`;
      break;
    case "rise":
      opacity *= p;
      transform += ` translateY(${(1 - p) * 90}px)`;
      break;
    case "push":
      opacity *= Math.min(1, p * 1.5);
      transform += ` translateX(${(1 - p) * 260}px)`;
      break;
    case "flip":
      transform += ` rotateY(${-90 * (1 - p)}deg)`;
      break;
  }
  switch (exit) {
    case "zoom":
      opacity *= 1 - q;
      transform += ` scale(${1 + 0.1 * q})`;
      break;
    case "fade":
      opacity *= 1 - q;
      break;
    case "flip":
      transform += ` rotateY(${90 * q}deg)`;
      if (q >= 1) opacity = 0;
      break;
  }
  return (
    <AbsoluteFill style={{ perspective: 2600 }}>
      <AbsoluteFill style={{ opacity, transform, filter: filter || undefined, backfaceVisibility: "hidden" }}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};
