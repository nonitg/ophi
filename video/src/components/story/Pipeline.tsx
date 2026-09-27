import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { color, font } from "../../theme";
import { lerp, pop, prog, seeded } from "./util";

export const PIPE = { w: 1680, h: 300 } as const;
const GATE = 1010; // x of the preauthorization gate
const BAND = { y: 108, h: 100 }; // the channel coverage flows through
const CY = BAND.y + BAND.h / 2;
const N = 46;
const DOT = 26;
const SPEED = 300; // px per second
const LOOP = PIPE.w + 60;
const SLOT = 31; // queue spacing
const RUSH = 2.6; // queued dots close up fast after the stall, so the jam reads within a second
const ROWS = 3;

// $13B of coverage flows toward care and jams at the preauthorization gate. Before `stallAt` the flow is
// free; after it, dots queue behind the gate (sticky, in arrival order) and only a trickle passes.
export const Pipeline: React.FC<{ at: number; stallAt: number }> = ({ at, stallAt }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const show = prog(frame, at, 18);
  const gate = prog(frame, stallAt - 4, 10);
  const chip = pop(frame, stallAt, fps, "overshoot");

  const rand = seeded(13);
  const dots = Array.from({ length: N }, (_, i) => ({ phase: rand(), lane: rand() - 0.5, passes: i % 8 === 0 }));
  const t = (frame - at) / fps;
  const ts = (stallAt - at) / fps;
  const wrap = (p: number) => ((p % LOOP) + LOOP) % LOOP - 30;
  const posAt = (d: (typeof dots)[number], time: number) => d.phase * LOOP + time * SPEED;

  // Queue slots at the stall: dots before the gate take slots nearest the gate first; dots already past it
  // leave the frame and rejoin at the back.
  const atStall = dots.map((d, i) => ({ i, x: wrap(posAt(d, ts)), d })).filter((o) => !o.d.passes);
  const before = atStall.filter((o) => o.x < GATE).sort((a, b) => b.x - a.x);
  const past = atStall.filter((o) => o.x >= GATE).sort((a, b) => b.x - a.x);
  const slot = new Map<number, { x: number; y: number }>();
  [...before, ...past].forEach((o, k) => {
    const col = Math.floor(k / ROWS);
    slot.set(o.i, { x: GATE - 30 - col * SLOT, y: CY + ((k % ROWS) - 1) * 29 });
  });

  return (
    <div style={{ position: "relative", width: PIPE.w, height: PIPE.h, opacity: show }}>
      {/* channel */}
      <div style={{ position: "absolute", left: 0, right: 0, top: BAND.y, height: BAND.h, borderRadius: BAND.h / 2, background: "rgba(25,58,48,0.06)", border: "2.5px solid rgba(25,58,48,0.2)" }} />
      <div style={{ position: "absolute", left: GATE, right: 0, top: BAND.y, height: BAND.h, borderRadius: `0 ${BAND.h / 2}px ${BAND.h / 2}px 0`, background: color.orange, opacity: 0.08 * gate }} />

      {dots.map((d, i) => {
        let x = wrap(posAt(d, t));
        let y = CY + d.lane * 50;
        let queued = false;
        const s = slot.get(i);
        if (frame >= stallAt && s) {
          const xs = wrap(posAt(d, ts)) + (t - ts) * SPEED * RUSH; // unwrapped since the stall
          const pastGate = wrap(posAt(d, ts)) >= GATE;
          const travel = pastGate ? (xs <= PIPE.w + 30 ? xs : xs - LOOP) : xs;
          const arrived = !(pastGate && xs <= PIPE.w + 30);
          x = arrived ? lerp(travel, Math.min(travel, s.x), prog(frame, stallAt, 10)) : travel;
          queued = arrived && travel >= s.x - 2;
          y = lerp(y, s.y, arrived ? prog(frame, stallAt, 14) : 0);
        }
        const inFrame = x > -DOT && x < PIPE.w + DOT;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - DOT / 2,
              top: y - DOT / 2,
              width: DOT,
              height: DOT,
              borderRadius: 99,
              background: queued ? color.orange : color.forest,
              opacity: inFrame ? 0.9 : 0,
            }}
          />
        );
      })}

      {/* gate */}
      <div
        style={{
          position: "absolute",
          left: GATE - 11,
          top: BAND.y - 36,
          width: 22,
          height: BAND.h + 72,
          borderRadius: 11,
          background: gate > 0.5 ? color.orange : color.forest,
          transform: `scaleY(${0.75 + 0.25 * gate})`,
          boxShadow: gate > 0.5 ? "0 0 0 8px rgba(239,134,91,0.18)" : "none",
        }}
      />
      <div style={{ position: "absolute", left: GATE - 250, width: 500, top: BAND.y + BAND.h + 50, textAlign: "center", fontFamily: font.mono, fontSize: 26, letterSpacing: "0.12em", color: gate > 0.5 ? color.orange : color.forest }}>
        PREAUTHORIZATION
      </div>
      <div
        style={{
          position: "absolute",
          left: GATE - 130,
          width: 260,
          top: -6,
          textAlign: "center",
          padding: "12px 0",
          borderRadius: 999,
          background: color.orange,
          color: color.ink,
          fontFamily: font.sans,
          fontWeight: 500,
          fontSize: 34,
          transform: `scale(${chip})`,
          opacity: chip > 0.01 ? 1 : 0,
        }}
      >
        Stalls here
      </div>
      <div style={{ position: "absolute", left: 4, top: 50, fontFamily: font.mono, fontSize: 26, letterSpacing: "0.12em", color: color.muted }}>COVERAGE →</div>
      <div style={{ position: "absolute", right: 4, top: 50, fontFamily: font.mono, fontSize: 26, letterSpacing: "0.12em", color: color.muted }}>CARE IN THE CHAIR</div>
    </div>
  );
};
