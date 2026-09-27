import React, { useMemo } from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";
import { evolvePath, getLength, getPointAtLength, getTangentAtLength } from "@remotion/paths";
import { font, springs } from "../../theme";
import { film, ramp } from "./util";

type Branch = { d: string; from: number; to: number; w: number; hairs?: number };
export type TreeNode = {
  id: string;
  x: number;
  y: number;
  at: number; // frame the node lights
  tag: string;
  name: string;
  detail?: React.ReactNode;
  side: "left" | "right";
  big?: boolean;
};

// Deterministic root hairs along a branch: short curls that sprout once the branch has grown past them.
const hairsFor = (d: string, n: number, seed: number) => {
  const L = getLength(d);
  return Array.from({ length: n }, (_, i) => {
    const f = 0.18 + (i / Math.max(1, n)) * 0.72 + ((seed * 7 + i * 13) % 10) / 200;
    const p = getPointAtLength(d, L * f) ?? { x: 0, y: 0 };
    const t = getTangentAtLength(d, L * f) ?? { x: 0, y: 1 };
    const side = (i + seed) % 2 === 0 ? 1 : -1;
    const len = 26 + ((seed * 11 + i * 17) % 30);
    // Normal to the tangent, bent downward like a root reaching for water.
    const nx = -t.y * side;
    const ny = t.x * side;
    const ex = p.x + nx * len + t.x * len * 0.5;
    const ey = p.y + ny * len + Math.abs(t.x) * len * 0.35 + len * 0.3;
    const cx = p.x + nx * len * 0.6;
    const cy = p.y + ny * len * 0.6;
    return { f, d: `M ${p.x} ${p.y} Q ${cx} ${cy} ${ex} ${ey}` };
  });
};

const Stroke: React.FC<{ d: string; progress: number; w: number; glow: number; color: string }> = ({ d, progress, w, glow, color }) => {
  if (progress <= 0) return null;
  const ev = evolvePath(progress, d);
  return (
    <>
      <path d={d} fill="none" stroke={color} strokeWidth={w * 2.6} strokeLinecap="round" opacity={0.12 * glow} {...ev} />
      <path d={d} fill="none" stroke={color} strokeWidth={w} strokeLinecap="round" {...ev} />
    </>
  );
};

type Props = {
  branches: Branch[];
  nodes: TreeNode[];
  // Extra brightness flowing up the roots (moat act: data returning), 0..1.
  flow?: number;
  opacity?: number;
};

export const RootTree: React.FC<Props> = ({ branches, nodes, flow = 0, opacity = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // Hairs never cross a node's label: drop any whose curl ends inside a label box.
  const boxes = useMemo(
    () =>
      nodes.map((n) => {
        const w = n.big ? 540 : 460;
        const pad = n.big ? 34 : 28;
        const x0 = n.side === "right" ? n.x + pad - 10 : n.x - pad - w;
        return { x0, x1: x0 + w + 10, y0: n.y - (n.big ? 54 : 46), y1: n.y + (n.big ? 80 : 74) };
      }),
    [nodes],
  );
  const hairs = useMemo(
    () =>
      branches.map((b, i) =>
        (b.hairs ? hairsFor(b.d, b.hairs, i + 1) : []).filter((h) => {
          const m = h.d.match(/([\d.-]+) ([\d.-]+)$/);
          const ex = m ? Number(m[1]) : 0;
          const ey = m ? Number(m[2]) : 0;
          return !boxes.some((bx) => ex > bx.x0 && ex < bx.x1 && ey > bx.y0 && ey < bx.y1);
        }),
      ),
    [branches, boxes],
  );

  return (
    <div style={{ position: "absolute", inset: 0, opacity }}>
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <filter id="rootGlow" filterUnits="userSpaceOnUse" x={0} y={0} width={1920} height={1080}>
            <feGaussianBlur stdDeviation="5" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <linearGradient id="flowGrad" x1="0" y1="1" x2="0" y2="0">
            <stop offset="0%" stopColor={film.metal} stopOpacity={0} />
            <stop offset="50%" stopColor={film.metal} stopOpacity={0.9} />
            <stop offset="100%" stopColor={film.metal} stopOpacity={0} />
          </linearGradient>
        </defs>
        <g filter="url(#rootGlow)">
          {branches.map((b, i) => {
            const p = ramp(frame, b.from, b.to);
            return (
              <g key={i}>
                <Stroke d={b.d} progress={p} w={b.w} glow={1} color={film.bone} />
                {hairs[i].map((h, j) => (
                  <Stroke key={j} d={h.d} progress={Math.min(1, Math.max(0, (p - h.f) / 0.18))} w={1.4} glow={0.6} color={film.boneDim} />
                ))}
                {flow > 0 && p >= 1 && (
                  // Data returning up the roots: a bright pulse travelling from tip to tooth.
                  <path
                    d={b.d}
                    fill="none"
                    stroke={film.metal}
                    strokeWidth={b.w * 0.9}
                    strokeLinecap="round"
                    opacity={flow}
                    strokeDasharray={`60 ${getLength(b.d)}`}
                    strokeDashoffset={-(getLength(b.d) - ((frame * 9 + i * 97) % (getLength(b.d) + 60)))}
                  />
                )}
              </g>
            );
          })}
        </g>
        {nodes.map((n) => {
          const on = spring({ frame: frame - n.at, fps, config: springs.overshoot });
          const pulse = ramp(frame, n.at, n.at + 26);
          if (frame < n.at - 2) return null;
          const r = n.big ? 13 : 10;
          return (
            <g key={n.id}>
              <circle cx={n.x} cy={n.y} r={r + pulse * 34} fill="none" stroke={film.metal} strokeWidth={2} opacity={(1 - pulse) * 0.9} />
              <circle cx={n.x} cy={n.y} r={r * 2.2 * on} fill={film.metalGlow} opacity={0.35} />
              <circle cx={n.x} cy={n.y} r={r * on} fill={film.bone} />
              <circle cx={n.x} cy={n.y} r={r * 0.45 * on} fill={film.metal} />
            </g>
          );
        })}
      </svg>
      {nodes.map((n) => {
        const p = ramp(frame, n.at, n.at + 16);
        if (p <= 0) return null;
        const pad = n.big ? 34 : 28;
        return (
          <div
            key={n.id}
            style={{
              position: "absolute",
              top: n.y - (n.big ? 44 : 36),
              ...(n.side === "right" ? { left: n.x + pad } : { right: 1920 - n.x + pad, textAlign: "right" as const }),
              opacity: p,
              transform: `translateX(${(1 - p) * (n.side === "right" ? -16 : 16)}px)`,
              whiteSpace: "nowrap",
            }}
          >
            <div style={{ fontFamily: font.mono, fontSize: 17, letterSpacing: "0.14em", color: film.metal, textTransform: "uppercase" }}>{n.tag}</div>
            <div style={{ fontFamily: font.display, fontSize: n.big ? 50 : 40, color: film.bone, lineHeight: 1.08, marginTop: 4 }}>{n.name}</div>
            {n.detail && <div style={{ fontFamily: font.mono, fontSize: n.big ? 24 : 21, color: film.boneDim, marginTop: 6 }}>{n.detail}</div>}
          </div>
        );
      })}
    </div>
  );
};
