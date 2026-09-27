import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { color, ease, font, springs, type } from "../../theme";

// 0..1 eased ramp starting at `at`.
export const ramp = (frame: number, at: number, dur = 14, easing = ease.out) =>
  interpolate(frame, [at, at + dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing });

// Rise-and-fade wrapper: enters at `at`, optionally leaves at `out`.
export const Rise: React.FC<{ at: number; out?: number; dy?: number; dx?: number; style?: React.CSSProperties; children: React.ReactNode }> = ({ at, out = Infinity, dy = 28, dx = 0, style, children }) => {
  const frame = useCurrentFrame();
  const i = ramp(frame, at, 16);
  const o = Number.isFinite(out) ? 1 - ramp(frame, out, 12, ease.in) : 1;
  return <div style={{ opacity: i * o, transform: `translate(${(1 - i) * dx - (1 - o) * 40}px, ${(1 - i) * dy}px)`, ...style }}>{children}</div>;
};

// Words that rise one by one on the frames they are spoken.
export const SpokenLine: React.FC<{ words: { text: string; at: number; br?: boolean }[]; size: number; color?: string; italic?: boolean; style?: React.CSSProperties }> = ({ words, size, color: c = color.forest, italic, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ fontFamily: font.display, fontSize: size, color: c, lineHeight: 1.04, letterSpacing: "-0.015em", fontStyle: italic ? "italic" : "normal", ...style }}>
      {words.map((w, i) => {
        const p = spring({ frame: frame - w.at, fps, config: springs.critical });
        return (
          <React.Fragment key={i}>
            {w.br && <br />}
            <span style={{ display: "inline-block", opacity: p, transform: `translateY(${(1 - p) * size * 0.3}px)`, marginRight: "0.24em" }}>{w.text}</span>
          </React.Fragment>
        );
      })}
    </div>
  );
};

// Top rail naming the three reasons; titles appear as they are reached, all three stay for the summary.
export const PillarNav: React.FC<{ items: { title: string; at: number }[]; active: number; start: number; out?: number }> = ({ items, active, start, out = Infinity }) => {
  const frame = useCurrentFrame();
  const o = ramp(frame, start, 14) * (Number.isFinite(out) ? 1 - ramp(frame, out, 10) : 1);
  return (
    <div style={{ position: "absolute", top: 64, left: 120, right: 120, display: "flex", gap: 28, opacity: o }}>
      {items.map((it, i) => {
        const shown = ramp(frame, it.at, 12);
        const on = i === active;
        return (
          <div key={i} style={{ flex: 1, borderTop: `2px solid ${on ? color.orange : "rgba(25,58,48,0.18)"}`, paddingTop: 14, display: "flex", gap: 14, alignItems: "baseline" }}>
            <span style={{ fontFamily: font.mono, fontSize: type.label, color: on ? color.orange : color.muted }}>{String(i + 1).padStart(2, "0")}</span>
            <span style={{ fontFamily: font.sans, fontWeight: 500, fontSize: 24, color: on ? color.forest : color.muted, opacity: 0.25 + 0.75 * shown }}>
              {shown > 0.01 ? it.title : ""}
            </span>
          </div>
        );
      })}
    </div>
  );
};

// A chore that appears, then gets struck through in orange.
export const Chore: React.FC<{ text: string; at: number; strikeAt: number; size?: number }> = ({ text, at, strikeAt, size = 54 }) => {
  const frame = useCurrentFrame();
  const i = ramp(frame, at, 12);
  const s = ramp(frame, strikeAt, 10, ease.inOut);
  return (
    <div style={{ opacity: i, transform: `translateX(${(1 - i) * 30}px)`, display: "flex", alignItems: "center", gap: 22, margin: "18px 0" }}>
      <span style={{ fontFamily: font.mono, fontSize: 26, color: color.orange, width: 40 }}>{s > 0.5 ? "×" : "·"}</span>
      <span style={{ position: "relative", fontFamily: font.display, fontSize: size, color: s > 0.5 ? color.muted : color.forest, lineHeight: 1.1 }}>
        {text}
        <span style={{ position: "absolute", left: -6, right: -6, top: "56%", height: 5, borderRadius: 3, background: color.orange, transform: `scaleX(${s})`, transformOrigin: "0 50%" }} />
      </span>
    </div>
  );
};

