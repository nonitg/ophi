import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { Counter, Footnote, Paper } from "../components";
import { CanadaDotMap } from "../components/market/CanadaDotMap";
import { Rise, ramp } from "../components/market/parts";
import { Narration, Sfx } from "../audio";
import { wordAt } from "../vo";
import { color, ease, font, type } from "../theme";

const w = (word: string, nth = 0) => wordAt("market", 0, word, nth);

// The first product's market: nearly every provider takes CDCP, 17,857 clinics, $42.6M a year at $199/month,
// and two national groups that can roll it out at once.
export const Market: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const t = {
    nearly: w("Nearly"),
    canada: w("Canada"),
    patients: w("patients,"),
    across: w("across"),
    eighteen: w("eighteen"),
    clinics: w("clinics."),
    at: w("At"),
    hundred: w("hundred"),
    month: w("month,"),
    fortyThree: w("forty-three-million-dollar-a-year"),
    first: w("first"),
    alone: w("alone."),
    and: w("And", 1), // the first "and" is in "a hundred and ninety-nine"
    dentalcorp: w("dentalcorp"),
    dentist: w("Dentist"),
    thousand: w("thousand", 1),
    once: w("once."),
  };

  // Left column states: quote → count → math → rollout.
  const quoteOut = t.across - 4;
  const mathIn = t.at - 2;
  const mathOut = t.and - 2;
  const dim = ramp(frame, mathIn, 14, ease.inOut) * (1 - ramp(frame, mathOut, 14, ease.inOut));

  return (
    <Paper light={0.55}>
      <Narration section="market" />

      {/* Map */}
      <div style={{ position: "absolute", left: 760, top: 150, transform: `scale(${1 + 0.02 * (frame / durationInFrames)})`, transformOrigin: "60% 70%" }}>
        <CanadaDotMap
          width={1080}
          drawFrom={t.nearly}
          drawTo={t.patients}
          dotsFrom={t.across - 4}
          dotsTo={t.clinics + 6}
          shimmerAt={t.fortyThree}
          dcAt={t.dentalcorp}
          d123At={t.dentist}
          labelsAt={t.across + 10}
          dim={dim}
        />
      </div>
      <div style={{ position: "absolute", left: 1340, top: 944, fontFamily: font.mono, fontSize: 17, letterSpacing: "0.06em", color: color.muted, opacity: ramp(frame, t.across, 14) }}>
        EACH DOT ≈ 50 CLINICS · ILLUSTRATIVE PLACEMENT
      </div>

      <div style={{ position: "absolute", left: 120, top: 120, fontFamily: font.mono, fontSize: type.label, letterSpacing: "0.12em", color: color.muted, opacity: ramp(frame, 0, 14) }}>
        THE MARKET · CANADA
      </div>

      {/* 1 · Nearly every provider */}
      <Rise at={t.nearly} out={quoteOut} style={{ position: "absolute", left: 120, top: 300, width: 600 }}>
        <div style={{ fontFamily: font.display, fontSize: 60, lineHeight: 1.12, color: color.forest }}>
          “Close to <span style={{ color: color.orange }}>100%</span> of active dentists … are caring for patients covered under the CDCP.”
        </div>
        <div style={{ marginTop: 26, fontFamily: font.sans, fontSize: 24, color: color.muted }}>Health Canada, April 17, 2026</div>
      </Rise>

      {/* 2 · 17,857 clinics */}
      <Rise at={t.across} out={Infinity} style={{ position: "absolute", left: 120, top: 250 }}>
        <Counter to={17857} start={t.across + 4} duration={Math.max(24, t.clinics - t.across)} style={{ fontFamily: font.display, fontSize: 170, color: color.forest, letterSpacing: "-0.03em", lineHeight: 1 }} />
        <div style={{ fontFamily: font.sans, fontWeight: 500, fontSize: 34, color: color.forest, marginTop: 10 }}>dental clinics in Canada</div>
      </Rise>

      {/* 3 · The math */}
      <MathBlock inAt={mathIn} outAt={mathOut} hundred={t.hundred} month={t.month} total={t.fortyThree} first={t.first} />

      {/* 4 · Rollout */}
      <Rise at={t.dentalcorp - 6} style={{ position: "absolute", left: 120, top: 590, width: 620 }}>
        <Legend dot="solid" label="dentalcorp" count="~630 clinics" at={t.dentalcorp} />
        <Legend dot="ring" label="123Dentist" count="~510 clinics" at={t.dentist} />
        <Rise at={t.thousand - 2} style={{ marginTop: 40 }}>
          <div style={{ fontFamily: font.display, fontSize: 76, lineHeight: 1.05, color: color.forest }}>
            1,100+ clinics.
            <br />
            <span style={{ fontStyle: "italic", color: color.orange }}>Two decisions.</span>
          </div>
        </Rise>
      </Rise>
      <SummaryChip at={mathOut} />

      <Footnote text="Health Canada, Apr 17, 2026 · ISED Canadian Industry Statistics 2025, dental offices (NAICS 6212), 17,857 employer establishments" start={t.nearly + 10} end={mathIn} bottom={34} />
      <Footnote text="17,857 clinics × $199 × 12 months = $42,642,516 a year · Canada only, first product" start={mathIn + 6} end={mathOut} bottom={34} />
      <Footnote text="dentalcorp, Jul 21, 2026: 650+ practices in North America (≈630 in Canada) · 123Dentist clinic map: 510 clinics" start={mathOut + 6} bottom={34} />

      <Sfx name="shimmer" at={t.across} volume={0.3} />
      <Sfx name="counter" at={t.across + 4} volume={0.3} />
      <Sfx name="pop" at={t.hundred} volume={0.3} />
      <Sfx name="pop" at={t.month} volume={0.3} />
      <Sfx name="impact" at={t.fortyThree} volume={0.35} />
      <Sfx name="chime" at={t.dentalcorp} volume={0.3} />
      <Sfx name="chime" at={t.dentist} volume={0.3} />
    </Paper>
  );
};

