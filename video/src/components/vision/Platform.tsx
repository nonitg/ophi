import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { evolvePath } from "@remotion/paths";
import { ease, font, springs } from "../../theme";
import { wordAt } from "../../vo";
import { Sfx } from "../../audio";
import { film, lerp, ramp, window01 } from "./util";

const w0 = (word: string, nth = 0) => wordAt("vision", 0, word, nth);

// Where the three platform layers end up: stacked segments of the tree's trunk, just under the tooth.
export const TRUNK = { x: 960, top: 392, seg: 30, gap: 3, w: 34 };
export const trunkBottom = TRUNK.top + 3 * TRUNK.seg + 2 * TRUNK.gap;

// ── Why preauthorization: clinic, patient and payer all look at one chart ─────────────────────────────
const CHART = { x: 960, y: 520, w: 560, h: 170 };
const SPOKES = [
  { id: "clinic", label: "The clinic", x: 420, y: 760, to: [CHART.x - CHART.w / 2 + 30, CHART.y + CHART.h / 2 - 16] },
  { id: "patient", label: "The patient", x: 960, y: 830, to: [CHART.x, CHART.y + CHART.h / 2] },
  { id: "payer", label: "The payer", x: 1500, y: 760, to: [CHART.x + CHART.w / 2 - 30, CHART.y + CHART.h / 2 - 16] },
] as const;

const ChartCard: React.FC<{ frame: number; inAt: number; glowAt: number; outAt: number }> = ({ frame, inAt, glowAt, outAt }) => {
  const p = ramp(frame, inAt, inAt + 16);
  const out = ramp(frame, outAt, outAt + 16);
  const glow = window01(frame, glowAt - 4, outAt + 10, 10);
  if (p <= 0 || out >= 1) return null;
  // Mini odontogram: upper and lower arches, #46 marked (lower right first molar = 6th from the midline).
  const upper = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
  const lower = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];
  const tooth = (n: number) => (
    <div
      key={n}
      style={{
        width: 24,
        height: 20,
        borderRadius: 5,
        border: `1.5px solid ${n === 46 ? film.metal : film.boneFaint}`,
        background: n === 46 ? "rgba(239,134,91,0.45)" : "rgba(230,236,227,0.06)",
        boxShadow: n === 46 ? `0 0 14px ${film.metalGlow}` : undefined,
      }}
    />
  );
  return (
    <div
      style={{
        position: "absolute",
        left: CHART.x - CHART.w / 2,
        top: CHART.y - CHART.h / 2,
        width: CHART.w,
        height: CHART.h,
        borderRadius: 14,
        background: "rgba(14,31,25,0.9)",
        border: `1.5px solid ${glow > 0 ? `rgba(239,134,91,${0.4 + 0.5 * glow})` : film.boneFaint}`,
        boxShadow: `0 0 ${20 + 50 * glow}px rgba(239,134,91,${0.08 + 0.3 * glow})`,
        padding: "18px 24px",
        opacity: p * (1 - out),
        transform: `translateY(${(1 - p) * 24 - out * 40}px) scale(${lerp(0.96, 1, p) * lerp(1, 0.9, out)})`,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: font.mono, fontSize: 16, letterSpacing: "0.12em", color: film.boneDim }}>
        <span>ONE CHART</span>
        <span style={{ color: film.metal }}>CROWN · #46</span>
      </div>
      <div style={{ display: "flex", gap: 6, marginTop: 16, justifyContent: "center" }}>{upper.map(tooth)}</div>
      <div style={{ display: "flex", gap: 6, marginTop: 8, justifyContent: "center" }}>{lower.map(tooth)}</div>
      <div style={{ display: "flex", gap: 18, marginTop: 14, justifyContent: "center", fontFamily: font.mono, fontSize: 15, color: film.boneDim }}>
        <span>x-rays</span>
        <span>·</span>
        <span>gum chart</span>
        <span>·</span>
        <span>treatment plan</span>
        <span>·</span>
        <span>notes</span>
      </div>
    </div>
  );
};

// ── The platform: three layers Ophi needs to get one request right ───────────────────────────────────
type Layer = { n: string; title: string; sub: string; at: number; ai?: boolean };

