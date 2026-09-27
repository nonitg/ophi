import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Counter, Footnote, Paper, Wordmark } from "../components";
import { Pipeline } from "../components/story/Pipeline";
import { QueueLoop } from "../components/story/QueueLoop";
import { fadeOut, pop, prog } from "../components/story/util";
import { SweepOnPaper } from "../components/story/SweepOnPaper";
import { Narration, Sfx } from "../audio";
import { voLines, wordAt } from "../vo";
import { color, ease, font } from "../theme";

const S = "problem";

const StatCard: React.FC<{ at: number; big: React.ReactNode; caption: string; source: string; strong?: boolean }> = ({ at, big, caption, source, strong }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = pop(frame, at, fps, "critical");
  const ink = strong ? color.ivory : color.forest;
  return (
    <div
      style={{
        width: 500,
        height: 430,
        borderRadius: 26,
        background: strong ? color.forest : "#fbfaf4",
        boxShadow: "0 30px 60px rgba(15,36,29,0.14), 0 4px 10px rgba(15,36,29,0.06)",
        padding: "44px 44px 36px",
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        opacity: p,
        transform: `translateY(${(1 - p) * 90}px) rotate(${(1 - p) * 4}deg)`,
      }}
    >
      <div style={{ fontFamily: font.display, fontSize: 150, lineHeight: 0.95, letterSpacing: "-0.04em", color: ink }}>{big}</div>
      <div style={{ fontFamily: font.sans, fontSize: 32, lineHeight: 1.25, color: ink, marginTop: 22 }}>{caption}</div>
      <div style={{ flex: 1 }} />
      <div style={{ fontFamily: font.mono, fontSize: 16, letterSpacing: "0.04em", lineHeight: 1.4, color: strong ? "rgba(244,242,233,0.7)" : color.muted }}>{source}</div>
    </div>
  );
};

const QUOTE = "The most common reasons for denials are incomplete submissions, such as missing X-rays, insufficient evidence that the clinical criteria has been met…";

// Quote set word by word; the phrase "incomplete submissions" gets a drawn orange underline.
const Quote: React.FC<{ at: number; underlineAt: number }> = ({ at, underlineAt }) => {
  const frame = useCurrentFrame();
  const words = QUOTE.split(" ");
  const u = prog(frame, underlineAt, 16, ease.inOut);
  return (
    <div style={{ fontFamily: font.display, fontStyle: "italic", fontSize: 76, lineHeight: 1.16, color: color.forest, letterSpacing: "-0.01em" }}>
      {words.map((w, i) => {
        const p = prog(frame, at + i * 4, 10);
        const key = i === 7 || i === 8; // "incomplete submissions,"
        return (
          <span key={i} style={{ display: "inline-block", marginRight: "0.26em", opacity: p, transform: `translateY(${(1 - p) * 16}px)`, position: "relative" }}>
            {w}
            {key && (
              <span style={{ position: "absolute", left: 0, right: i === 8 ? "0.3em" : "-0.3em", bottom: "0.02em", height: 6, borderRadius: 3, background: color.orange, transformOrigin: "left", transform: `scaleX(${i === 7 ? Math.min(1, u * 2) : Math.max(0, u * 2 - 1)})` }} />
            )}
          </span>
        );
      })}
    </div>
  );
};

// Words of the closing line appear as they are spoken; "what's missing" in orange, "still in the chair" underlined.
const Kinetic: React.FC = () => {
  const frame = useCurrentFrame();
  const line = voLines(S)[2];
  const words = line.words.slice(1); // "Ophi" is the wordmark itself
  const chairFrom = words.findIndex((w) => w.w.toLowerCase() === "still");
  const under = prog(frame, words[words.length - 1].from, 14, ease.inOut);
  return (
    <div style={{ fontFamily: font.display, fontSize: 70, lineHeight: 1.2, color: color.forest, textAlign: "center", maxWidth: 1400, letterSpacing: "-0.01em" }}>
      {words.map((w, i) => {
        const p = prog(frame, w.from - 2, 10);
        const hot = /what|missing/i.test(w.w);
        return (
          <span key={i} style={{ display: "inline-block", marginRight: "0.24em", opacity: p, transform: `translateY(${(1 - p) * 22}px)`, color: hot ? color.orange : color.forest, position: "relative" }}>
            {w.w}
            {i >= chairFrom && (
              <span style={{ position: "absolute", left: 0, right: i === words.length - 1 ? "0.1em" : "-0.28em", bottom: "0.06em", height: 4, background: color.forest, opacity: 0.8, transformOrigin: "left", transform: `scaleX(${under})` }} />
            )}
          </span>
        );
      })}
    </div>
  );
};

