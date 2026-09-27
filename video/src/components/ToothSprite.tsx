import React, { useEffect } from "react";
import { Img, prefetch, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

const FRAMES = 120;
const folder = { normal: "normal-noshadow", shadow: "normal", xray: "xray" } as const;
export type ToothVariant = keyof typeof folder;

const src = (variant: ToothVariant, i: number) =>
  staticFile(`tooth/${folder[variant]}/${String(((i % FRAMES) + FRAMES) % FRAMES).padStart(4, "0")}.png`);

type Props = {
  variant?: ToothVariant;
  // Turns per second; negative spins the other way.
  rotationSpeed?: number;
  // Sprite index to start from (0..119; 0 is the homepage pose).
  frameOffset?: number;
  size?: number;
  // Warm pool of light behind the tooth, 0..1.
  spotlight?: number;
  style?: React.CSSProperties;
};

// The site's enamel tooth as a turntable. Two neighbouring sprites cross-fade by the fractional index,
// so slow turns glide instead of stepping in 3° increments.
export const ToothSprite: React.FC<Props> = ({ variant = "normal", rotationSpeed = 0.08, frameOffset = 0, size = 720, spotlight = 0, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  useEffect(() => {
    const handles = Array.from({ length: FRAMES }, (_, i) => prefetch(src(variant, i)));
    return () => handles.forEach((h) => h.free());
  }, [variant]);

  const pos = frameOffset + (frame / fps) * rotationSpeed * FRAMES;
  const i = Math.floor(pos);
  const t = pos - i;

  return (
    <div style={{ position: "relative", width: size, height: size, ...style }}>
      {spotlight > 0 && (
        <div
          style={{
            position: "absolute",
            inset: -size * 0.35,
            opacity: spotlight,
            background:
              variant === "xray"
                ? "radial-gradient(circle at 50% 50%, rgba(150,190,170,0.35), rgba(14,31,25,0) 60%)"
                : "radial-gradient(circle at 46% 44%, rgba(255,248,226,0.95), rgba(255,244,214,0.35) 38%, rgba(244,242,233,0) 64%)",
          }}
        />
      )}
      <Img src={src(variant, i)} style={{ position: "absolute", inset: 0, width: size, height: size }} />
      <Img src={src(variant, i + 1)} style={{ position: "absolute", inset: 0, width: size, height: size, opacity: t }} />
    </div>
  );
};

export const HeroTooth: React.FC<{ size?: number; style?: React.CSSProperties }> = ({ size = 900, style }) => (
  <Img src={staticFile("tooth/still-hero.png")} style={{ width: size, height: size, ...style }} />
);