const SLAB = { x: 360, w: 1200, h: 124, top: 440, step: 140 };

const Micro: React.FC<{ i: number; t: number; frame: number }> = ({ i, t, frame }) => {
  const row = (k: number) => ramp(t, k * 0.22, k * 0.22 + 0.25);
  const mono: React.CSSProperties = { fontFamily: font.mono, fontSize: 15, color: film.boneDim, whiteSpace: "nowrap", lineHeight: 1.55 };
  if (i === 0) {
    const rows = ["odontogram  #46 MODB", "PA #46      2023-11-14", "perio       4-point"];
    return (
      <div style={mono}>
        <div style={{ color: film.metal, letterSpacing: "0.12em", fontSize: 13 }}>READ-ONLY</div>
        {rows.map((r, k) => (
          <div key={k} style={{ opacity: row(k + 1), transform: `translateX(${(1 - row(k + 1)) * 10}px)` }}>
            {r}
          </div>
        ))}
      </div>
    );
  }
  if (i === 1) {
    const rows: [string, boolean][] = [
      ["Guide 6.3.5     met", true],
      ["PA ≤ 12 months  gap", false],
      ["perio, 6 sites  gap", false],
    ];
    return (
      <div style={mono}>
        <div style={{ color: film.metal, letterSpacing: "0.12em", fontSize: 13 }}>RULE PACK 2026-01-26</div>
        {rows.map(([r, ok], k) => (
          <div key={k} style={{ opacity: row(k + 1), color: ok ? film.boneDim : film.metal }}>
            {r}
          </div>
        ))}
      </div>
    );
  }
  // Calibrated note answers filling in, then the risk level they feed.
  const bars = [0.82, 0.35, 0.64, 0.18, 0.9, 0.46, 0.72];
  return (
    <div style={mono}>
      <div style={{ color: film.metal, letterSpacing: "0.12em", fontSize: 13 }}>✦ 7 NOTE ANSWERS</div>
      <div style={{ display: "flex", gap: 7, alignItems: "flex-end", height: 40, marginTop: 6 }}>
        {bars.map((b, k) => {
          const g = ramp(t, 0.1 + k * 0.06, 0.4 + k * 0.06);
          const wob = 0.04 * Math.sin((frame + k * 11) / 7) * g;
          return <div key={k} style={{ width: 18, height: 40 * Math.max(0.05, b * g + wob), borderRadius: 3, background: k === 4 ? film.metal : "rgba(230,236,227,0.55)" }} />;
        })}
      </div>
      <div style={{ marginTop: 6, opacity: ramp(t, 0.6, 0.85) }}>
        risk <span style={{ color: film.metal }}>High</span> → Medium
      </div>
    </div>
  );
};

