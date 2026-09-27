import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { Counter, Footnote, Paper, ToothSprite } from "../components";
import { Stamp } from "../components/story/Stamp";
import { fadeOut, lerp, pop, prog } from "../components/story/util";
import { Narration, Sfx } from "../audio";
import { wordAt } from "../vo";
import { color, ease, font } from "../theme";

const S = "patient";

// 75 dots, one per 100,000 enrolled Canadians; the orange one is Teresa.
const DOTS = 75;
const TERESA_DOT = 52;

// Layout (1080p). The file is the hero alone, then shrinks into a left column beside the right-hand beat.
const FILE = { w: 880, h: 560 };
const SMALL = 0.8;
const HERO_POS = { x: (1920 - FILE.w) / 2, y: (1080 - FILE.h) / 2 };
const LEFT_POS = { x: 110, y: 250 };
const RIGHT = { x: 880, w: 920 };
const ROW_H = 122;

// A checklist row: a numbered ghost placeholder from `ghostAt` (so all four slots read at once), filled with
// its requirement when the narrator names it at `at`.
const Requirement: React.FC<{ n: number; ghostAt: number; at: number; title: string; sub: string }> = ({ n, ghostAt, at, title, sub }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ghost = prog(frame, ghostAt, 10);
  const p = pop(frame, at, fps, "critical");
  const filled = prog(frame, at, 8);
  const bar = (w: number, h: number) => <div style={{ width: w, height: h, borderRadius: h / 2, background: "rgba(25,58,48,0.1)" }} />;
  return (
    <div style={{ position: "relative", height: ROW_H, boxSizing: "border-box", display: "flex", alignItems: "center", gap: 26, opacity: ghost, transform: `translateY(${(1 - ghost) * 14}px)`, borderTop: "1.5px solid rgba(25,58,48,0.14)" }}>
      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: 12,
          border: `3px solid ${color.forest}`,
          opacity: 0.3 + 0.5 * filled,
          transform: `scale(${1 + 0.12 * Math.sin(Math.PI * filled)})`,
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: font.mono,
          fontSize: 24,
          color: color.forest,
        }}
      >
        {n}
      </div>
      <div style={{ position: "relative", flex: 1, height: "100%" }}>
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", justifyContent: "center", gap: 14, opacity: 1 - filled }}>
          {bar([300, 240, 280, 420][n - 1], 22)}
          {bar([220, 330, 260, 360][n - 1], 14)}
        </div>
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", justifyContent: "center", opacity: p, transform: `translateX(${(1 - p) * 40}px)` }}>
          <div style={{ fontFamily: font.sans, fontWeight: 500, fontSize: 38, color: color.forest, lineHeight: 1.15 }}>{title}</div>
          <div style={{ fontFamily: font.sans, fontSize: 26, color: color.muted, marginTop: 6 }}>{sub}</div>
        </div>
      </div>
    </div>
  );
};

