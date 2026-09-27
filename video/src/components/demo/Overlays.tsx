import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { color, font, springs } from "../../theme";

const out = Easing.bezier(0.16, 1, 0.3, 1);

// The demo's screen layout: the app sits in STAGE; everything that explains it lives in the band below,
// so no caption ever covers app text.
export const STAGE = { x: 40, y: 28, w: 1840, h: 840 };
export const BAND_Y = STAGE.y + STAGE.h + 16; // chip row
export const RAIL_BOTTOM = 22;

// Visibility envelope for an overlay living between two frames: eased in, faded out.
export const useEnvelope = (start: number, end: number, inDur = 14, outDur = 12) => {
  const f = useCurrentFrame();
  const i = interpolate(f, [start, start + inDur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: out });
  const o = interpolate(f, [end - outDur, end], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return Math.min(i, o);
};

// Plain-words caption, right side of the band: what the shot means, readable on a phone.
export const Callout: React.FC<{
  start: number;
  end: number;
  title: string;
  tone?: "ink" | "paper" | "orange";
  icon?: React.ReactNode;
}> = ({ start, end, title, tone = "ink", icon }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const v = useEnvelope(start, end);
  const s = spring({ frame: f - start, fps, config: springs.snappy });
  if (v <= 0) return null;
  const bg = tone === "ink" ? color.forest : tone === "orange" ? color.orange : "#faf9f4";
  const fg = tone === "ink" ? color.ivory : color.ink;
  return (
    <div
      style={{
        position: "absolute",
        right: 1920 - STAGE.x - STAGE.w,
        top: BAND_Y + 4,
        transform: `translateY(${(1 - s) * 16}px)`,
        opacity: v,
        display: "flex",
        alignItems: "center",
        gap: 16,
        height: 70,
        padding: "0 30px 0 26px",
        borderRadius: 18,
        background: bg,
        color: fg,
        boxShadow: "0 14px 36px rgba(15,36,29,0.22), 0 2px 5px rgba(15,36,29,0.14)",
        whiteSpace: "nowrap",
        fontFamily: font.sans,
        fontWeight: 500,
        fontSize: 30,
        letterSpacing: "-0.01em",
      }}
    >
      {icon}
      {title}
    </div>
  );
};

export const Dot: React.FC<{ c?: string }> = ({ c = color.orange }) => <div style={{ width: 14, height: 14, borderRadius: 7, background: c, flex: "none" }} />;

// Glyphs for the tech chips: ✦ marks a trained model; the others are deterministic machinery.
const Glyph: React.FC<{ kind: ChipKind }> = ({ kind }) => {
  if (kind === "ai") return <span style={{ color: color.orange, fontSize: 30, lineHeight: 1 }}>✦</span>;
  const common = { fill: "none", stroke: color.orange, strokeWidth: 2.4, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  if (kind === "db")
    return (
      <svg width={28} height={30} viewBox="0 0 28 30">
        <ellipse cx={14} cy={6} rx={11} ry={4} {...common} />
        <path d="M3 6 v18 a11 4 0 0 0 22 0 v-18 M3 15 a11 4 0 0 0 22 0" {...common} />
      </svg>
    );
  if (kind === "watch")
    return (
      <svg width={30} height={30} viewBox="0 0 30 30">
        <path d="M2 15 h6 l3 -8 l5 16 l3 -8 h9" {...common} />
      </svg>
    );
  return (
    <svg width={26} height={30} viewBox="0 0 26 30">
      <path d="M5 3 h12 l5 5 v19 h-17 z M9 13 h9 M9 18 h9 M9 23 h6" {...common} />
    </svg>
  );
};

export type ChipKind = "ai" | "db" | "rules" | "watch";

// The tech/AI label: film-dark, DM Mono, types on like a readout, with a live dot. Left side of the band.
export const TechChip: React.FC<{ start: number; end: number; kind: ChipKind; label: string; detail: string }> = ({ start, end, kind, label, detail }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const v = useEnvelope(start, end, 12, 12);
  const s = spring({ frame: f - start, fps, config: springs.snappy });
  if (v <= 0) return null;
  const n = Math.max(0, Math.min(detail.length, Math.floor((f - start - 6) * 2.4)));
  const live = 0.45 + 0.55 * Math.abs(Math.sin(((f - start) / fps) * Math.PI * 1.2));
  return (
    <div
      style={{
        position: "absolute",
        left: STAGE.x,
        top: BAND_Y,
        opacity: v,
        transform: `translateY(${(1 - s) * 16}px)`,
        display: "flex",
        alignItems: "center",
        gap: 18,
        height: 78,
        padding: "0 26px 0 22px",
        borderRadius: 16,
        background: color.film,
        boxShadow: "0 14px 36px rgba(15,36,29,0.28), inset 0 0 0 1px rgba(239,134,91,0.28)",
        whiteSpace: "nowrap",
      }}
    >
      <Glyph kind={kind} />
      <div style={{ fontFamily: font.mono }}>
        <div style={{ fontSize: 19, letterSpacing: "0.12em", color: color.orange, display: "flex", alignItems: "center", gap: 10 }}>
          {label}
          <span style={{ width: 8, height: 8, borderRadius: 4, background: "#7fc59a", opacity: live, boxShadow: "0 0 8px #7fc59a" }} />
        </div>
        <div style={{ fontSize: 23, color: color.bone, marginTop: 5 }}>
          {detail.slice(0, n)}
          <span style={{ opacity: n < detail.length ? 1 : 0 }}>▌</span>
        </div>
      </div>
    </div>
  );
};

// Monitoring motif for the band: practice software ⇄ Ophi with a heartbeat pulse travelling the wire.
// `hot` frames light the practice-software end (a status read).
export const WatchMotif: React.FC<{ start: number; end: number; pms: string; hot?: number }> = ({ start, end, pms, hot = Infinity }) => {
  const f = useCurrentFrame();
  const v = useEnvelope(start, end, 14, 12);
  if (v <= 0) return null;
  const W = 1080;
  const wireL = 340;
  const wireR = W - 300;
  const t = f - start;
  const glow = f >= hot ? interpolate(f - hot, [0, 8, 30], [0, 1, 0.35], { extrapolateRight: "clamp" }) : 0;
  // Heartbeat trace scrolling along the wire.
  const pts: string[] = [];
  for (let x = 0; x <= wireR - wireL; x += 4) {
    const ph = ((x + t * 9) % 180) / 180;
    const y = ph > 0.42 && ph < 0.58 ? Math.sin(((ph - 0.42) / 0.16) * Math.PI * 2) * -18 : 0;
    pts.push(`${wireL + x},${39 + y}`);
  }
  const draw = interpolate(t, [0, 18], [0, 1], { extrapolateRight: "clamp", easing: out });
  return (
    <div style={{ position: "absolute", left: STAGE.x, top: BAND_Y, width: W, height: 78, opacity: v }}>
      <svg width={W} height={78} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <clipPath id="wm-draw">
            <rect x={wireL} y={0} width={(wireR - wireL) * draw} height={78} />
          </clipPath>
        </defs>
        <polyline points={pts.join(" ")} fill="none" stroke={color.orange} strokeWidth={3} strokeLinejoin="round" clipPath="url(#wm-draw)" />
      </svg>
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          height: 78,
          width: wireL - 14,
          borderRadius: 16,
          background: color.film,
          display: "flex",
          alignItems: "center",
          gap: 14,
          padding: "0 18px",
          boxShadow: `0 14px 36px rgba(15,36,29,0.28), 0 0 ${30 * glow}px rgba(127,197,154,${0.9 * glow}), inset 0 0 0 ${1 + 2 * glow}px rgba(127,197,154,${0.3 + 0.6 * glow})`,
          boxSizing: "border-box",
          whiteSpace: "nowrap",
        }}
      >
        <Glyph kind="db" />
        <div style={{ fontFamily: font.mono, lineHeight: 1.15 }}>
          <div style={{ fontSize: 17, letterSpacing: "0.12em", color: color.orange }}>PRACTICE SOFTWARE</div>
          <div style={{ fontSize: 22, color: color.bone }}>{pms}</div>
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          left: wireR + 14,
          top: 0,
          height: 78,
          width: W - wireR - 14,
          borderRadius: 16,
          background: color.film,
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "0 18px",
          boxShadow: "0 14px 36px rgba(15,36,29,0.28), inset 0 0 0 1px rgba(239,134,91,0.28)",
          boxSizing: "border-box",
          whiteSpace: "nowrap",
        }}
      >
        <Glyph kind="watch" />
        <div style={{ fontFamily: font.mono, lineHeight: 1.15 }}>
          <div style={{ fontSize: 17, letterSpacing: "0.12em", color: color.orange }}>OPHI · WATCHING</div>
          <div style={{ fontSize: 22, color: color.bone }}>claim status</div>
        </div>
      </div>
    </div>
  );
};