const Slab: React.FC<{ layer: Layer; i: number; frame: number; fps: number; morphAt: number }> = ({ layer, i, frame, fps, morphAt }) => {
  const inP = spring({ frame: frame - layer.at + 4, fps, config: springs.critical });
  if (frame < layer.at - 6) return null;
  const lit = ramp(frame, layer.at, layer.at + 20); // content build + scan
  const scan = ramp(frame, layer.at - 2, layer.at + 22, ease.inOut);
  const m = ramp(frame, morphAt, morphAt + 30, ease.inOut);
  const content = 1 - ramp(frame, morphAt, morphAt + 10);

  const x = lerp(SLAB.x, TRUNK.x - TRUNK.w / 2, m);
  const y = lerp(SLAB.top + i * SLAB.step, TRUNK.top + i * (TRUNK.seg + TRUNK.gap), m);
  const w = lerp(SLAB.w, TRUNK.w, m);
  const h = lerp(SLAB.h, TRUNK.seg, m);
  const accent = i === 2 ? film.metal : film.bone;
  // The slab turns from dark glass into solid trunk (bone, with the decisions layer in orange "metal").
  const fill = m > 0 ? `rgba(${i === 2 ? "239,134,91" : "230,236,227"},${lerp(0.06, 0.95, m)})` : "rgba(230,236,227,0.06)";

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y + (1 - inP) * 40,
        width: w,
        height: h,
        borderRadius: lerp(14, 6, m),
        background: fill,
        border: `1.5px solid ${lit > 0 ? `rgba(239,134,91,${0.25 + 0.45 * lit * (1 - m)})` : film.boneFaint}`,
        boxShadow: `0 0 ${lerp(36, 18, m)}px rgba(${i === 2 ? "239,134,91" : "170,210,190"},${0.12 + 0.18 * lit})`,
        opacity: inP,
        overflow: "hidden",
      }}
    >
      {/* scan line passing once as the layer comes online */}
      {scan > 0 && scan < 1 && (
        <div
          style={{
            position: "absolute",
            top: 0,
            bottom: 0,
            left: `${scan * 110 - 10}%`,
            width: 120,
            background: "linear-gradient(90deg, rgba(239,134,91,0), rgba(239,134,91,0.35), rgba(255,250,240,0.55), rgba(239,134,91,0))",
          }}
        />
      )}
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 6, background: accent, opacity: 0.9 * content }} />
      <div style={{ position: "absolute", left: 40, top: 20, opacity: content, whiteSpace: "nowrap" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 18 }}>
          <span style={{ fontFamily: font.mono, fontSize: 18, color: film.metal, letterSpacing: "0.12em" }}>{layer.n}</span>
          <span style={{ fontFamily: font.display, fontSize: 46, color: film.bone, lineHeight: 1 }}>{layer.title}</span>
        </div>
        <div style={{ fontFamily: font.mono, fontSize: 18, color: film.boneDim, marginTop: 16, marginLeft: 44, opacity: ramp(lit, 0.3, 1) }}>
          {layer.sub}
        </div>
      </div>
      <div style={{ position: "absolute", right: 30, top: 18, width: 250, opacity: content }}>
        <Micro i={i} t={ramp(frame, layer.at + 6, layer.at + 50)} frame={frame} />
      </div>
    </div>
  );
};