// Teresa, one of 7.5 million enrolled, and the four things Sun Life needs before her crown can be booked.
export const Patient: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const tMeet = wordAt(S, 0, "meet");
  const tCrown = wordAt(S, 0, "crown");
  const tSeven = wordAt(S, 0, "seven");
  const tCanadians = wordAt(S, 0, "canadians");
  const tEnrolled = wordAt(S, 0, "enrolled");
  const tBut = wordAt(S, 1, "but");
  const tBook = wordAt(S, 1, "book");
  const tSun = wordAt(S, 1, "sun");
  const tTreatment = wordAt(S, 1, "treatment");
  const tRecent = wordAt(S, 1, "recent");
  const tFull = wordAt(S, 1, "full");
  const tProof = wordAt(S, 1, "proof");
  const tCriteria = wordAt(S, 1, "criteria");

  const card = pop(frame, tMeet - 4, fps, "critical");
  const crown = pop(frame, tCrown, fps, "overshoot");
  const move = prog(frame, tSeven - 10, 24, ease.inOut);
  const fileX = lerp(HERO_POS.x, LEFT_POS.x, move);
  const fileY = lerp(HERO_POS.y, LEFT_POS.y, move);
  const fileScale = lerp(1, SMALL, move);

  const enrolled = prog(frame, tSeven, 16);
  const enrolledOut = fadeOut(frame, tBut - 6, 14);
  const sheet = pop(frame, tSun - 2, fps, "critical");

  // The booking pill: appears on the right as "book" is said, is blocked, then tucks under the file when the
  // preauthorization sheet takes the right-hand side.
  const pill = pop(frame, tBut + 6, fps, "critical");
  const locked = prog(frame, tBook + 8, 10);
  const tuck = prog(frame, tSun - 8, 22, ease.inOut);
  const pillX = lerp(RIGHT.x + RIGHT.w / 2, LEFT_POS.x, tuck);
  const pillY = lerp(470, LEFT_POS.y + FILE.h * SMALL + 40, tuck);
  const pillScale = lerp(1.5, 1, tuck);

  return (
    <Paper light={0.85}>
      {/* Teresa's file */}
      <div
        style={{
          position: "absolute",
          left: fileX,
          top: fileY,
          width: FILE.w,
          height: FILE.h,
          transformOrigin: "top left",
          transform: `translateY(${(1 - card) * 60}px) rotate(${(1 - card) * -3}deg) scale(${fileScale})`,
          opacity: card,
          background: "#fbfaf4",
          borderRadius: 28,
          boxShadow: "0 36px 70px rgba(15,36,29,0.16), 0 4px 12px rgba(15,36,29,0.08)",
          padding: "52px 64px",
          boxSizing: "border-box",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: font.mono, fontSize: 28, letterSpacing: "0.14em", color: color.muted }}>
          <span>PATIENT FILE</span>
          <span style={{ color: color.orange }}>FICTIONAL</span>
        </div>
        <div style={{ fontFamily: font.display, fontSize: 140, color: color.forest, lineHeight: 1, marginTop: 30, letterSpacing: "-0.02em" }}>Teresa, 64</div>
        <div style={{ fontFamily: font.sans, fontSize: 34, color: color.muted, marginTop: 16 }}>Recall exam today · Dr. Priya Lau</div>
        <div style={{ display: "flex", alignItems: "center", gap: 28, marginTop: 44, opacity: crown, transform: `scale(${0.9 + 0.1 * crown})`, transformOrigin: "left center" }}>
          <div style={{ width: 140, height: 140, borderRadius: 26, background: color.forest, overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <ToothSprite size={160} rotationSpeed={0.12} frameOffset={30} />
          </div>
          <div>
            <div style={{ fontFamily: font.sans, fontWeight: 500, fontSize: 46, color: color.forest }}>Needs a crown</div>
            <div style={{ fontFamily: font.mono, fontSize: 30, color: color.muted, marginTop: 8 }}>Tooth 46 · lower right molar</div>
          </div>
        </div>
      </div>

      {/* booking, blocked until the preauthorization comes back */}
      <div
        style={{
          position: "absolute",
          left: pillX,
          top: pillY,
          opacity: pill,
          transformOrigin: tuck > 0.5 ? "top left" : "top left",
          transform: `translateX(${(1 - tuck) * -210 * pillScale}px) translateY(${(1 - pill) * 24}px) scale(${pillScale})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          gap: 12,
        }}
      >
        <div
          style={{
            padding: "18px 32px",
            borderRadius: 999,
            background: locked > 0.5 ? "rgba(25,58,48,0.12)" : color.forest,
            color: locked > 0.5 ? "rgba(25,58,48,0.5)" : color.ivory,
            fontFamily: font.sans,
            fontWeight: 500,
            fontSize: 30,
            whiteSpace: "nowrap",
            textDecoration: locked > 0.5 ? "line-through" : "none",
          }}
        >
          Book crown · Thu Oct 15
        </div>
        <div style={{ fontFamily: font.mono, fontSize: 23, color: color.orange, letterSpacing: "0.06em", opacity: locked, whiteSpace: "nowrap" }}>WAITING ON PREAUTHORIZATION</div>
      </div>

      {/* 7.5 million enrolled */}
      <div style={{ position: "absolute", left: RIGHT.x, top: 250, width: RIGHT.w, opacity: enrolled * enrolledOut, transform: `translateY(${(1 - enrolled) * 30 - (1 - enrolledOut) * 30}px)` }}>
        <Counter to={7500000} start={tSeven} duration={34} style={{ fontFamily: font.display, fontSize: 170, color: color.forest, letterSpacing: "-0.03em", lineHeight: 1 }} />
        <div style={{ fontFamily: font.sans, fontSize: 38, color: color.forest, marginTop: 18, opacity: prog(frame, tCanadians - 4, 12) }}>
          Canadians enrolled in the Canadian Dental Care Plan
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(15, 40px)", gap: 16, marginTop: 44 }}>
          {Array.from({ length: DOTS }, (_, i) => {
            const on = prog(frame, tSeven + i * 0.45, 6);
            const isTeresa = i === TERESA_DOT && frame >= tEnrolled;
            const t = pop(frame, tEnrolled, fps, "overshoot");
            return (
              <div
                key={i}
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 999,
                  background: isTeresa ? color.orange : color.forest,
                  opacity: on * (isTeresa ? 1 : 0.8),
                  transform: `scale(${on * (isTeresa ? 0.8 + 0.4 * t : 1)})`,
                }}
              />
            );
          })}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", width: 824, marginTop: 22, fontFamily: font.mono, fontSize: 24, color: color.muted, letterSpacing: "0.06em" }}>
          <span>EACH DOT = 100,000 PEOPLE</span>
          <span style={{ color: color.orange, opacity: prog(frame, tEnrolled, 10) }}>● TERESA</span>
        </div>
      </div>

      {/* what Sun Life needs first */}
      <div
        style={{
          position: "absolute",
          left: RIGHT.x,
          top: 170,
          width: RIGHT.w,
          background: "#fbfaf4",
          borderRadius: 28,
          boxShadow: "0 36px 70px rgba(15,36,29,0.14), 0 4px 12px rgba(15,36,29,0.06)",
          padding: "48px 56px 30px",
          boxSizing: "border-box",
          opacity: sheet,
          transform: `translateY(${(1 - sheet) * 80}px)`,
        }}
      >
        <div style={{ fontFamily: font.mono, fontSize: 22, letterSpacing: "0.12em", color: color.muted }}>SUN LIFE RUNS THE PLAN · IT MUST APPROVE</div>
        <div style={{ fontFamily: font.display, fontSize: 80, color: color.forest, marginTop: 12, marginBottom: 20, letterSpacing: "-0.015em", lineHeight: 1.1, opacity: prog(frame, tSun + 8, 14) }}>
          A preauthorization
        </div>
        <Requirement n={1} ghostAt={tSun + 6 + 0 * 3} at={tTreatment} title="Treatment plan" sub="Codes, fees and the tooth" />
        <Requirement n={2} ghostAt={tSun + 6 + 1 * 3} at={tRecent} title="Recent x-rays" sub="Periapical and bitewings, last 12 months" />
        <Requirement n={3} ghostAt={tSun + 6 + 2 * 3} at={tFull} title="Full gum chart" sub="Six readings around every tooth" />
        <Requirement n={4} ghostAt={tSun + 6 + 3 * 3} at={tProof} title="Proof the tooth meets the criteria" sub="As written in CDCP's Dental Benefits Guide" />
      </div>
      {/* lands across the checklist's right edge, over row 3, clear of every label */}
      <Stamp at={tCriteria + 4} lines={["PENDING", "SUN LIFE REVIEW"]} rotate={7} size={1.35} style={{ left: 1510, top: 628 }} />

      <Footnote text="7,535,054 enrolled since launch, as of Aug 31, 2026 · canada.ca CDCP statistics" start={tSeven + 10} end={tBut} />

      <Narration section={S} />
      <Sfx name="paper-slide" at={tMeet - 4} volume={0.3} />
      <Sfx name="pop" at={tCrown} volume={0.16} />
      <Sfx name="counter" at={tSeven} volume={0.16} />
      <Sfx name="pop" at={tBut + 6} volume={0.14} />
      <Sfx name="denied" at={tBook + 8} volume={0.14} />
      <Sfx name="paper-slide" at={tSun - 2} volume={0.25} />
      {[tTreatment, tRecent, tFull, tProof].map((t, i) => (
        <Sfx key={i} name="pop" at={t} volume={0.12} />
      ))}
      <Sfx name="stamp" at={tCriteria + 4} volume={0.4} />
    </Paper>
  );
};
