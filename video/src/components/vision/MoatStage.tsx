import React from "react";
import { random, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { evolvePath } from "@remotion/paths";
import { color, ease, font, springs } from "../../theme";
import { lineAt, wordAt } from "../../vo";
import { Sfx } from "../../audio";
import { film, lerp, ramp, seg, window01 } from "./util";

const w2 = (word: string, nth = 0) => wordAt("vision", 2, word, nth);
const w3 = (word: string, nth = 0) => wordAt("vision", 3, word, nth);

const CORE = { x: 960, y: 500, r: 86 };
const RING = 280;
const ROW_Y = 968;
const CLINICS = Array.from({ length: 30 }, (_, i) => ({ x: 250 + i * (1420 / 29), y: ROW_Y + (i % 2 ? 14 : -6), seed: i }));
const MORE_CLINICS = Array.from({ length: 29 }, (_, i) => ({ x: 250 + (i + 0.5) * (1420 / 29), y: ROW_Y + 44 + (i % 2 ? -8 : 6), seed: 100 + i }));

// ── Act 2a: the split — public rules vs private decisions ─────────────────────────────────────────────
const GuidePage: React.FC<{ p: number; out: number }> = ({ p, out }) => {
  const lines = [0.92, 0.8, 0.95, 0.62, 0.88, 0.74, 0.9, 0.55];
  return (
    <div
      style={{
        position: "absolute",
        left: 560 - 290,
        top: 520 - 200,
        width: 580,
        height: 400,
        opacity: p * (1 - out),
        transform: `translateY(${(1 - p) * 40}px) scale(${lerp(1, 0.9, out)})`,
      }}
    >
      <div style={{ fontFamily: font.mono, fontSize: 18, letterSpacing: "0.14em", color: film.boneDim }}>THE RULES</div>
      <div style={{ fontFamily: font.display, fontSize: 64, color: film.bone, lineHeight: 1.1 }}>Public.</div>
      <div
        style={{
          marginTop: 18,
          height: 250,
          borderRadius: 10,
          background: "rgba(230,236,227,0.1)",
          border: `1.5px solid ${film.boneFaint}`,
          padding: "22px 26px",
          boxShadow: "0 0 60px rgba(170,210,190,0.12)",
        }}
      >
        <div style={{ fontFamily: font.mono, fontSize: 16, color: film.boneDim, letterSpacing: "0.08em" }}>DENTAL BENEFITS GUIDE · 6.3.5</div>
        {lines.map((w, i) => (
          <div
            key={i}
            style={{
              marginTop: i === 0 ? 18 : 12,
              height: 10,
              width: `${w * 100}%`,
              borderRadius: 5,
              background: i === 3 ? film.metal : film.boneFaint,
              opacity: i === 3 ? 0.9 : 1,
            }}
          />
        ))}
      </div>
    </div>
  );
};

const Envelope: React.FC<{ w: number; h: number; seal?: number; glow?: number }> = ({ w, h, seal = 1, glow = 0 }) => (
  <svg width={w} height={h} viewBox="0 0 100 64" style={{ overflow: "visible" }}>
    <rect x={1} y={1} width={98} height={62} rx={4} fill="rgba(230,236,227,0.1)" stroke={film.bone} strokeWidth={1.6} />
    <path d="M 1 3 L 50 38 L 99 3" fill="none" stroke={film.bone} strokeWidth={1.6} strokeLinejoin="round" />
    {glow > 0 && <rect x={1} y={1} width={98} height={62} rx={4} fill={film.metal} opacity={glow * 0.35} />}
    <g transform={`translate(50 38) scale(${seal})`}>
      <circle r={11} fill={film.metal} />
      {/* padlock */}
      <rect x={-4.5} y={-1.5} width={9} height={7} rx={1.2} fill={film.ink} />
      <path d="M -2.8 -1.5 L -2.8 -4 A 2.8 2.8 0 0 1 2.8 -4 L 2.8 -1.5" fill="none" stroke={film.ink} strokeWidth={1.6} />
    </g>
  </svg>
);

const Sealed: React.FC<{ p: number; fly: number }> = ({ p, fly }) => {
  // On "Every decision…" the sealed envelope flies into the centre and becomes the model's core.
  const x = lerp(1360, CORE.x, ease.inOut(fly));
  const y = lerp(520, CORE.y, ease.inOut(fly));
  const s = lerp(1, 0.18, ease.inOut(fly));
  return (
    <div style={{ position: "absolute", left: x - 290, top: y - 200, width: 580, height: 400, opacity: p * (1 - seg(fly, 0.85, 1)), transform: `translateY(${(1 - p) * 40}px) scale(${s})` }}>
      <div style={{ opacity: 1 - fly * 3 }}>
        <div style={{ fontFamily: font.mono, fontSize: 18, letterSpacing: "0.14em", color: film.boneDim }}>THE DECISIONS</div>
        <div style={{ fontFamily: font.display, fontSize: 64, color: film.bone, lineHeight: 1.1 }}>Private.</div>
      </div>
      <div style={{ marginTop: 26, display: "flex", justifyContent: "center" }}>
        <Envelope w={400} h={256} />
      </div>
    </div>
  );
};

// ── Act 2b: clinics send decisions into the model ─────────────────────────────────────────────────────
const Flyer: React.FC<{ x0: number; y0: number; launch: number; dur: number; frame: number; tx?: number; ty?: number }> = ({ x0, y0, launch, dur, frame, tx = CORE.x, ty = CORE.y }) => {
  const t = (frame - launch) / dur;
  if (t <= 0 || t >= 1) return null;
  const e = ease.inOut(t);
  const cx = (x0 + tx) / 2;
  const cy = Math.min(y0, ty) - 120;
  const x = (1 - e) * (1 - e) * x0 + 2 * (1 - e) * e * cx + e * e * tx;
  const y = (1 - e) * (1 - e) * y0 + 2 * (1 - e) * e * cy + e * e * ty;
  const s = lerp(1, 0.35, e);
  return (
    <div style={{ position: "absolute", left: x - 13, top: y - 8, transform: `scale(${s})`, opacity: Math.min(1, t * 6, (1 - t) * 5) }}>
      <Envelope w={26} h={17} seal={0.9} glow={e} />
    </div>
  );
};

const Chip: React.FC<{ text: string; x: number; y: number; gx: number; gy: number; at: number; gather: number; frame: number; fps: number }> = ({
  text,
  x,
  y,
  gx,
  gy,
  at,
  gather,
  frame,
  fps,
}) => {
  const s = spring({ frame: frame - at, fps, config: springs.snappy });
  if (frame < at || gather >= 1) return null;
  const g = ease.inOut(gather);
  return (
    <div
      style={{
        position: "absolute",
        left: lerp(x, gx, g),
        top: lerp(y, gy, g),
        transform: `translate(-50%, -50%) scale(${s * lerp(1, 0.7, g)})`,
        opacity: 1 - seg(gather, 0.75, 1),
        padding: "12px 26px",
        borderRadius: 999,
        border: `2px solid ${film.bone}`,
        background: "rgba(14,31,25,0.85)",
        fontFamily: font.sans,
        fontWeight: 500,
        fontSize: 32,
        color: film.bone,
        whiteSpace: "nowrap",
        boxShadow: `0 0 30px ${film.metalGlow}`,
      }}
    >
      {text}
    </div>
  );
};

// ── Act 2b': one labelled example, tied to the exact chart that was sent ─────────────────────────────
const CARD = { x: 1180, y: 350, w: 580, h: 300 };
const SNAP = { x: 160, y: 380, w: 560, h: 240 };
const ROWS = [
  { tag: "SENT", text: "request + chart snapshot" },
  { tag: "BACK", text: "the payer's decision" },
  { tag: "WHY", text: "the reason, by clause" },
];
const rowY = (i: number) => CARD.y + 104 + i * 58;

const ExampleCard: React.FC<{ p: number; absorb: number }> = ({ p, absorb }) => {
  if (p <= 0 || absorb >= 1) return null;
  const a = ease.inOut(absorb);
  return (
    <div
      style={{
        position: "absolute",
        left: CARD.x,
        top: CARD.y,
        width: CARD.w,
        height: CARD.h,
        borderRadius: 16,
        background: "rgba(14,31,25,0.92)",
        border: `1.5px solid rgba(239,134,91,0.7)`,
        boxShadow: `0 0 50px rgba(239,134,91,0.22)`,
        padding: "22px 30px",
        opacity: p * (1 - seg(absorb, 0.6, 1)),
        transform: `translate(${(CORE.x - (CARD.x + CARD.w / 2)) * a}px, ${(CORE.y - (CARD.y + CARD.h / 2)) * a}px) scale(${lerp(lerp(0.94, 1, p), 0.12, a)})`,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: font.mono, fontSize: 17, letterSpacing: "0.14em" }}>
        <span style={{ color: film.metal }}>LABELLED EXAMPLE</span>
        <span style={{ color: film.boneDim }}>✦ TRAINING DATA</span>
      </div>
      {ROWS.map((r, i) => (
        <div key={r.tag} style={{ position: "absolute", left: 30, top: rowY(i) - CARD.y - 20, display: "flex", alignItems: "baseline", gap: 22, opacity: seg(p, 0.3 + i * 0.2, 0.6 + i * 0.2) }}>
          <span style={{ fontFamily: font.mono, fontSize: 17, letterSpacing: "0.12em", color: film.metal, width: 60 }}>{r.tag}</span>
          <span style={{ fontFamily: font.display, fontSize: 36, color: film.bone }}>{r.text}</span>
        </div>
      ))}
    </div>
  );
};

const ChartSnap: React.FC<{ p: number; absorb: number }> = ({ p, absorb }) => {
  if (p <= 0 || absorb >= 1) return null;
  const a = ease.inOut(absorb);
  const teeth = Array.from({ length: 16 }, (_, i) => i);
  return (
    <div
      style={{
        position: "absolute",
        left: SNAP.x,
        top: SNAP.y,
        width: SNAP.w,
        height: SNAP.h,
        borderRadius: 16,
        background: "rgba(14,31,25,0.92)",
        border: `1.5px solid ${film.boneFaint}`,
        boxShadow: "0 0 40px rgba(170,210,190,0.14)",
        padding: "22px 30px",
        opacity: p * (1 - seg(absorb, 0.6, 1)),
        transform: `translate(${(CORE.x - (SNAP.x + SNAP.w / 2)) * a}px, ${(CORE.y - (SNAP.y + SNAP.h / 2)) * a}px) scale(${lerp(lerp(0.94, 1, p), 0.12, a)})`,
      }}
    >
      <div style={{ fontFamily: font.mono, fontSize: 17, letterSpacing: "0.14em", color: film.boneDim }}>THE EXACT CHART SENT</div>
      {[0, 1].map((row) => (
        <div key={row} style={{ display: "flex", gap: 6, marginTop: row ? 8 : 20 }}>
          {teeth.map((i) => {
            const hot = row === 1 && i === 2; // #46
            return <div key={i} style={{ width: 24, height: 20, borderRadius: 5, border: `1.5px solid ${hot ? film.metal : film.boneFaint}`, background: hot ? "rgba(239,134,91,0.45)" : "rgba(230,236,227,0.06)" }} />;
          })}
        </div>
      ))}
      <div style={{ fontFamily: font.mono, fontSize: 17, color: film.boneDim, marginTop: 20, lineHeight: 1.6 }}>
        PA #46 · 2023-11-14
        <br />
        perio · 4-point · plan · note
      </div>
    </div>
  );
};

// ── Act 2c: flywheel → moat → intelligence layer ─────────────────────────────────────────────────────
const arc = (a0: number, a1: number, r: number) => {
  const p = (a: number) => [CORE.x + r * Math.cos((a * Math.PI) / 180), CORE.y + r * Math.sin((a * Math.PI) / 180)];
  const [x0, y0] = p(a0);
  const [x1, y1] = p(a1);
  return `M ${x0} ${y0} A ${r} ${r} 0 ${a1 - a0 > 180 ? 1 : 0} 1 ${x1} ${y1}`;
};

const FLY_LABELS = [
  { text: "More clinics", a: -90 },
  { text: "More decisions", a: 30 },
  { text: "Sharper models ✦", a: 150 },
];

const PAYERS = ["CDCP", "NIHB", "Provincial plans", "Private insurers"];
const CLINIC_COL = Array.from({ length: 7 }, (_, i) => 250 + i * 100);
const PAYER_ROWS = PAYERS.map((_, i) => 330 + i * 125);
const BAND = { w: 170, h: 740 };

export const MoatStage: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const l1 = lineAt("vision", 2);
  if (frame < l1.from - 10) return null;

  const cue = {
    rules: w2("rules"),
    decisions: w2("decisions"),
    every: w2("Every"),
    clinics: w2("request"),
    model: w2("checks"),
    sent: w2("request"),
    back: w2("answer"),
    why: w2("becomes"),
    labelled: w2("labelled"),
    exact: w2("exact"),
    chart: w2("chart"),
    prop: w2("proprietary"),
    tied: w2("tied"),
    sharpens: w2("sharpens"),
    grows: w2("every", 2),
    moat: w3("moat"),
    intel: w3("intelligence"),
    clinics2: w3("clinics"),
    payers: w3("payers"),
    knowing: w3("knowing"),
  };

  const leftIn = ramp(frame, cue.rules - 8, cue.rules + 10);
  const leftOut = ramp(frame, cue.every - 4, cue.every + 14);
  const rightIn = ramp(frame, cue.decisions - 8, cue.decisions + 10);
  const fly = ramp(frame, cue.every - 2, cue.every + 26, ease.inOut);

  const coreIn = spring({ frame: frame - (cue.every + 20), fps, config: springs.overshoot });
  const layerMorph = ramp(frame, cue.intel - 4, cue.intel + 30, ease.inOut);
  const rowIn = (i: number) => ramp(frame, cue.every + 6 + i * 1.4, cue.every + 18 + i * 1.4);
  const rowOut = ramp(frame, cue.intel - 6, cue.intel + 12);
  const moreIn = (i: number) => ramp(frame, cue.grows - 6 + i * 1.2, cue.grows + 6 + i * 1.2);

  // Envelopes: each clinic sends one every ~45 frames; the flow doubles once "it grows with every clinic".
  const flyers: React.ReactNode[] = [];
  const flowEnd = cue.moat - 12;
  if (frame > cue.clinics && frame < flowEnd + 40) {
    CLINICS.forEach((c, i) => {
      for (let k = 0; k < 12; k++) {
        const launch = cue.clinics + Math.floor(random(`l${i}-${k}`) * 40) + k * 44;
        if (launch > flowEnd) break;
        flyers.push(<Flyer key={`a${i}-${k}`} x0={c.x} y0={c.y} launch={launch} dur={34} frame={frame} />);
      }
    });
    MORE_CLINICS.forEach((c, i) => {
      for (let k = 0; k < 6; k++) {
        const launch = cue.grows + 10 + Math.floor(random(`m${i}-${k}`) * 30) + k * 30;
        if (launch > flowEnd) break;
        flyers.push(<Flyer key={`b${i}-${k}`} x0={c.x} y0={c.y} launch={launch} dur={34} frame={frame} />);
      }
    });
  }
  // Absorbed-so-far drives the core's inner glow.
  const absorbed = ramp(frame, cue.clinics + 30, cue.moat);

  const gather = ramp(frame, cue.labelled - 4, cue.labelled + 18, ease.inOut);
  const cardIn = ramp(frame, cue.labelled + 6, cue.labelled + 26);
  const snapIn = ramp(frame, cue.exact - 8, cue.exact + 10);
  const tether = ramp(frame, cue.chart - 6, cue.chart + 16, ease.inOut);
  const absorb = ramp(frame, cue.prop - 2, cue.prop + 22, ease.inOut);
  const datasetIn = ramp(frame, cue.prop + 10, cue.prop + 28);
  const tiedIn = ramp(frame, cue.tied - 4, cue.tied + 12);
  const labelOut = ramp(frame, cue.moat - 8, cue.moat + 4);

  // Flywheel: three arcs; arrows march faster as the dataset grows, then lock into one ring on "moat".
  const wheelIn = ramp(frame, cue.prop + 16, cue.prop + 48);
  const lock = ramp(frame, cue.moat - 3, cue.moat + 10, ease.out);
  const speed = 2 + 10 * ramp(frame, cue.grows - 10, cue.moat - 6, ease.inOut);
  const march = (frame - cue.prop) * speed;
  const gap = lerp(14, 0, lock);
  const ringW = lerp(5, 14, lock);
  const shock = ramp(frame, cue.moat, cue.moat + 34);
  const moatLabel = window01(frame, cue.moat + 4, cue.intel + 6, 12);

  // Ring → vertical band: a circle is a rounded rect whose corner radius is half its size.
  const bw = lerp(RING * 2, BAND.w, layerMorph);
  const bh = lerp(RING * 2, BAND.h, layerMorph);
  const brx = lerp(RING, BAND.w / 2, layerMorph);
  const bandY = lerp(CORE.y, 540, layerMorph);
  const coreY = bandY;

  const colIn = (i: number) => spring({ frame: frame - (cue.clinics2 - 14 + i * 3), fps, config: springs.snappy });
  const payerIn = (i: number) => spring({ frame: frame - (cue.payers - 18 + i * 4), fps, config: springs.snappy });
  const linkL = ramp(frame, cue.clinics2 - 10, cue.clinics2 + 22);
  const linkR = ramp(frame, cue.payers - 12, cue.payers + 16);
  const layerTitle = ramp(frame, cue.intel, cue.intel + 18);

  return (
    <div style={{ position: "absolute", inset: 0 }}>
      {/* "Here's what no one can copy." */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 470,
          textAlign: "center",
          opacity: window01(frame, l1.from + 2, cue.rules - 4, 10),
          transform: `translateY(${(1 - ramp(frame, l1.from + 2, l1.from + 22)) * 18}px)`,
          fontFamily: font.display,
          fontStyle: "italic",
          fontSize: 96,
          color: film.bone,
        }}
      >
        What no one can copy
      </div>
      <GuidePage p={leftIn} out={leftOut} />
      <Sealed p={rightIn} fly={fly} />

      {/* clinics along the bottom, then more of them */}
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        {CLINICS.map((c, i) => (
          <g key={i} opacity={rowIn(i) * (1 - rowOut)}>
            <circle cx={c.x} cy={c.y} r={9} fill={film.bone} />
            <circle cx={c.x} cy={c.y} r={16} fill="none" stroke={film.boneFaint} strokeWidth={1.5} />
          </g>
        ))}
        {MORE_CLINICS.map((c, i) => (
          <circle key={i} cx={c.x} cy={c.y} r={7} fill={film.bone} opacity={moreIn(i) * (1 - rowOut) * 0.8} />
        ))}
      </svg>
      <div style={{ position: "absolute", left: 72, top: ROW_Y - 64, opacity: ramp(frame, cue.clinics - 6, cue.clinics + 10) * (1 - rowOut), fontFamily: font.mono, fontSize: 17, letterSpacing: "0.14em", color: film.boneDim }}>
        OPHI CLINICS
      </div>
      {flyers}

      {/* flywheel arcs and shockwave */}
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
        <defs>
          <filter id="moatGlow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation={lerp(4, 10, lock)} result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {wheelIn > 0 && layerMorph < 0.02 && (
          <g filter="url(#moatGlow)">
            {[0, 1, 2].map((k) => {
              const a0 = -90 + k * 120 + gap / 2;
              const a1 = -90 + (k + 1) * 120 - gap / 2;
              const d = arc(a0, a1, RING);
              const ev = evolvePath(seg(wheelIn, k * 0.25, 0.5 + k * 0.25), d);
              return (
                <g key={k}>
                  <path d={d} fill="none" stroke={lock > 0 ? film.metal : film.bone} strokeOpacity={lerp(0.9, 1, lock)} strokeWidth={ringW} strokeLinecap="round" {...ev} />
                  {/* marching dashes: the data moving round the loop */}
                  <path d={d} fill="none" stroke={film.metal} strokeWidth={ringW * 0.6} strokeDasharray="10 34" strokeDashoffset={-march} opacity={seg(wheelIn, 0.6, 1) * (1 - lock)} strokeLinecap="round" />
                  {/* arrowhead at the arc's end */}
                  {(() => {
                    const ang = (a1 * Math.PI) / 180;
                    const ex = CORE.x + RING * Math.cos(ang);
                    const ey = CORE.y + RING * Math.sin(ang);
                    const rot = a1 + 90;
                    return (
                      <path
                        d="M -12 -10 L 4 0 L -12 10"
                        fill="none"
                        stroke={film.bone}
                        strokeWidth={5}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        transform={`translate(${ex} ${ey}) rotate(${rot})`}
                        opacity={seg(wheelIn, 0.55 + k * 0.15, 0.7 + k * 0.15) * (1 - lock)}
                      />
                    );
                  })()}
                </g>
              );
            })}
          </g>
        )}
        {shock > 0 && shock < 1 && (
          <circle cx={CORE.x} cy={CORE.y} r={lerp(RING, 560, shock)} fill="none" stroke={film.metal} strokeWidth={lerp(10, 1, shock)} opacity={(1 - shock) * 0.8} />
        )}
        {/* the moat ring morphs into the intelligence layer */}
        {layerMorph > 0 && (
          <rect
            x={CORE.x - bw / 2}
            y={bandY - bh / 2}
            width={bw}
            height={bh}
            rx={brx}
            fill={`rgba(239,134,91,${0.1 * layerMorph})`}
            stroke={film.metal}
            strokeWidth={lerp(14, 4, layerMorph)}
            filter="url(#moatGlow)"
          />
        )}
        {/* links: clinics → layer → payers */}
        {CLINIC_COL.map((y, i) => {
          const d = `M 350 ${y} C 600 ${y}, 700 ${lerp(y, 540, 0.5)}, ${960 - BAND.w / 2} ${lerp(y, 540, 0.55)}`;
          return <path key={i} d={d} fill="none" stroke={film.boneDim} strokeWidth={2} {...evolvePath(linkL, d)} />;
        })}
        {PAYER_ROWS.map((y, i) => {
          const d = `M ${960 + BAND.w / 2} ${lerp(y, 540, 0.55)} C 1220 ${lerp(y, 540, 0.5)}, 1320 ${y}, 1520 ${y}`;
          return <path key={i} d={d} fill="none" stroke={film.boneDim} strokeWidth={2} {...evolvePath(linkR, d)} />;
        })}
        {/* traffic once both sides are drawn: requests go out checked (orange →), decisions come back (bone ←) */}
        {linkR >= 1 &&
          CLINIC_COL.map((y, i) => {
            const y1 = lerp(y, 540, 0.55);
            const out = ((frame - cue.payers + i * 7) % 28) / 28;
            const back = ((frame - cue.payers + i * 11 + 13) % 34) / 34;
            return (
              <g key={`p${i}`}>
                <circle cx={lerp(350, 960 - BAND.w / 2, out)} cy={lerp(y, y1, ease.inOut(out))} r={5} fill={film.metal} />
                <circle cx={lerp(960 - BAND.w / 2, 350, back)} cy={lerp(y1, y, ease.inOut(back))} r={4} fill={film.bone} opacity={0.85} />
              </g>
            );
          })}
        {linkR >= 1 &&
          PAYER_ROWS.map((y, i) => {
            const y0 = lerp(y, 540, 0.55);
            const out = ((frame - cue.payers + i * 9) % 30) / 30;
            const back = ((frame - cue.payers + i * 5 + 17) % 36) / 36;
            return (
              <g key={`q${i}`}>
                <circle cx={lerp(960 + BAND.w / 2, 1520, out)} cy={lerp(y0, y, ease.inOut(out))} r={5} fill={film.metal} />
                <circle cx={lerp(1520, 960 + BAND.w / 2, back)} cy={lerp(y, y0, ease.inOut(back))} r={4} fill={film.bone} opacity={0.85} />
              </g>
            );
          })}
        {/* clinic column nodes */}
        {CLINIC_COL.map((y, i) => (
          <g key={`c${i}`} transform={`translate(330 ${y}) scale(${colIn(i)})`}>
            <circle r={13} fill={film.bone} />
            <circle r={24} fill="none" stroke={film.boneFaint} strokeWidth={1.5} />
          </g>
        ))}
        {PAYER_ROWS.map((y, i) => (
          <circle key={`d${i}`} cx={1540} cy={y} r={10 * payerIn(i)} fill={film.metal} />
        ))}
      </svg>

      {/* flywheel labels */}
      {FLY_LABELS.map((l, k) => {
        const r = RING + 30;
        const x = CORE.x + r * Math.cos((l.a * Math.PI) / 180);
        const y = CORE.y + r * Math.sin((l.a * Math.PI) / 180);
        const anchor = l.a === -90 ? "translate(-50%, -100%)" : l.a < 90 ? "translate(0, -30%)" : "translate(-100%, -30%)";
        const at = k === 2 ? cue.sharpens - 4 : cue.prop + 22 + k * 12;
        const o = ramp(frame, at, at + 14) * (1 - ramp(frame, cue.moat - 4, cue.moat + 6));
        return (
          <div key={k} style={{ position: "absolute", left: x, top: y, transform: `${anchor} translateY(${(1 - o) * 10}px)`, opacity: o, fontFamily: font.display, fontSize: 40, color: film.bone, whiteSpace: "nowrap" }}>
            {l.text}
          </div>
        );
      })}

      {/* the model's core */}
      {frame >= cue.every + 16 && (
        <div
          style={{
            position: "absolute",
            left: CORE.x - CORE.r,
            top: coreY - CORE.r,
            width: CORE.r * 2,
            height: CORE.r * 2,
            borderRadius: "50%",
            transform: `scale(${coreIn})`,
            background: `radial-gradient(circle, rgba(239,134,91,${0.15 + 0.45 * absorbed}) 0%, rgba(14,31,25,0.95) 70%)`,
            border: `2px solid ${film.bone}`,
            boxShadow: `0 0 ${40 + 60 * absorbed}px rgba(239,134,91,${0.25 + 0.35 * absorbed})`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: font.display,
            fontSize: 58,
            color: film.bone,
            letterSpacing: "-0.02em",
          }}
        >
          ophi<span style={{ color: color.orange }}>.</span>
        </div>
      )}
      <div style={{ position: "absolute", left: CORE.x, top: CORE.y + CORE.r + 22, transform: "translateX(-50%)", textAlign: "center", whiteSpace: "nowrap" }}>
        <div style={{ opacity: ramp(frame, cue.model - 4, cue.model + 10) * (1 - datasetIn), fontFamily: font.mono, fontSize: 20, letterSpacing: "0.14em", color: film.boneDim, position: "absolute", left: "50%", transform: "translateX(-50%)" }}>
          ✦ OPHI&apos;S MODELS
        </div>
        <div style={{ opacity: datasetIn * (1 - labelOut) }}>
          <div style={{ fontFamily: font.display, fontSize: 42, color: film.bone }}>Proprietary dataset</div>
          <div style={{ fontFamily: font.mono, fontSize: 18, color: film.boneDim, marginTop: 4, opacity: tiedIn }}>real outcomes, tied to the chart</div>
        </div>
      </div>

      {/* the tether: this example is tied to the exact chart that produced it */}
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        {tether > 0 && absorb < 1 &&
          [`M ${SNAP.x + SNAP.w} ${CORE.y} L ${CORE.x - CORE.r - 6} ${CORE.y}`, `M ${CORE.x + CORE.r + 6} ${CORE.y} L ${CARD.x} ${CORE.y}`].map((d, k) => (
            <path key={k} d={d} stroke={film.metal} strokeWidth={3} fill="none" opacity={1 - seg(absorb, 0, 0.5)} {...evolvePath(tether, d)} />
          ))}
      </svg>
      <ChartSnap p={snapIn} absorb={absorb} />
      <ExampleCard p={cardIn} absorb={absorb} />
      <Chip text="What was sent" x={560} y={CORE.y} gx={CARD.x + 330} gy={rowY(0)} at={cue.sent - 6} gather={gather} frame={frame} fps={fps} />
      <Chip text="What came back" x={1360} y={CORE.y - 110} gx={CARD.x + 330} gy={rowY(1)} at={cue.back - 6} gather={gather} frame={frame} fps={fps} />
      <Chip text="Why" x={CORE.x} y={CORE.y - 200} gx={CARD.x + 330} gy={rowY(2)} at={cue.why - 4} gather={gather} frame={frame} fps={fps} />

      {/* moat title */}
      <div style={{ position: "absolute", left: CORE.x, top: CORE.y + RING + 34, transform: `translateX(-50%) scale(${lerp(0.9, 1, moatLabel)})`, opacity: moatLabel, textAlign: "center", whiteSpace: "nowrap" }}>
        <div style={{ fontFamily: font.display, fontSize: 64, color: film.bone, lineHeight: 1 }}>Our moat</div>
        <div style={{ fontFamily: font.mono, fontSize: 20, color: film.boneDim, marginTop: 8 }}>decision data that grows with every clinic</div>
      </div>

      {/* intelligence layer diagram */}
      <div style={{ position: "absolute", left: CORE.x, top: 540 - BAND.h / 2 - 76, transform: "translateX(-50%)", opacity: layerTitle, fontFamily: font.display, fontStyle: "italic", fontSize: 44, color: film.bone, whiteSpace: "nowrap" }}>
        the intelligence layer
      </div>
      <div style={{ position: "absolute", left: 72, top: 140, opacity: ramp(frame, cue.clinics2 - 16, cue.clinics2 + 4) }}>
        <div style={{ fontFamily: font.mono, fontSize: 17, letterSpacing: "0.14em", color: film.boneDim }}>CANADA&apos;S CLINICS</div>
        <div style={{ fontFamily: font.display, fontSize: 56, color: film.bone, lineHeight: 1.1 }}>17,857</div>
      </div>
      {PAYERS.map((p, i) => (
        <div key={p} style={{ position: "absolute", left: 1572, top: PAYER_ROWS[i] - 28, opacity: payerIn(i), transform: `translateX(${(1 - payerIn(i)) * 20}px)`, fontFamily: font.display, fontSize: 44, color: film.bone, whiteSpace: "nowrap" }}>
          {p}
        </div>
      ))}
      <div style={{ position: "absolute", left: 1572, top: 200, opacity: ramp(frame, cue.payers - 20, cue.payers), fontFamily: font.mono, fontSize: 17, letterSpacing: "0.14em", color: film.boneDim }}>
        PAYERS
      </div>

      <div style={{ position: "absolute", left: 0, right: 0, top: 960, display: "flex", justifyContent: "center", gap: 64, opacity: ramp(frame, cue.payers - 4, cue.payers + 14), fontFamily: font.sans, fontSize: 26, color: film.bone }}>
        <span><span style={{ display: "inline-block", width: 14, height: 14, borderRadius: 7, background: film.metal, marginRight: 12 }} />Requests go out checked</span>
        <span><span style={{ display: "inline-block", width: 12, height: 12, borderRadius: 6, background: film.bone, marginRight: 12 }} />Decisions come back as data</span>
      </div>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 1004,
          textAlign: "center",
          opacity: ramp(frame, cue.knowing - 4, cue.knowing + 16),
          transform: `translateY(${(1 - ramp(frame, cue.knowing - 4, cue.knowing + 16)) * 10}px)`,
          fontFamily: font.display,
          fontStyle: "italic",
          fontSize: 38,
          color: film.metal,
        }}
      >
        Knowing what&apos;s missing, before anything is sent.
      </div>
      <div
        style={{
          position: "absolute",
          left: 72,
          bottom: 30,
          opacity: window01(frame, cue.every, cue.intel, 14),
          fontFamily: font.sans,
          fontSize: 18,
          color: "rgba(230,236,227,0.6)",
        }}
      >
        Today the model trains on simulated decisions. With partner clinics, it learns from real ones.
      </div>

      <Sfx name="whoosh" at={cue.rules - 8} volume={0.2} />
      <Sfx name="whoosh" at={cue.decisions - 8} volume={0.2} />
      <Sfx name="whoosh" at={cue.every} volume={0.3} />
      <Sfx name="pop" at={cue.sent - 6} volume={0.25} />
      <Sfx name="pop" at={cue.back - 6} volume={0.25} />
      <Sfx name="pop" at={cue.why - 4} volume={0.25} />
      <Sfx name="whoosh" at={cue.labelled - 4} volume={0.22} />
      <Sfx name="click" at={cue.chart} volume={0.3} />
      <Sfx name="whoosh" at={cue.prop - 2} volume={0.25} />
      <Sfx name="riser" at={cue.moat - 32} volume={0.25} />
      <Sfx name="impact" at={cue.moat - 2} volume={0.5} />
      <Sfx name="shimmer" at={cue.moat} volume={0.35} />
      <Sfx name="whoosh" at={cue.intel - 4} volume={0.25} />
      <Sfx name="chime" at={cue.knowing} volume={0.2} />
    </div>
  );
};