// The demo's through-line, bottom centre: which stage of the request we're watching.
const STAGES = ["Read", "Check", "Fix", "Confirm", "Send", "Watch", "Follow up"];
export const StageRail: React.FC<{ at: number[]; start?: number }> = ({ at, start = 0 }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const idx = Math.max(0, at.filter((a) => f >= a).length - 1);
  const pos = at.reduce((p, a, i) => (i === 0 ? 0 : p + spring({ frame: f - a, fps, config: springs.critical })), 0);
  const appear = interpolate(f, [start, start + 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: out });
  const W = 128;
  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        bottom: RAIL_BOTTOM,
        transform: `translate(-50%, ${(1 - appear) * 30}px)`,
        opacity: appear,
        display: "flex",
        padding: 6,
        borderRadius: 999,
        background: "rgba(25,58,48,0.94)",
        boxShadow: "0 10px 30px rgba(15,36,29,0.22)",
      }}
    >
      <div style={{ position: "absolute", left: 6 + pos * W, top: 6, width: W, height: 44, borderRadius: 999, background: color.orange }} />
      {STAGES.map((s, i) => (
        <div
          key={s}
          style={{
            position: "relative",
            width: W,
            height: 44,
            lineHeight: "44px",
            textAlign: "center",
            fontFamily: font.sans,
            fontWeight: 500,
            fontSize: 20,
            color: i === idx ? color.ink : "rgba(244,242,233,0.72)",
          }}
        >
          {s}
        </div>
      ))}
    </div>
  );
};

