import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import map from "./canada-map.json";
import { color, ease, font, springs } from "../../theme";

type Dot = { x: number; y: number; city: string; o: number; g?: "dc" | "d123" };
const DOTS = map.dots as Dot[];
// Land a step deeper than brand sage so the country reads on a small player.
const LAND = "#dbe1cd";

type Props = {
  width: number;
  // Outline draws between these frames.
  drawFrom: number;
  drawTo: number;
  // Dots sweep in west→east between these frames.
  dotsFrom: number;
  dotsTo: number;
  // Frames the two national groups light up (dentalcorp, 123Dentist).
  dcAt?: number;
  d123At?: number;
  // 0..1: fade the map back while the math has the stage.
  dim?: number;
  // Frame a soft shimmer ripples across every dot (the market total landing).
  shimmerAt?: number;
  labelsAt?: number;
};

// Canada, Natural Earth outline in a Lambert conic, filled with clinic dots (1 dot ≈ 50 clinics).
// Dot placement follows population centres and is illustrative, not clinic addresses.
export const CanadaDotMap: React.FC<Props> = ({ width, drawFrom, drawTo, dotsFrom, dotsTo, dcAt = Infinity, d123At = Infinity, dim = 0, shimmerAt = Infinity, labelsAt = Infinity }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = width / map.width;
  const draw = interpolate(frame, [drawFrom, drawTo], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease.inOut });
  const fill = interpolate(frame, [drawTo - 10, drawTo + 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const labelsO = Number.isFinite(labelsAt) ? interpolate(frame, [labelsAt, labelsAt + 15], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 0;
  const span = dotsTo - dotsFrom;
  const dc = spring({ frame: frame - dcAt, fps, config: springs.snappy });
  const d123 = spring({ frame: frame - d123At, fps, config: springs.snappy });

  return (
    <svg width={width} height={map.height * scale} viewBox={`0 0 ${map.width} ${map.height}`} style={{ overflow: "visible", opacity: 1 - dim * 0.55 }}>
      <path d={map.graticule} fill="none" stroke={color.forest} strokeOpacity={0.07 * draw} strokeWidth={0.8} />
      <path d={map.outline} fill={LAND} fillOpacity={fill} stroke="none" />
      <path
        d={map.outline}
        fill="none"
        stroke={color.forest}
        strokeOpacity={0.82}
        strokeWidth={1.7}
        pathLength={1}
        strokeDasharray={1}
        strokeDashoffset={1 - draw}
        strokeLinejoin="round"
      />
      {DOTS.map((d, i) => {
        const at = dotsFrom + d.o * span;
        const p = spring({ frame: frame - at, fps, config: springs.overshoot, durationInFrames: 18 });
        if (p <= 0.001) return null;
        const inGroup = (d.g === "dc" && dc > 0.01) || (d.g === "d123" && d123 > 0.01);
        const g = d.g === "dc" ? dc : d.g === "d123" ? d123 : 0;
        const shimmer = Number.isFinite(shimmerAt) ? interpolate(frame - shimmerAt - d.o * 18, [0, 6, 16], [0, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 0;
        const r = 4.3 * p * (1 + 0.35 * shimmer) * (inGroup ? 1 + 0.75 * g : 1);
        const pulse = inGroup ? ((frame - (d.g === "dc" ? dcAt : d123At)) % 40) / 40 : 0;
        return (
          <g key={i}>
            {inGroup && (
              <circle cx={d.x} cy={d.y} r={8 + 22 * pulse} fill={color.orange} fillOpacity={(1 - pulse) * 0.12 * g} stroke={color.orange} strokeWidth={2} strokeOpacity={(1 - pulse) * 0.7 * g} />
            )}
            {d.g === "d123" && inGroup ? (
              <circle cx={d.x} cy={d.y} r={r + 1} fill={color.ivory} stroke={color.orange} strokeWidth={3.4 * g} />
            ) : (
              <circle cx={d.x} cy={d.y} r={r} fill={d.g === "dc" && inGroup ? color.orange : shimmer > 0.4 ? color.forestSoft : color.forest} fillOpacity={1} />
            )}
          </g>
        );
      })}
      {map.labels.map((l) => (
        <text key={l.name} x={l.x + 9} y={l.y - 9} fontFamily={font.mono} fontSize={13} fill={color.muted} stroke={color.ivory} strokeWidth={3.5} paintOrder="stroke" opacity={labelsO} letterSpacing="0.04em">
          {l.name.toUpperCase()}
        </text>
      ))}
    </svg>
  );
};