// A clock whose hands run backwards: hours handed back to the clinic.
export const RewindClock: React.FC<{ at: number; dur: number; size?: number }> = ({ at, dur, size = 420 }) => {
  const frame = useCurrentFrame();
  const p = ramp(frame, at, dur, ease.inOut);
  const appear = ramp(frame, at - 8, 16);
  const minute = -720 * p;
  const hour = -60 * p + 60;
  const r = 180;
  // Trail: a 70° wedge behind the minute hand (it runs backwards, so the trail sits clockwise of it).
  const speed = interpolate(frame, [at, at + 20, at + dur - 20, at + dur], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const rad = (d: number) => ((d - 90) * Math.PI) / 180;
  const R = r - 18;
  const a0 = minute, a1 = minute + 70;
  const trail = speed > 0.01 ? `M 200 200 L ${200 + R * Math.cos(rad(a0))} ${200 + R * Math.sin(rad(a0))} A ${R} ${R} 0 0 1 ${200 + R * Math.cos(rad(a1))} ${200 + R * Math.sin(rad(a1))} Z` : "";
  return (
    <svg width={size} height={size} viewBox="0 0 400 400" style={{ opacity: appear, transform: `scale(${0.92 + 0.08 * appear})` }}>
      <circle cx={200} cy={200} r={r} fill={color.ivory} stroke={color.forest} strokeWidth={4} />
      {trail && <path d={trail} fill={color.orangeSoft} fillOpacity={0.6 * speed} />}
      {Array.from({ length: 12 }, (_, i) => {
        const t = (i * 30 * Math.PI) / 180;
        return <line key={i} x1={200 + (r - 14) * Math.sin(t)} y1={200 - (r - 14) * Math.cos(t)} x2={200 + (r - (i % 3 === 0 ? 38 : 26)) * Math.sin(t)} y2={200 - (r - (i % 3 === 0 ? 38 : 26)) * Math.cos(t)} stroke={color.forest} strokeWidth={i % 3 === 0 ? 5 : 3} strokeLinecap="round" />;
      })}
      <line x1={200} y1={200} x2={200} y2={96} stroke={color.forest} strokeWidth={9} strokeLinecap="round" transform={`rotate(${hour} 200 200)`} />
      <line x1={200} y1={200} x2={200} y2={52} stroke={color.orange} strokeWidth={6} strokeLinecap="round" transform={`rotate(${minute} 200 200)`} />
      <circle cx={200} cy={200} r={10} fill={color.forest} />
      {/* rewind chevrons */}
      <g transform="translate(200 356)" opacity={ramp(frame, at + 6, 12)}>
        <path d="M -8 -12 L -26 0 L -8 12 Z M 16 -12 L -2 0 L 16 12 Z" fill={color.orange} />
      </g>
    </svg>
  );
};

// A benefits-guide page: plain paper, no government branding.
const GuidePage: React.FC<{ effective: string; tint?: string; tag?: string; tagAt?: number }> = ({ effective, tint = color.ivory, tag, tagAt = Infinity }) => {
  const frame = useCurrentFrame();
  const t = Number.isFinite(tagAt) ? ramp(frame, tagAt, 12) : 0;
  return (
    <div style={{ position: "relative", width: 440, height: 560, background: tint, border: "1.5px solid rgba(25,58,48,0.22)", borderRadius: 6, boxShadow: "0 24px 50px rgba(15,36,29,0.16), 0 3px 8px rgba(15,36,29,0.08)", padding: "40px 38px", boxSizing: "border-box" }}>
      <div style={{ fontFamily: font.mono, fontSize: 15, color: color.muted, letterSpacing: "0.08em" }}>CANADIAN DENTAL CARE PLAN</div>
      <div style={{ fontFamily: font.display, fontSize: 44, color: color.forest, lineHeight: 1.05, marginTop: 12 }}>Dental Benefits Guide</div>
      <div style={{ marginTop: 28 }}>
        {[0.92, 0.86, 0.95, 0.7, 0.9, 0.82, 0.6, 0.93, 0.78].map((w, i) => (
          <div key={i} style={{ height: 10, width: `${w * 100}%`, background: "rgba(25,58,48,0.12)", borderRadius: 5, margin: "13px 0" }} />
        ))}
      </div>
      <div style={{ position: "absolute", left: 38, bottom: 36, fontFamily: font.sans, fontSize: 22, fontWeight: 500, color: color.forest }}>Effective {effective}</div>
      {tag && (
        <div style={{ position: "absolute", top: -18, right: 26, opacity: t, transform: `scale(${0.8 + 0.2 * t})`, background: color.forest, color: color.ivory, fontFamily: font.sans, fontWeight: 700, fontSize: 18, padding: "8px 16px", borderRadius: 999 }}>
          {tag}
        </div>
      )}
    </div>
  );
};

// Two guide versions stacking: the rules moved twice in ten months.
export const GuideStack: React.FC<{ firstAt: number; secondAt: number; checkAt: number }> = ({ firstAt, secondAt, checkAt }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = spring({ frame: frame - firstAt, fps, config: springs.critical });
  const b = spring({ frame: frame - secondAt, fps, config: springs.critical });
  const c = spring({ frame: frame - checkAt, fps, config: springs.overshoot });
  return (
    <div style={{ position: "relative", width: 620, height: 700 }}>
      <div style={{ position: "absolute", left: 20, top: 40, opacity: a * (1 - 0.35 * b), transform: `translateY(${(1 - a) * 60}px) rotate(${-4 * a}deg)` }}>
        <GuidePage effective="Dec 7, 2025" tint={color.ivoryDeep} />
      </div>
      <div style={{ position: "absolute", left: 150, top: 110, opacity: b, transform: `translate(${(1 - b) * 120}px, ${(1 - b) * 20}px) rotate(${3 * b}deg)` }}>
        <GuidePage effective="Apr 1, 2026" tag="Current" tagAt={secondAt + 10} />
        <div style={{ position: "absolute", right: -34, bottom: 70, width: 96, height: 96, borderRadius: 999, background: color.orange, display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${c})`, boxShadow: "0 10px 24px rgba(239,134,91,0.35)" }}>
          <svg width={52} height={52} viewBox="0 0 52 52">
            <path d="M 12 27 L 22 37 L 41 16" fill="none" stroke={color.ivory} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - ramp(frame, checkAt + 4, 10)} />
          </svg>
        </div>
      </div>
    </div>
  );
};

// Plan → complete request → treatment, with the patient moving along it.
export const CareTrack: React.FC<{ at: number; moveFrom: number; moveTo: number; width?: number }> = ({ at, moveFrom, moveTo, width = 1180 }) => {
  const frame = useCurrentFrame();
  const o = ramp(frame, at, 14);
  const m = interpolate(frame, [moveFrom, moveTo], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease.inOut });
  const nodes = ["Treatment plan", "Complete request", "Treatment"];
  const x = (i: number) => (i / (nodes.length - 1)) * width;
  const px = m * width;
  return (
    <div style={{ position: "relative", width, height: 120, opacity: o }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 30, height: 3, background: "rgba(25,58,48,0.18)" }} />
      <div style={{ position: "absolute", left: 0, width: px, top: 30, height: 3, background: color.orange }} />
      {nodes.map((n, i) => {
        const reached = px >= x(i) - 1;
        return (
          <div key={n} style={{ position: "absolute", left: x(i), top: 18, transform: "translateX(-50%)", display: "flex", flexDirection: "column", alignItems: "center" }}>
            <div style={{ width: 27, height: 27, borderRadius: 999, background: reached ? color.orange : color.ivory, border: `3px solid ${reached ? color.orange : color.forest}`, boxSizing: "border-box" }} />
            <div style={{ marginTop: 16, fontFamily: font.sans, fontWeight: 500, fontSize: 24, color: reached ? color.forest : color.muted, whiteSpace: "nowrap" }}>{n}</div>
          </div>
        );
      })}
      <div style={{ position: "absolute", left: px, top: -46, transform: "translateX(-50%)", padding: "8px 18px", borderRadius: 999, background: color.forest, color: color.ivory, fontFamily: font.sans, fontWeight: 500, fontSize: 22, whiteSpace: "nowrap", boxShadow: "0 8px 18px rgba(15,36,29,0.25)" }}>
        Teresa
        <div style={{ position: "absolute", left: "50%", bottom: -7, width: 14, height: 14, background: color.forest, transform: "translateX(-50%) rotate(45deg)" }} />
      </div>
    </div>
  );
};

// Four months of Ophi against one CDCP crown.
export const RoiMeter: React.FC<{ monthAts: number[]; crownAt: number; crownLabelAt?: number; paidAt: number; width?: number }> = ({ monthAts, crownAt, crownLabelAt, paidAt, width = 1500 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const CROWN = 884, MONTH = 199;
  const px = width / CROWN;
  const crown = ramp(frame, crownAt, 18);
  const crownLabel = ramp(frame, crownLabelAt ?? crownAt, 14);
  const months = monthAts.map((at) => spring({ frame: frame - at, fps, config: springs.snappy }));
  const filled = months.filter((m) => m > 0.5).length;
  const paid = spring({ frame: frame - paidAt, fps, config: springs.overshoot });
  return (
    <div style={{ position: "relative", width, height: 330 }}>
      {/* Crown bar */}
      <div style={{ position: "absolute", left: 0, top: 70, width, height: 130, borderRadius: 14, border: `3px solid ${color.forest}`, boxSizing: "border-box", opacity: crown, background: "rgba(228,231,217,0.6)" }} />
      <div style={{ position: "absolute", left: 0, top: 18, width, display: "flex", justifyContent: "space-between", opacity: crownLabel, fontFamily: font.sans, fontWeight: 500, fontSize: 26, color: color.forest }}>
        <span>One CDCP crown</span>
        <span style={{ fontFamily: font.display, fontSize: 40, marginTop: -10 }}>$884</span>
      </div>
      {/* Month blocks */}
      {months.map((m, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: 10 + i * MONTH * px,
            top: 80,
            width: MONTH * px - 12,
            height: 110,
            borderRadius: 9,
            background: color.forest,
            opacity: m,
            transform: `scaleY(${0.3 + 0.7 * m})`,
            transformOrigin: "50% 100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: color.ivory,
            fontFamily: font.sans,
            fontWeight: 500,
            fontSize: 28,
          }}
        >
          Month {i + 1} · $199
        </div>
      ))}
      <div style={{ position: "absolute", left: 0, top: 222, fontFamily: font.mono, fontSize: 26, color: color.muted, opacity: ramp(frame, monthAts[0], 10) }}>
        Ophi · ${MONTH * Math.max(1, filled)} so far
      </div>
      <div style={{ position: "absolute", right: 0, top: 214, display: "flex", alignItems: "center", gap: 18, opacity: paid, transform: `scale(${0.7 + 0.3 * paid}) rotate(${-4 * paid}deg)`, transformOrigin: "100% 50%" }}>
        <div style={{ fontFamily: font.display, fontStyle: "italic", fontSize: 64, color: color.orange }}>Paid for.</div>
      </div>
    </div>
  );
};

// Ophi's weekly rules check: one tick per week across the last ten months, the two guide changes flagged in
// orange, and today's check pulsing at the right end.
export const WeeklyWatch: React.FC<{ at: number; sweepTo: number; changesAt: number; pulseAt: number; width?: number }> = ({ at, sweepTo, changesAt, pulseAt, width = 820 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const WEEKS = 43; // Nov 30, 2025 → Sep 20, 2026
  const changes: Record<number, string> = { 1: "Dec 7", 17: "Apr 1" };
  const step = width / (WEEKS - 1);
  const sweep = interpolate(frame, [at, sweepTo], [0, WEEKS], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease.inOut });
  const ch = spring({ frame: frame - changesAt, fps, config: springs.overshoot });
  const pulseOn = frame >= pulseAt;
  const beat = pulseOn ? ((frame - pulseAt) % 15) / 15 : 0;
  return (
    <div style={{ position: "relative", width, height: 118, opacity: ramp(frame, at - 4, 10) }}>
      <div style={{ position: "absolute", left: 0, top: 0, fontFamily: font.mono, fontSize: 18, letterSpacing: "0.08em", color: color.muted }}>CHECKED EVERY WEEK</div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 70, height: 2, background: "rgba(25,58,48,0.2)" }} />
      {Array.from({ length: WEEKS }, (_, i) => {
        const shown = Math.min(1, Math.max(0, sweep - i));
        const isChange = i in changes;
        const h = isChange ? 24 + 30 * ch : 22;
        return (
          <div key={i} style={{ position: "absolute", left: i * step - 2, top: 71 - h, width: isChange ? 6 : 4, height: h, borderRadius: 3, background: isChange && ch > 0.05 ? color.orange : color.forest, opacity: shown * (isChange ? 1 : 0.55) }} />
        );
      })}
      {Object.entries(changes).map(([i, label]) => (
        <div key={i} style={{ position: "absolute", left: Number(i) * step, top: 80, transform: "translateX(-50%)", fontFamily: font.sans, fontWeight: 500, fontSize: 20, color: color.orange, opacity: ch, whiteSpace: "nowrap" }}>
          {label}
        </div>
      ))}
      <div style={{ position: "absolute", left: width - 9, top: 62, width: 18, height: 18, borderRadius: 99, background: color.orange, opacity: ramp(frame, sweepTo - 6, 8) }} />
      {pulseOn && <div style={{ position: "absolute", left: width - 9 - 22 * beat, top: 62 - 22 * beat, width: 18 + 44 * beat, height: 18 + 44 * beat, borderRadius: 99, border: `2px solid ${color.orange}`, opacity: 1 - beat, boxSizing: "border-box" }} />}
      <div style={{ position: "absolute", right: -10, top: 80, fontFamily: font.sans, fontWeight: 500, fontSize: 20, color: color.forest, whiteSpace: "nowrap", opacity: ramp(frame, sweepTo - 6, 8) }}>This week</div>
    </div>
  );
};

// A product chip marking an Ophi capability.
export const Chip: React.FC<{ at: number; children: React.ReactNode; style?: React.CSSProperties }> = ({ at, children, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - at, fps, config: springs.snappy });
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 14, padding: "14px 26px", borderRadius: 999, background: color.forest, color: color.ivory, fontFamily: font.sans, fontSize: 26, opacity: p, transform: `translateY(${(1 - p) * 16}px) scale(${0.94 + 0.06 * p})`, transformOrigin: "0 50%", boxShadow: "0 12px 28px rgba(15,36,29,0.2)", ...style }}>
      {children}
    </div>
  );
};

type Region = { at: number; x: number; y: number; w: number };
type PanelBox = { x: number; y: number; w: number; h: number };

// A window onto one app capture (2x PNG of a 1440-wide page) with its own camera: `regions` are page-space
// crops (CSS px) the view glides between; rings and a cursor sit on named boxes from the capture's sidecar.
export const AppPanel: React.FC<{
  src: string;
  width: number;
  aspect: number;
  regions: Region[];
  rings?: { box: PanelBox; from: number; to?: number }[];
  // Page-space areas to dim, so one row reads as the focus without cropping the page.
  dims?: { box: PanelBox; from: number; to?: number }[];
  cursor?: { box?: PanelBox; point?: { x: number; y: number }; from: number; clickAt: number; until?: number };
  // Whole UI elements lifted out of the page and enlarged (panel px position), e.g. a button that sits in a
  // column the crop leaves out.
  insets?: { box: PanelBox; x: number; y: number; zoom: number; from: number; to?: number }[];
  at: number;
}> = ({ src, width, aspect, regions, rings = [], dims = [], insets = [], cursor, at }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const height = width / aspect;
  // Current crop: ease between consecutive regions.
  let r = regions[0];
  for (let i = 1; i < regions.length; i++) {
    const a = regions[i - 1], b = regions[i];
    if (frame >= b.at + 6) { r = b; continue; }
    const t = interpolate(frame, [b.at - 18, b.at + 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease.inOut });
    r = { at: 0, x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, w: a.w + (b.w - a.w) * t };
    break;
  }
  const s = width / r.w;
  const toPanel = (b: PanelBox) => ({ x: (b.x - r.x) * s, y: (b.y - r.y) * s, w: b.w * s, h: b.h * s });
  const appear = ramp(frame, at, 16);
  return (
    <div style={{ position: "relative", width, height: height + 36, opacity: appear, transform: `translateY(${(1 - appear) * 40}px)`, borderRadius: 14, overflow: "hidden", background: "#fff", boxShadow: "0 30px 70px rgba(15,36,29,0.22), 0 4px 12px rgba(15,36,29,0.1)", border: "1px solid rgba(25,58,48,0.14)" }}>
      <div style={{ height: 36, background: "#efece2", display: "flex", alignItems: "center", gap: 8, padding: "0 16px", borderBottom: "1px solid rgba(25,58,48,0.1)" }}>
        {["#e8806a", "#e9c46a", "#8cc084"].map((c) => (
          <span key={c} style={{ width: 12, height: 12, borderRadius: 99, background: c, opacity: 0.8 }} />
        ))}
        <span style={{ marginLeft: 16, fontFamily: font.sans, fontSize: 15, color: color.muted }}>ophi.app · Past denials</span>
      </div>
      <div style={{ position: "relative", width, height, overflow: "hidden" }}>
        <img src={src} style={{ position: "absolute", left: -r.x * s, top: -r.y * s, width: 1440 * s, height: 900 * s }} />
        {dims.map((g, i) => {
          const o = ramp(frame, g.from, 20, ease.inOut) * (g.to === undefined ? 1 : 1 - ramp(frame, g.to, 20, ease.inOut));
          if (o <= 0) return null;
          const b = toPanel(g.box);
          return <div key={`d${i}`} style={{ position: "absolute", left: b.x, top: b.y, width: b.w, height: b.h, background: "rgba(244,242,233,0.72)", opacity: o }} />;
        })}
        {rings.map((g, i) => {
          const o = ramp(frame, g.from, 10) * (g.to === undefined ? 1 : 1 - ramp(frame, g.to, 10));
          if (o <= 0) return null;
          const b = toPanel(g.box);
          return <div key={i} style={{ position: "absolute", left: b.x - 8, top: b.y - 6, width: b.w + 16, height: b.h + 12, borderRadius: 10, border: `3px solid ${color.orange}`, opacity: o, boxShadow: "0 0 0 6px rgba(239,134,91,0.15)" }} />;
        })}
        {insets.map((g, i) => {
          const o = spring({ frame: frame - g.from, fps, config: springs.overshoot }) * (g.to === undefined ? 1 : 1 - ramp(frame, g.to, 10));
          if (o <= 0.001) return null;
          const k = 2 * g.zoom;
          return (
            <div key={`i${i}`} style={{ position: "absolute", left: g.x, top: g.y, width: g.box.w * g.zoom, height: g.box.h * g.zoom, overflow: "hidden", borderRadius: 12, background: "#fff", boxShadow: "0 18px 40px rgba(15,36,29,0.28), 0 0 0 3px rgba(239,134,91,0.9)", transform: `scale(${0.7 + 0.3 * o})`, opacity: Math.min(1, o * 1.3), transformOrigin: "50% 50%" }}>
              <img src={src} style={{ position: "absolute", left: -g.box.x * g.zoom, top: -g.box.y * g.zoom, width: 1440 * g.zoom, height: 900 * g.zoom, maxWidth: "none" }} />
              {void k}
            </div>
          );
        })}
        {cursor && (() => {
          const b = cursor.point ? { x: cursor.point.x - 10, y: cursor.point.y - 10, w: 16, h: 16 } : toPanel(cursor.box!);
          const t = interpolate(frame, [cursor.from, cursor.clickAt], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease.inOut });
          const cx = width + 40 + (b.x + b.w * 0.6 - width - 40) * t;
          const cy = height * 0.9 + (b.y + b.h * 0.6 - height * 0.9) * t;
          const click = frame >= cursor.clickAt ? Math.min(1, (frame - cursor.clickAt) / 12) : 0;
          if (frame < cursor.from || (cursor.until !== undefined && frame >= cursor.until + 8)) return null;
          const fade = cursor.until === undefined ? 1 : 1 - ramp(frame, cursor.until, 8);
          return (
            <>
              {click > 0 && click < 1 && <div style={{ position: "absolute", left: cx - 24 * click, top: cy - 24 * click, width: 48 * click, height: 48 * click, borderRadius: 99, border: `2px solid ${color.orange}`, opacity: 1 - click }} />}
              <svg width={30} height={40} viewBox="0 0 30 40" style={{ position: "absolute", left: cx, top: cy, opacity: fade, filter: "drop-shadow(0 3px 4px rgba(0,0,0,0.3))" }}>
                <path d="M 2 2 L 2 32 L 10 25 L 16 38 L 21 36 L 15 23 L 26 23 Z" fill="#111" stroke="#fff" strokeWidth={2.2} strokeLinejoin="round" />
              </svg>
            </>
          );
        })()}
      </div>
    </div>
  );
};

// Ten past denials as letters; on the "drafts" cue each turns into a drafted call.
export const DenialCards: React.FC<{ at: number; flipFrom: number; flipTo: number; count?: number }> = ({ at, flipFrom, flipTo, count = 10 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 76px)", gap: 12 }}>
      {Array.from({ length: count }, (_, i) => {
        const p = spring({ frame: frame - at - i * 2, fps, config: springs.snappy });
        const flipAt = flipFrom + ((flipTo - flipFrom) * i) / Math.max(1, count - 1);
        const f = ramp(frame, flipAt, 8, ease.inOut);
        const called = f > 0.5;
        return (
          <div key={i} style={{ height: 64, borderRadius: 10, background: called ? color.forest : color.ivory, border: `2px solid ${called ? color.forest : "rgba(25,58,48,0.28)"}`, display: "flex", alignItems: "center", justifyContent: "center", opacity: p, transform: `translateY(${(1 - p) * 14}px) scaleX(${Math.abs(1 - 2 * f) * 0.9 + 0.1})`, boxShadow: "0 4px 10px rgba(15,36,29,0.08)" }}>
            {called ? (
              <svg width={30} height={30} viewBox="0 0 24 24">
                <path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.6a1 1 0 0 1-.25 1z" fill={color.ivory} />
              </svg>
            ) : (
              <svg width={34} height={30} viewBox="0 0 34 30">
                <rect x={3} y={3} width={24} height={24} rx={3} fill="none" stroke={color.forest} strokeWidth={2} strokeOpacity={0.5} />
                <path d="M8 10 H22 M8 15 H19 M8 20 H16" stroke={color.forest} strokeWidth={2} strokeOpacity={0.35} strokeLinecap="round" />
                <circle cx={27} cy={23} r={6} fill={color.orange} />
                <path d="M24.8 20.8 L29.2 25.2 M29.2 20.8 L24.8 25.2" stroke={color.ivory} strokeWidth={1.8} strokeLinecap="round" />
              </svg>
            )}
          </div>
        );
      })}
    </div>
  );
};