// Practice software → Ophi, drawn in the stage's left gutter while the app window is at full view:
// a database with records flowing into the window's edge.
export const PmsFlow: React.FC<{ start: number; end: number; x: number; y: number; toX: number; toY: number }> = ({ start, end, x, y, toX, toY }) => {
  const f = useCurrentFrame();
  const v = useEnvelope(start, end, 16, 14);
  if (v <= 0) return null;
  const sx = x + 204;
  const sy = y + 70;
  const p0 = [sx, sy], p1 = [sx + 50, sy], p2 = [toX - 60, toY], p3 = [toX, toY];
  const pointOn = (t: number) => {
    const u = 1 - t;
    return {
      x: u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
      y: u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1],
    };
  };
  const path = `M ${p0} C ${p1}, ${p2}, ${p3}`;
  const dots = Array.from({ length: 6 }, (_, i) => ((f - start) / 34 + i / 6) % 1);
  return (
    <div style={{ position: "absolute", inset: 0, opacity: v }}>
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        <path d={path} fill="none" stroke={color.orange} strokeWidth={3} strokeDasharray="2 12" strokeLinecap="round" opacity={0.8} />
        {dots.map((t, i) => {
          const pt = pointOn(t);
          return <rect key={i} x={pt.x - 9} y={pt.y - 6} width={18} height={12} rx={3} fill={color.orange} opacity={Math.sin(t * Math.PI)} />;
        })}
      </svg>
      <div
        style={{
          position: "absolute",
          left: x,
          top: y,
          width: 204,
          padding: "20px 16px",
          borderRadius: 18,
          background: color.film,
          boxShadow: "0 18px 50px rgba(15,36,29,0.25)",
          textAlign: "center",
          boxSizing: "border-box",
        }}
      >
        <svg width={60} height={70} viewBox="0 0 70 80">
          {[0, 1, 2].map((i) => (
            <g key={i} transform={`translate(0 ${i * 20})`}>
              <ellipse cx={35} cy={14} rx={30} ry={10} fill={i === 0 ? "rgba(239,134,91,0.25)" : "none"} stroke={color.orange} strokeWidth={3} />
              <path d="M5 14 v18 a30 10 0 0 0 60 0 v-18" fill="none" stroke={color.orange} strokeWidth={3} />
            </g>
          ))}
        </svg>
        <div style={{ fontFamily: font.mono, fontSize: 17, letterSpacing: "0.1em", color: color.orange, marginTop: 10 }}>PRACTICE SOFTWARE</div>
        <div style={{ fontFamily: font.sans, fontSize: 20, color: color.bone, marginTop: 4, lineHeight: 1.25 }}>charts · x-rays · perio</div>
      </div>
    </div>
  );
};

// Rubber stamp in orange ink: slams in with overshoot, settles slightly rotated. Drawn centred on its anchor.
export const Stamp: React.FC<{ at: number; text: string; size?: number; rotate?: number }> = ({ at, text, size = 1, rotate = -7 }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (f < at) return null;
  const s = spring({ frame: f - at, fps, config: { damping: 12, stiffness: 260, mass: 0.6 } });
  const scale = 2.2 - 1.2 * s;
  const o = interpolate(f - at, [0, 4], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 0, top: 0, transform: `translate(-50%,-50%) rotate(${rotate}deg) scale(${scale * size})`, opacity: o }}>
      <svg width={560} height={170} viewBox="0 0 560 170" style={{ overflow: "visible", display: "block" }}>
        <defs>
          <filter id="ink" x="-5%" y="-5%" width="110%" height="110%">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={7} result="n" />
            <feColorMatrix in="n" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.1 1.2" result="holes" />
            <feComposite in="SourceGraphic" in2="holes" operator="in" />
          </filter>
        </defs>
        <g filter="url(#ink)" fill="none" stroke={color.orange}>
          <rect x={8} y={8} width={544} height={154} rx={18} strokeWidth={9} />
          <rect x={24} y={24} width={512} height={122} rx={10} strokeWidth={3} />
          <text x={280} y={104} textAnchor="middle" fill={color.orange} stroke="none" style={{ fontFamily: font.sans, fontWeight: 700, fontSize: 64, letterSpacing: "0.08em" }}>
            {text}
          </text>
        </g>
      </svg>
    </div>
  );
};
