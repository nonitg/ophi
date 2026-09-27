import React from "react";
import { color } from "../../theme";

// Line-art molar: crown with two cusps, two roots. Drawn once, reused on request cards and checklists.
export const ToothGlyph: React.FC<{ size?: number; stroke?: string; fill?: string; width?: number; style?: React.CSSProperties }> = ({
  size = 24,
  stroke = color.forest,
  fill = "none",
  width = 1.6,
  style,
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={style}>
    <path
      d="M6.2 3.2c1.6-.9 3.1-.3 4.4.4.9.5 1.9.5 2.8 0 1.3-.7 2.8-1.3 4.4-.4 2.1 1.2 2.4 4.2 1.7 6.6-.5 1.7-1.1 3.1-1.4 4.9-.3 2.1-.5 4.9-1.9 5.9-1.2.8-2-.6-2.3-2.1-.3-1.6-.6-3.6-1.9-3.6s-1.6 2-1.9 3.6c-.3 1.5-1.1 2.9-2.3 2.1-1.4-1-1.6-3.8-1.9-5.9-.3-1.8-.9-3.2-1.4-4.9-.7-2.4-.4-5.4 1.7-6.6z"
      fill={fill}
      stroke={stroke}
      strokeWidth={width}
      strokeLinejoin="round"
    />
  </svg>
);

// A checkbox whose tick draws itself as `p` goes 0→1.
export const Tick: React.FC<{ p: number; size?: number; ink?: string; box?: boolean }> = ({ p, size = 36, ink = color.forest, box = true }) => {
  const len = 22;
  return (
    <svg width={size} height={size} viewBox="0 0 36 36">
      {box && <rect x="2" y="2" width="32" height="32" rx="7" fill="none" stroke={ink} strokeOpacity={0.35} strokeWidth="2" />}
      <path
        d="M9 18.5l6 6 12-13"
        fill="none"
        stroke={ink}
        strokeWidth="3.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={len + 4}
        strokeDashoffset={(len + 4) * (1 - p)}
      />
    </svg>
  );
};

// Simple wall clock whose hand sweeps with `turns` (0..n) and whose face drains with `drain` (0..1).
export const Clock: React.FC<{ turns: number; drain: number; size?: number }> = ({ turns, drain, size = 120 }) => {
  const r = 50;
  const a = drain * Math.PI * 2;
  const x = 60 + r * Math.sin(a);
  const y = 60 - r * Math.cos(a);
  const large = drain > 0.5 ? 1 : 0;
  const hand = turns * 360;
  return (
    <svg width={size} height={size} viewBox="0 0 120 120">
      <circle cx="60" cy="60" r="56" fill={color.ivory} stroke={color.forest} strokeWidth="3" />
      {drain > 0.001 && drain < 0.999 && (
        <path d={`M60 60 L60 10 A50 50 0 ${large} 1 ${x} ${y} Z`} fill={color.orange} fillOpacity={0.28} />
      )}
      {drain >= 0.999 && <circle cx="60" cy="60" r="50" fill={color.orange} fillOpacity={0.28} />}
      {Array.from({ length: 12 }, (_, i) => (
        <line key={i} x1="60" y1="9" x2="60" y2={i % 3 === 0 ? 17 : 14} stroke={color.forest} strokeWidth={i % 3 === 0 ? 3 : 1.6} transform={`rotate(${i * 30} 60 60)`} />
      ))}
      <line x1="60" y1="60" x2="60" y2="22" stroke={color.forest} strokeWidth="3.5" strokeLinecap="round" transform={`rotate(${hand} 60 60)`} />
      <line x1="60" y1="60" x2="60" y2="34" stroke={color.forest} strokeWidth="5" strokeLinecap="round" transform={`rotate(${hand / 12} 60 60)`} />
      <circle cx="60" cy="60" r="5" fill={color.forest} />
    </svg>
  );
};
