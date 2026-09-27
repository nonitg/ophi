import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { ease, font } from "../../theme";
import { film, ramp } from "./util";

export type TallyStep = { at: number; value: number; plus?: boolean; note: string };

// Running total of dental benefit dollars the engine can check, stepping up as each branch lights.
// `extras` are touchpoints on the same dollars (claims before sending, audits after payment), not new money.
export const Tally: React.FC<{ steps: TallyStep[]; start: number; opacity?: number; sources?: string; extras?: { at: number; text: string }[] }> = ({
  steps,
  start,
  opacity = 1,
  sources,
  extras = [],
}) => {
  const frame = useCurrentFrame();
  const vis = ramp(frame, start, start + 18) * opacity;
  if (vis <= 0) return null;
  const done = steps.filter((s) => frame >= s.at);
  const cur = done[done.length - 1] ?? steps[0];
  const prev = done.length > 1 ? done[done.length - 2].value : 0;
  const t = interpolate(frame, [cur.at, cur.at + 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease.out });
  const v = frame < steps[0].at ? 0 : prev + (cur.value - prev) * t;
  const plus = done.some((s) => s.plus);
  const bump = 1 + 0.04 * Math.sin(Math.min(1, t) * Math.PI) * (done.length > 0 ? 1 : 0);
  return (
    <div style={{ position: "absolute", top: 64, right: 72, textAlign: "right", opacity: vis }}>
      <div style={{ fontFamily: font.mono, fontSize: 17, letterSpacing: "0.14em", color: film.boneDim, textTransform: "uppercase" }}>
        Dental benefits a year, by payer
      </div>
      <div
        style={{
          fontFamily: font.display,
          fontSize: 112,
          lineHeight: 1,
          color: film.bone,
          marginTop: 16,
          fontVariantNumeric: "tabular-nums",
          transform: `scale(${bump})`,
          transformOrigin: "100% 100%",
        }}
      >
        ${v.toFixed(1)}B{plus ? <span style={{ color: film.metal }}>+</span> : null}
      </div>
      <div style={{ fontFamily: font.mono, fontSize: 19, color: film.boneDim, marginTop: 8 }}>
        {done.map((s) => s.note).join("  ·  ") || " "}
      </div>
      {extras.map((x) => {
        const o = ramp(frame, x.at, x.at + 14);
        return o > 0 ? (
          <div key={x.text} style={{ fontFamily: font.mono, fontSize: 19, color: film.metal, marginTop: 6, opacity: o, transform: `translateY(${(1 - o) * 8}px)` }}>
            {x.text}
          </div>
        ) : null;
      })}
      {sources && (
        <div style={{ fontFamily: font.sans, fontSize: 15, lineHeight: 1.4, color: "rgba(230,236,227,0.5)", marginTop: 14, maxWidth: 560, marginLeft: "auto" }}>{sources}</div>
      )}
    </div>
  );
};
