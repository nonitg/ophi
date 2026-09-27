import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { color, font, springs } from "../../theme";
import { useEnvelope } from "./Overlays";

const out = Easing.bezier(0.16, 1, 0.3, 1);

// Teresa's last periapical (Nov 14, 2023) against CDCP's 12-month window, on a 34-month axis to today.
export const FilmTimeline: React.FC<{ start: number; film: number; gap: number; win: number; end: number; top: number }> = ({ start, film, gap, win, end, top }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const v = useEnvelope(start, end, 16, 14);
  if (v <= 0) return null;
  const W = 1400;
  const H = 268;
  const x0 = 90;
  const x1 = W - 90;
  const mx = (m: number) => x0 + ((x1 - x0) * m) / 34;
  const axisY = 160;
  const axis = interpolate(f, [start, start + 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: out });
  const drop = spring({ frame: f - film, fps, config: springs.overshoot });
  const gapP = interpolate(f, [gap, gap + 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: out });
  const winP = interpolate(f, [win, win + 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: out });
  const years: [number, string][] = [
    [2, "2024"],
    [14, "2025"],
  ];
  return (
    <div
      style={{
        position: "absolute",
        left: (1920 - W) / 2,
        top,
        width: W,
        height: H,
        opacity: v,
        transform: `translateY(${(1 - v) * 40}px)`,
        borderRadius: 24,
        background: "#faf9f4",
        boxShadow: "0 24px 70px rgba(15,36,29,0.30), 0 2px 6px rgba(15,36,29,0.15)",
      }}
    >
      <svg width={W} height={H} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
        {/* CDCP window: the last 12 months */}
        <rect x={mx(34) - (mx(34) - mx(22)) * winP} y={axisY - 24} width={(mx(34) - mx(22)) * winP} height={48} rx={10} fill={color.sage} stroke={color.forestSoft} strokeWidth={2} opacity={winP > 0 ? 1 : 0} />
        <line x1={x0} y1={axisY} x2={x0 + (x1 - x0) * axis} y2={axisY} stroke={color.forest} strokeWidth={3} strokeLinecap="round" />
        {years.map(([m, y]) => (
          <g key={y} opacity={axis}>
            <line x1={mx(m)} y1={axisY - 10} x2={mx(m)} y2={axisY + 10} stroke={color.forest} strokeWidth={2} />
            <text x={mx(m)} y={axisY + 46} textAnchor="middle" style={{ fontFamily: font.mono, fontSize: 22 }} fill={color.muted}>
              {y}
            </text>
          </g>
        ))}
        {/* Gap bracket, film to today */}
        {gapP > 0 && (
          <g>
            <path
              d={`M ${mx(0)} ${axisY - 56} v -16 h ${(mx(34) - mx(0)) * gapP} v 16`}
              fill="none"
              stroke={color.orange}
              strokeWidth={4}
              strokeLinejoin="round"
            />
          </g>
        )}
        {/* Today */}
        <g opacity={axis}>
          <circle cx={mx(34)} cy={axisY} r={9} fill={color.forest} />
          <text x={mx(34) + 18} y={axisY + 8} textAnchor="start" style={{ fontFamily: font.mono, fontSize: 22 }} fill={color.forest}>
            today
          </text>
        </g>
      </svg>
      {/* Gap label */}
      <div
        style={{
          position: "absolute",
          left: mx(17),
          top: axisY - 128,
          transform: "translateX(-50%)",
          opacity: gapP,
          fontFamily: font.sans,
          fontWeight: 700,
          fontSize: 40,
          color: color.orange,
          whiteSpace: "nowrap",
        }}
      >
        34 months old
      </div>
      {/* Window label */}
      <div
        style={{
          position: "absolute",
          left: mx(28),
          top: axisY + 34,
          transform: "translateX(-50%)",
          opacity: winP,
          fontFamily: font.sans,
          fontWeight: 700,
          fontSize: 26,
          color: color.forestSoft,
          whiteSpace: "nowrap",
        }}
      >
        CDCP window · last 12 months
      </div>
      {/* The film */}
      {f >= film && (
        <div
          style={{
            position: "absolute",
            left: mx(0),
            top: axisY,
            transform: `translate(-50%, ${-50 - (1 - drop) * 120}%)`,
            opacity: Math.min(1, (f - film) / 5),
          }}
        >
          <div
            style={{
              width: 62,
              height: 82,
              borderRadius: 9,
              background: color.film,
              boxShadow: "0 8px 18px rgba(0,0,0,0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              border: `3px solid ${color.orange}`,
            }}
          >
            <svg width={34} height={48} viewBox="0 0 34 48">
              <path d="M5 6 Q17 -2 29 6 Q32 20 26 26 L24 44 Q21 46 19 40 L17 30 L15 40 Q13 46 10 44 L8 26 Q2 20 5 6 Z" fill={color.bone} opacity={0.9} />
            </svg>
          </div>
        </div>
      )}
      <div
        style={{
          position: "absolute",
          left: mx(0) - 40,
          top: axisY + 70,
          opacity: interpolate(f, [film + 6, film + 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          fontFamily: font.sans,
          fontSize: 24,
          color: color.forest,
          whiteSpace: "nowrap",
        }}
      >
        <b style={{ fontWeight: 700 }}>Last x-ray of #46</b> · Nov 14, 2023
      </div>
    </div>
  );
};