const MathBlock: React.FC<{ inAt: number; outAt: number; hundred: number; month: number; total: number; first: number }> = ({ inAt, outAt, hundred, month, total, first }) => {
  const frame = useCurrentFrame();
  const o = ramp(frame, inAt, 12) * (1 - ramp(frame, outAt, 12, ease.in));
  if (o <= 0) return null;
  const row = (at: number): React.CSSProperties => ({
    opacity: ramp(frame, at, 12),
    transform: `translateX(${(1 - ramp(frame, at, 12)) * -24}px)`,
    fontFamily: font.display,
    fontSize: 62,
    color: color.forest,
    lineHeight: 1.25,
    display: "flex",
    gap: 20,
    alignItems: "baseline",
  });
  const op = { fontFamily: font.mono, fontSize: 40, color: color.orange, width: 44 } as const;
  const rule = ramp(frame, total - 4, 14, ease.inOut);
  return (
    <div style={{ position: "absolute", left: 120, top: 510, opacity: o }}>
      <div style={row(hundred - 4)}>
        <span style={op}>×</span>$199 <span style={{ fontSize: 34, color: color.muted, fontFamily: font.sans }}>per location, per month</span>
      </div>
      <div style={row(month)}>
        <span style={op}>×</span>12 <span style={{ fontSize: 34, color: color.muted, fontFamily: font.sans }}>months</span>
      </div>
      <div style={{ width: 560 * rule, height: 3, background: color.forest, margin: "16px 0 22px" }} />
      <div style={{ ...row(total - 2), fontSize: 132, letterSpacing: "-0.03em", lineHeight: 1 }}>
        <span style={{ ...op, fontSize: 56 }}>=</span>
        <span>
          $42.6M<span style={{ fontSize: 44, color: color.muted, marginLeft: 16, letterSpacing: 0 }}>a year</span>
        </span>
      </div>
      <div style={{ ...row(first - 2), fontFamily: font.sans, fontSize: 30, color: color.muted, marginTop: 18 }}>Our first product. Canada alone.</div>
    </div>
  );
};

const Legend: React.FC<{ dot: "solid" | "ring"; label: string; count: string; at: number }> = ({ dot, label, count, at }) => {
  const frame = useCurrentFrame();
  const p = ramp(frame, at - 3, 12);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 20, margin: "16px 0", opacity: p, transform: `translateX(${(1 - p) * -20}px)` }}>
      <span style={{ width: 26, height: 26, borderRadius: 99, boxSizing: "border-box", background: dot === "solid" ? color.orange : color.ivory, border: `4px solid ${color.orange}` }} />
      <span style={{ fontFamily: font.display, fontSize: 56, color: color.forest }}>{label}</span>
      <span style={{ fontFamily: font.sans, fontSize: 30, color: color.muted }}>{count}</span>
    </div>
  );
};

// The market total stays visible, small, once the rollout takes the stage.
const SummaryChip: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  const p = ramp(frame, at + 14, 14);
  return (
    <div style={{ position: "absolute", left: 120, top: 486, opacity: p, display: "flex", alignItems: "baseline", gap: 14, fontFamily: font.sans, fontSize: 30, color: color.forest }}>
      <span style={{ fontFamily: font.display, fontSize: 46 }}>$42.6M</span>
      <span style={{ color: color.muted }}>a year at $199 a month</span>
    </div>
  );
};