// The problem at national scale, the rework loop that wastes it, and Ophi's answer.
export const Problem: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const tThirteen = wordAt(S, 0, "thirteen");
  const tDollars = wordAt(S, 0, "dollars");
  const tPreauth = wordAt(S, 0, "preauthorization");
  const tStalls = wordAt(S, 0, "stalls");
  const tClose = wordAt(S, 0, "close");
  const tTwo = wordAt(S, 0, "two");
  const tWeek = wordAt(S, 0, "two", 1);
  const tHealth = wordAt(S, 1, "health");
  const tIncomplete = wordAt(S, 1, "incomplete");
  const tThe = wordAt(S, 1, "the", 1); // "The clinic only finds out…"
  const tHome = wordAt(S, 1, "home");
  const tBack = wordAt(S, 1, "back");
  const tTwice = wordAt(S, 1, "twice");
  const tPublic = wordAt(S, 1, "public");
  const tOphi = wordAt(S, 2, "ophi");

  // Phase windows.
  const headOut = fadeOut(frame, tClose - 10, 14);
  const cardsOut = fadeOut(frame, tHealth - 8, 12);
  const quoteOut = fadeOut(frame, tThe - 10, 12);
  const sweepAt = tOphi - 22;
  const sweep = interpolate(frame, [sweepAt, sweepAt + 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const head = pop(frame, tThirteen - 2, fps, "snappy");
  const headLift = prog(frame, tPreauth - 12, 20, ease.inOut);

  const before = (
    <Paper light={0.85}>
      {/* $13 billion, set like a front page */}
      {frame < tClose + 6 && (
        <AbsoluteFill style={{ alignItems: "center", opacity: headOut, transform: `translateY(${-headLift * 150}px)` }}>
          <div style={{ marginTop: 330, width: 1300, textAlign: "center", color: color.forest }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontFamily: font.mono, fontSize: 19, letterSpacing: "0.14em", color: color.muted, opacity: prog(frame, 0, 12) }}>
              <span>BUDGET 2023</span>
              <span>CANADIAN DENTAL CARE PLAN</span>
            </div>
            <div style={{ height: 3, background: color.forest, margin: "16px 0 4px", transformOrigin: "center", transform: `scaleX(${prog(frame, 0, 20)})` }} />
            <div style={{ height: 1, background: color.forest, marginBottom: 20, transformOrigin: "center", transform: `scaleX(${prog(frame, 2, 20)})` }} />
            <div
              style={{
                fontFamily: font.display,
                fontSize: 250,
                lineHeight: 1,
                letterSpacing: "-0.035em",
                opacity: head,
                transform: `scale(${interpolate(head, [0, 1], [1.12, 1])})`,
                filter: `blur(${(1 - head) * 8}px)`,
              }}
            >
              $13 billion
            </div>
            <div style={{ fontFamily: font.sans, fontSize: 34, color: color.muted, marginTop: 10, opacity: prog(frame, tDollars, 14) }}>
              over five years, then $4.4 billion a year, ongoing
            </div>
          </div>
          <div style={{ position: "absolute", top: 790, left: 120 }}>
            <Pipeline at={tPreauth - 8} stallAt={tStalls} />
          </div>
        </AbsoluteFill>
      )}

      {/* the scale of it */}
      {frame >= tClose - 6 && frame < tHealth + 6 && (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: cardsOut }}>
          <div style={{ display: "flex", gap: 44, marginTop: -40 }}>
            <StatCard at={tClose - 2} big="1.1M+" caption="preauthorization requests in the plan's first benefit period" source="CDCP Annual Report 2024–25 · Health Canada" />
            <StatCard
              at={tTwo - 2}
              strong
              big={<><Counter from={1.1} to={1.9} decimals={1} start={tTwo} duration={24} />M</>}
              caption="a year, at the spring 2026 pace"
              source="480,000 complete requests, Mar 1 – May 31, 2026, ×4 · Health Canada via Oral Health Group"
            />
            <StatCard at={tWeek - 2} big="≈ 2" caption="a week, for the average clinic" source="1.9M a year ÷ 17,857 clinics (ISED, 2025) ÷ 52" />
          </div>
        </AbsoluteFill>
      )}

      {/* Health Canada, on why */}
      {frame >= tHealth - 6 && frame < tThe + 4 && (
        <AbsoluteFill style={{ justifyContent: "center", padding: "0 220px", opacity: prog(frame, tHealth - 6, 10) * quoteOut }}>
          <div style={{ fontFamily: font.display, fontSize: 260, lineHeight: 0.6, color: color.orange, height: 110 }}>“</div>
          <Quote at={tHealth} underlineAt={tIncomplete} />
          <div style={{ fontFamily: font.sans, fontSize: 28, color: color.muted, marginTop: 40, opacity: prog(frame, tIncomplete + 10, 14) }}>
            Health Canada spokesperson, to CBC · May 27, 2026
          </div>
        </AbsoluteFill>
      )}

      {/* the rework loop */}
      {frame >= tThe - 8 && <QueueLoop at={tThe - 8} send={tThe + 4} home={tHome} back={tBack} twice={tTwice} money={tPublic} />}

      <Footnote text="$13B over five years, $4.4B ongoing · Budget 2023, Department of Finance Canada" start={tDollars} end={tClose} />
    </Paper>
  );

  const after = (
    <Paper light={0.8}>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ marginTop: -80 }}>
          <Wordmark start={tOphi - 4} size={300} />
        </div>
        <div style={{ marginTop: 40 }}>
          <Kinetic />
        </div>
      </AbsoluteFill>
    </Paper>
  );

  return (
    <AbsoluteFill>
      {frame < sweepAt ? before : frame > sweepAt + 34 ? after : <SweepOnPaper progress={sweep} from={before} to={after} />}

      <Narration section={S} />
      <Sfx name="impact" at={tThirteen - 2} volume={0.22} />
      <Sfx name="denied" at={tStalls} volume={0.16} />
      <Sfx name="paper-slide" at={tClose - 2} volume={0.2} />
      <Sfx name="counter" at={tTwo} volume={0.14} />
      <Sfx name="paper-slide" at={tWeek - 2} volume={0.18} />
      <Sfx name="whoosh" at={tThe + 4} volume={0.18} />
      <Sfx name="denied" at={tHome - 8} volume={0.2} />
      <Sfx name="loop-back" at={tBack - 16} volume={0.22} />
      <Sfx name="pop" at={tTwice} volume={0.16} />
      <Sfx name="coin" at={tPublic} volume={0.2} />
      <Sfx name="clock" at={tThe} volume={0.08} trim={tPublic + 20 - tThe} />
      <Sfx name="xray-sweep" at={sweepAt} volume={0.3} />
      <Sfx name="shimmer" at={tOphi} volume={0.12} />
    </AbsoluteFill>
  );
};
