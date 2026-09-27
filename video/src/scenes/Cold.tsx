import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Counter, Letterbox, Paper, ToothSprite, TypeOn } from "../components";
import { cellCenter, gridSize, RequestGrid } from "../components/story/RequestGrid";
import { fadeOut, lerp, prog } from "../components/story/util";
import { Narration, Sfx } from "../audio";
import { lineAt, wordAt } from "../vo";
import { color, ease, font } from "../theme";

const S = "cold";
const ORIGIN = 44; // the specimen becomes this card in the grid
const GRID_LEFT = 300;
const GRID_TOP = 540 - gridSize.h / 2;
const TOOTH = { x: 720, y: 540, size: 660 };

// Cold open: a nature-documentary plate. The approved preauthorization is observed like a rare specimen,
// then revealed as one of 100 requests, of which 46 survive.
export const Cold: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const tHere = wordAt(S, 0, "here");
  const tFront = wordAt(S, 0, "front");
  const tRarest = wordAt(S, 0, "rarest");
  const tApproved = wordAt(S, 0, "approved");
  const tStatus = wordAt(S, 0, "preauthorization", 0, "to") - 6;
  const tFewer = wordAt(S, 1, "fewer");
  const pull = lineAt(S, 0).to - 4; // specimen pulls back into the grid as the first line ends

  const fadeIn = prog(frame, 0, 16, ease.inOut);
  const bars = 1 - prog(frame, durationInFrames - 16, 16, ease.inOut);

  // Specimen: slow documentary push-in, then shrink into its grid cell.
  const push = interpolate(frame, [0, pull], [0.94, 1.03], { extrapolateRight: "clamp", easing: ease.inOut });
  const toCell = prog(frame, pull, 26, ease.inOut);
  const cell = cellCenter(ORIGIN);
  const tx = lerp(TOOTH.x, GRID_LEFT + cell.x, toCell);
  const ty = lerp(TOOTH.y, GRID_TOP + cell.y, toCell);
  const tsize = lerp(TOOTH.size * push, 70, toCell);
  const toothOpacity = 1 - prog(frame, pull + 18, 8);

  const label = fadeOut(frame, pull - 2, 14);
  const binom = prog(frame, tRarest, 26);
  const common = prog(frame, tApproved, 18);
  const stat = prog(frame, tFewer, 16);

  return (
    <AbsoluteFill style={{ background: "#050807" }}>
      <AbsoluteFill style={{ opacity: fadeIn }}>
        <Paper light={0.9}>
          {/* museum-plate vignette */}
          <AbsoluteFill style={{ background: "radial-gradient(ellipse 62% 70% at 38% 50%, rgba(15,36,29,0) 45%, rgba(15,36,29,0.16) 100%)" }} />

          {/* grid of 100 requests */}
          <div style={{ position: "absolute", left: GRID_LEFT, top: GRID_TOP }}>
            <RequestGrid appearAt={pull + 8} origin={ORIGIN} lightAt={tFewer} lit={46} every={1} />
          </div>

          {/* the specimen */}
          <div
            style={{
              position: "absolute",
              left: tx - tsize / 2,
              top: ty - tsize / 2,
              opacity: toothOpacity,
            }}
          >
            <ToothSprite size={tsize} rotationSpeed={0.05} frameOffset={8} spotlight={1 - toCell} />
          </div>

          {/* field-guide plate label */}
          <div style={{ position: "absolute", left: 1150, top: 250, width: 640, opacity: label, color: color.forest }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontFamily: font.mono, fontSize: 18, letterSpacing: "0.14em", color: color.muted, opacity: prog(frame, tHere, 14) }}>
              <span>A FIELD GUIDE · PLATE XLVI</span>
              <span>No. 0046</span>
            </div>
            <div style={{ height: 1.5, background: color.forest, opacity: 0.5, margin: "14px 0 26px", transformOrigin: "left", transform: `scaleX(${prog(frame, tHere, 30)})` }} />
            <div
              style={{
                fontFamily: font.display,
                fontStyle: "italic",
                fontSize: 74,
                lineHeight: 1.02,
                letterSpacing: "-0.01em",
                clipPath: `inset(-10% ${100 - binom * 100}% -20% 0)`,
                transform: `translateY(${(1 - binom) * 14}px)`,
              }}
            >
              Praeauctorizatio
              <br />
              approbata
            </div>
            <div style={{ fontFamily: font.sans, fontSize: 34, marginTop: 18, opacity: common, transform: `translateY(${(1 - common) * 10}px)` }}>
              the approved preauthorization
            </div>
            <div style={{ height: 1, background: color.forest, opacity: 0.25, margin: "30px 0 20px" }} />
            <div style={{ display: "grid", gridTemplateColumns: "150px 1fr", rowGap: 14, fontSize: 21 }}>
              <span style={{ fontFamily: font.mono, color: color.muted, letterSpacing: "0.1em", opacity: prog(frame, tFront, 8) }}>HABITAT</span>
              <TypeOn text="Front desks, Canadian dental clinics" start={tFront} cps={30} size={21} caret={frame < tRarest} />
              <span style={{ fontFamily: font.mono, color: color.muted, letterSpacing: "0.1em", opacity: prog(frame, tStatus, 8) }}>STATUS</span>
              <TypeOn text="Rare" start={tStatus} cps={14} size={21} color={color.orange} caret={frame < pull} />
            </div>
          </div>

          {/* the survival rate */}
          <div style={{ position: "absolute", left: 1090, top: 300, width: 720, color: color.forest, opacity: stat }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 26, transform: `translateY(${(1 - stat) * 24}px)` }}>
              <Counter to={46} start={tFewer} duration={46} style={{ fontFamily: font.display, fontSize: 300, lineHeight: 0.9, letterSpacing: "-0.04em" }} />
              <span style={{ fontFamily: font.display, fontSize: 84, color: color.muted }}>in 100</span>
            </div>
            <div style={{ fontFamily: font.sans, fontSize: 34, lineHeight: 1.3, marginTop: 26, maxWidth: 600, opacity: prog(frame, tFewer + 14, 16) }}>
              complete CDCP preauthorization requests are approved
            </div>
            <div
              style={{
                fontFamily: font.display,
                fontStyle: "italic",
                fontSize: 52,
                color: color.orange,
                marginTop: 30,
                opacity: prog(frame, wordAt(S, 1, "half"), 14),
              }}
            >
              Fewer than half make it.
            </div>
          </div>

          <div style={{ position: "absolute", left: 1090, top: 846, width: 700, fontFamily: font.sans, fontSize: 18, lineHeight: 1.35, color: color.muted, opacity: prog(frame, tFewer + 10, 14) }}>
            46% of complete CDCP preauthorization requests approved, Mar 1 – May 31, 2026 · Health Canada via Oral Health Group
          </div>

          {/* plate furniture: leader line and figure caption */}
          <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, opacity: label * prog(frame, tHere + 20, 20) }}>
            <path
              d="M1136 520 L990 520 L905 450"
              fill="none"
              stroke={color.forest}
              strokeOpacity={0.55}
              strokeWidth={1.5}
              strokeDasharray={260}
              strokeDashoffset={260 * (1 - prog(frame, tHere + 20, 26))}
            />
            <circle cx={905} cy={450} r={4} fill={color.orange} opacity={prog(frame, tHere + 40, 8)} />
          </svg>
          <div style={{ position: "absolute", left: TOOTH.x - 320, top: 868, width: 640, textAlign: "center", fontFamily: font.mono, fontSize: 17, letterSpacing: "0.08em", color: color.muted, opacity: label * prog(frame, tHere + 30, 16) }}>
            FIG. 1 — OBSERVED AT A FRONT DESK, ONTARIO
          </div>
        </Paper>
      </AbsoluteFill>
      <Letterbox open={bars} />

      <Narration section={S} />
      <Sfx name="amb-clinic" at={0} volume={0.14} />
      <Sfx name="typewriter" at={tFront} volume={0.18} />
      <Sfx name="typewriter" at={tStatus} volume={0.18} trim={24} />
      <Sfx name="whoosh" at={pull} volume={0.22} />
      <Sfx name="counter" at={tFewer} volume={0.16} />
      <Sfx name="pop" at={tFewer + 44} volume={0.18} />
    </AbsoluteFill>
  );
};
