import React from "react";
import { AbsoluteFill, staticFile, useCurrentFrame } from "remotion";
import { color } from "../theme";

type Props = {
  variant?: "paper" | "film";
  // Window light strength over printed content (paper only), 0..1.
  light?: number;
  // Slow horizontal drift of the window light in px over the scene, for a sense of time passing.
  drift?: number;
  // Lightbox glow strength behind the film (film only), 0..1.
  glow?: number;
  // Draw the window light over the content (printed matter) or only on the paper beneath it (screens).
  lightOver?: boolean;
  children?: React.ReactNode;
  style?: React.CSSProperties;
};

// Film grain: a fresh noise seed every 2 frames so it shimmers like real emulsion.
const FilmGrain: React.FC = () => {
  const frame = useCurrentFrame();
  const seed = Math.floor(frame / 2) % 97;
  return (
    <svg width="100%" height="100%" style={{ position: "absolute", inset: 0, mixBlendMode: "screen", opacity: 0.16 }}>
      <filter id={`fg-${seed}`} x="0" y="0" width="100%" height="100%">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={seed} stitchTiles="stitch" />
        <feColorMatrix values="0 0 0 0 0.9  0 0 0 0 0.95  0 0 0 0 0.92  0 0 0 0.9 -0.25" />
      </filter>
      <rect width="100%" height="100%" filter={`url(#fg-${seed})`} />
    </svg>
  );
};

// Ophi's printed world: cotton paper in afternoon window light from the upper left (DESIGN.md), or the
// X-ray film on a lightbox that the site's X-ray mode turns it into.
export const Paper: React.FC<Props> = ({ variant = "paper", light = 1, drift = 0, glow = 1, lightOver = true, children, style }) => {
  const frame = useCurrentFrame();
  if (variant === "film") {
    return (
      <AbsoluteFill style={{ background: color.film, ...style }}>
        <AbsoluteFill
          style={{
            opacity: glow,
            background: `radial-gradient(ellipse 70% 60% at 50% 48%, rgba(120,160,140,0.28), rgba(14,31,25,0) 70%)`,
          }}
        />
        {children}
        <FilmGrain />
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)" }} />
      </AbsoluteFill>
    );
  }
  const dx = drift * Math.min(1, frame / 900);
  const windowLight = (
    <AbsoluteFill
      style={{
        opacity: light,
        backgroundImage: `url(${staticFile("light-wide.svg")})`,
        backgroundSize: "1920px auto",
        backgroundPosition: `${dx}px 0`,
        backgroundRepeat: "no-repeat",
        pointerEvents: "none",
      }}
    />
  );
  return (
    <AbsoluteFill style={{ background: color.ivory, ...style }}>
      <AbsoluteFill style={{ backgroundImage: `url(${staticFile("paper.svg")})`, backgroundSize: "256px 256px" }} />
      {!lightOver && windowLight}
      {children}
      {lightOver && windowLight}
    </AbsoluteFill>
  );
};
