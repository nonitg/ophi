import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { color } from "../../theme";
import { ToothGlyph } from "./Glyphs";
import { pop, prog, shuffle } from "./util";

export const GRID = { cols: 10, rows: 10, w: 52, h: 64, gap: 12 } as const;
export const gridSize = { w: GRID.cols * GRID.w + (GRID.cols - 1) * GRID.gap, h: GRID.rows * GRID.h + (GRID.rows - 1) * GRID.gap };
export const cellCenter = (i: number) => ({
  x: (i % GRID.cols) * (GRID.w + GRID.gap) + GRID.w / 2,
  y: Math.floor(i / GRID.cols) * (GRID.h + GRID.gap) + GRID.h / 2,
});

type Props = {
  // Frame the cards start appearing, rippling out from `origin`.
  appearAt: number;
  origin: number;
  // Frame the survivors start lighting, one every `every` frames.
  lightAt: number;
  lit: number;
  every?: number;
};

// 100 request cards; `lit` of them survive (light up forest), the rest dim. Order is a fixed shuffle so
// survivors are scattered like a real population, and the origin card always survives.
export const RequestGrid: React.FC<Props> = ({ appearAt, origin, lightAt, lit, every = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const order = shuffle(
    Array.from({ length: 100 }, (_, i) => i).filter((i) => i !== origin),
    46,
  );
  const survivors = new Map<number, number>([[origin, 0], ...order.slice(0, lit - 1).map((i, k) => [i, k + 1] as [number, number])]);
  const o = cellCenter(origin);
  const dimAll = prog(frame, lightAt + 4, 20);
  return (
    <div style={{ position: "relative", width: gridSize.w, height: gridSize.h }}>
      {Array.from({ length: 100 }, (_, i) => {
        const c = cellCenter(i);
        const d = Math.hypot(c.x - o.x, c.y - o.y) / (GRID.w + GRID.gap);
        const inP = pop(frame, appearAt + d * 1.6, fps, "snappy");
        const rank = survivors.get(i);
        const litP = rank === undefined ? 0 : pop(frame, lightAt + rank * every, fps, "overshoot");
        const litOn = rank !== undefined && frame >= lightAt + rank * every;
        const dim = rank === undefined ? dimAll : 0;
        const scale = interpolate(inP, [0, 1], [0.55, 1]) * (litOn ? interpolate(litP, [0, 1], [1.18, 1]) : 1);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: c.x - GRID.w / 2,
              top: c.y - GRID.h / 2,
              width: GRID.w,
              height: GRID.h,
              borderRadius: 7,
              background: litOn ? color.forest : color.ivory,
              border: `1.5px solid ${litOn ? color.forest : "rgba(25,58,48,0.32)"}`,
              boxShadow: litOn ? "0 6px 14px rgba(15,36,29,0.22)" : "0 1px 2px rgba(15,36,29,0.08)",
              opacity: inP * (1 - dim * 0.62),
              transform: `scale(${scale})`,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              paddingTop: 9,
              gap: 5,
            }}
          >
            <ToothGlyph size={22} stroke={litOn ? color.ivory : color.forest} width={1.5} />
            <div style={{ width: 30, height: 3, borderRadius: 2, background: litOn ? "rgba(244,242,233,0.55)" : "rgba(25,58,48,0.22)" }} />
            <div style={{ width: 20, height: 3, borderRadius: 2, background: litOn ? color.orange : "rgba(25,58,48,0.14)" }} />
          </div>
        );
      })}
    </div>
  );
};