export const Platform: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cue = {
    why: w0("Why"),
    moment: w0("moment"),
    clinic: w0("clinic"),
    patient: w0("patient"),
    payer: w0("payer"),
    chart: w0("chart"),
    to: w0("To"),
    read: w0("read"),
    know: w0("know"),
    learn: w0("learn"),
    foundation: w0("foundation"),
  };
  const spokeAt = [cue.clinic, cue.patient, cue.payer];
  const spokesOut = ramp(frame, cue.to, cue.to + 16);

  const LAYERS: Layer[] = [
    { n: "01", title: "Reads the chart", sub: "practice-software database · read-only · re-read within 15 s of an edit", at: cue.read },
    { n: "02", title: "Knows every rule", sub: "CDCP guide as code · 14 requirements · 31 cited clauses · checked weekly", at: cue.know },
    { n: "03", title: "Learns what the payer decides", sub: "✦ Laya 421M-param language model · ✦ risk model · ✦ letter reader", at: cue.learn, ai: true },
  ];

  const q = window01(frame, cue.why - 4, cue.to + 8, 14);
  const heading = window01(frame, cue.to - 2, cue.foundation + 6, 12);
  const trunkLabels = ramp(frame, cue.foundation + 24, cue.foundation + 40);
  const rootLink = ramp(frame, cue.foundation + 6, cue.foundation + 36);

  return (
    <div style={{ position: "absolute", inset: 0 }}>
      {/* the question */}
      <div style={{ position: "absolute", left: 72, top: 214, opacity: q, transform: `translateY(${(1 - ramp(frame, cue.why - 4, cue.why + 14)) * 16}px)` }}>
        <div style={{ fontFamily: font.mono, fontSize: 17, letterSpacing: "0.14em", color: film.metal }}>WHY START HERE</div>
        <div style={{ fontFamily: font.display, fontStyle: "italic", fontSize: 66, color: film.bone, lineHeight: 1.08, marginTop: 10 }}>
          Why start with
          <br />
          preauthorization?
        </div>
      </div>

      {/* spokes: clinic, patient and payer converge on the one chart */}
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, opacity: 1 - spokesOut }}>
        {SPOKES.map((s, k) => {
          const [tx, ty] = s.to;
          const d = `M ${s.x} ${s.y - 24} C ${s.x} ${s.y - 110}, ${tx} ${ty + 110}, ${tx} ${ty}`;
          const p = ramp(frame, spokeAt[k] - 2, spokeAt[k] + 16, ease.inOut);
          const pulseT = ((frame - spokeAt[k] - 16) % 30) / 30;
          return (
            <g key={s.id}>
              <path d={d} fill="none" stroke={film.boneDim} strokeWidth={2.5} strokeDasharray="2 9" strokeLinecap="round" opacity={p > 0 ? 1 : 0} {...(p < 1 ? evolvePath(p, d) : {})} />
              {p >= 1 && (
                <circle
                  cx={lerp(s.x, tx, ease.inOut(pulseT))}
                  cy={lerp(s.y - 24, ty, ease.inOut(pulseT))}
                  r={6}
                  fill={film.metal}
                  opacity={Math.sin(pulseT * Math.PI)}
                />
              )}
            </g>
          );
        })}
      </svg>
      {SPOKES.map((s, k) => {
        const on = spring({ frame: frame - spokeAt[k] + 3, fps, config: springs.overshoot });
        if (frame < spokeAt[k] - 4) return null;
        return (
          <div key={s.id} style={{ position: "absolute", left: s.x, top: s.y - 24, transform: "translate(-50%, -50%)", opacity: 1 - spokesOut }}>
            <div style={{ width: 30, height: 30, borderRadius: 15, background: film.bone, transform: `scale(${on})`, boxShadow: `0 0 24px ${film.metalGlow}`, margin: "0 auto" }} />
            <div style={{ fontFamily: font.display, fontSize: 44, color: film.bone, marginTop: 14, whiteSpace: "nowrap", textAlign: "center", opacity: Math.min(1, on) }}>{s.label}</div>
          </div>
        );
      })}
      <ChartCard frame={frame} inAt={cue.moment} glowAt={cue.chart} outAt={cue.to} />

      {/* what it takes */}
      <div style={{ position: "absolute", left: SLAB.x, top: 402, opacity: heading, fontFamily: font.mono, fontSize: 17, letterSpacing: "0.14em", color: film.boneDim }}>
        TO GET IT RIGHT, OPHI HAS TO
      </div>
      {LAYERS.map((l, i) => (
        <Slab key={l.n} layer={l} i={i} frame={frame} fps={fps} morphAt={cue.foundation} />
      ))}

      {/* after the morph: the tooth's roots join the trunk, and the trunk's layers keep their names */}
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        {[
          "M 888 303 C 890 345, 930 375, 952 392",
          "M 976 342 C 975 360, 970 378, 968 392",
        ].map((d, k) =>
          rootLink > 0 ? <path key={k} d={d} fill="none" stroke={film.bone} strokeWidth={6} strokeLinecap="round" {...evolvePath(rootLink, d)} /> : null,
        )}
      </svg>
      {["reads the chart", "knows every rule", "learns the payer"].map((t, i) => (
        <div
          key={t}
          style={{
            position: "absolute",
            right: 1920 - (TRUNK.x - TRUNK.w / 2) + 16,
            top: TRUNK.top + i * (TRUNK.seg + TRUNK.gap) + 4,
            opacity: trunkLabels,
            fontFamily: font.mono,
            fontSize: 15,
            color: i === 2 ? film.metal : film.boneDim,
            whiteSpace: "nowrap",
          }}
        >
          {t}
        </div>
      ))}

      <Sfx name="pop" at={cue.clinic} volume={0.25} />
      <Sfx name="pop" at={cue.patient} volume={0.25} />
      <Sfx name="pop" at={cue.payer} volume={0.25} />
      <Sfx name="chime" at={cue.chart} volume={0.2} />
      <Sfx name="whoosh" at={cue.read - 4} volume={0.22} />
      <Sfx name="whoosh" at={cue.know - 4} volume={0.22} />
      <Sfx name="shimmer" at={cue.learn} volume={0.3} />
      <Sfx name="whoosh" at={cue.foundation} volume={0.3} />
    </div>
  );
};
