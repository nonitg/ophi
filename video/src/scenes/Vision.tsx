import React from "react";
import { AbsoluteFill, Freeze, Sequence, useCurrentFrame } from "remotion";
import { Paper, ToothSprite, XrayBeam } from "../components";
import { Narration, Sfx } from "../audio";
import { lineAt, wordAt } from "../vo";
import { offsets } from "../timeline";
import { ease, font } from "../theme";
import { Market } from "./Market";
import { RootTree, TreeNode } from "../components/vision/RootTree";
import { Tally } from "../components/vision/Tally";
import { MoatStage } from "../components/vision/MoatStage";
import { Platform, trunkBottom } from "../components/vision/Platform";
import { film, lerp, ramp, window01 } from "../components/vision/util";

const w0 = (word: string, nth = 0) => wordAt("vision", 0, word, nth);
const w1 = (word: string, nth = 0) => wordAt("vision", 1, word, nth);

// Tooth sprite placement; root tips measured from public/tooth/xray/0000.png (374,931) and (650,1054) of 1200.
const TOOTH = { size: 380, left: 770, top: 8 };

// Entrance: the Market scene's last frame is x-rayed into the film world by a panoramic beam.
const SWEEP = 20;
const W = 1920;
const beamX = (p: number) => -90 + ease.inOut(Math.max(0, Math.min(1, p))) * (W + 90 + 420); // matches XraySweep
const marketFrames = offsets.market.frames;

// The evolutionary tree grows from the platform trunk: each branch is a payer the same engine can check.
// Wider tree = bigger market.
const T = trunkBottom;
const BRANCHES = [
  { d: `M 960 ${T} C 960 ${T + 25}, 960 ${T + 45}, 960 560`, from: w1("grows") - 6, to: w1("CDCP"), w: 8 },
  { d: "M 960 560 C 960 590, 960 615, 960 640", from: w1("treatment"), to: w1("federal") + 6, w: 8 },
  { d: "M 960 598 C 930 630, 800 640, 700 650 C 650 655, 610 660, 590 665", from: w1("federal") - 4, to: w1("NIHB"), w: 5, hairs: 5 },
  { d: "M 960 628 C 1000 660, 1150 668, 1250 685 C 1300 695, 1330 700, 1345 705", from: w1("NIHB") + 6, to: w1("plans"), w: 5, hairs: 5 },
  { d: "M 960 640 C 959 685, 962 735, 960 776", from: w1("provincial"), to: w1("private") - 2, w: 8 },
  { d: "M 960 776 C 960 800, 960 830, 960 856", from: w1("insurers") - 6, to: w1("insurers") + 8, w: 7 },
  { d: "M 960 856 C 900 876, 760 884, 600 890 C 520 894, 430 900, 360 912", from: w1("insurers"), to: w1("2024"), w: 5, hairs: 8 },
  { d: "M 960 856 C 1030 876, 1180 884, 1340 890 C 1420 894, 1510 900, 1590 908", from: w1("insurers") + 4, to: w1("2024") + 4, w: 5, hairs: 8 },
  { d: "M 958 862 C 925 890, 830 912, 760 926 C 720 934, 700 939, 690 945", from: w1("Then") - 2, to: w1("sent"), w: 5, hairs: 4 },
  { d: "M 962 862 C 990 895, 1070 918, 1150 934 C 1195 944, 1225 951, 1245 958", from: w1("every", 2) - 2, to: w1("paid", 1), w: 5, hairs: 4 },
];

const NODES: TreeNode[] = [
  { id: "cdcp", x: 960, y: 560, at: w1("CDCP"), tag: "Today · the wedge", name: "Every CDCP treatment", detail: "~1.9M preauthorizations a year", side: "right" },
  { id: "nihb", x: 590, y: 665, at: w1("NIHB"), tag: "Federal", name: "NIHB", detail: "$380M dental a year", side: "left" },
  { id: "prov", x: 1345, y: 705, at: w1("plans"), tag: "Provincial", name: "Provincial plans", detail: "public dental programs", side: "right" },
  { id: "priv", x: 960, y: 776, at: w1("private"), tag: "Private", name: "Private insurers", detail: "$12.6B in dental claims, 2024", side: "right", big: true },
  { id: "claims", x: 690, y: 945, at: w1("sent"), tag: "Before sending", name: "Every claim", detail: "checked before it's sent", side: "left" },
  { id: "audit", x: 1245, y: 958, at: w1("paid", 1), tag: "After payment · audits", name: "Claims already paid", detail: "checked before an audit does", side: "right" },
];

// Market reach under the tree: the bracket spans the lit branches, so the width reads as the market.
const REACH = [
  { at: w1("CDCP"), l: 900, r: 1020 },
  { at: w1("NIHB"), l: 590, r: 1020 },
  { at: w1("plans"), l: 590, r: 1345 },
  { at: w1("2024") - 6, l: 360, r: 1590 },
];

const Reach: React.FC<{ frame: number; opacity: number }> = ({ frame, opacity }) => {
  const done = REACH.filter((s) => frame >= s.at);
  if (!done.length || opacity <= 0) return null;
  const cur = done[done.length - 1];
  const prev = done.length > 1 ? done[done.length - 2] : { l: 960, r: 960 };
  const t = ramp(frame, cur.at, cur.at + 24, ease.inOut);
  const l = lerp(prev.l, cur.l, t);
  const r = lerp(prev.r, cur.r, t);
  const y = 1050;
  return (
    <div style={{ position: "absolute", inset: 0, opacity: opacity * ramp(frame, REACH[0].at, REACH[0].at + 14) }}>
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        <path d={`M ${l} ${y - 10} L ${l} ${y + 10} M ${l} ${y} L ${r} ${y} M ${r} ${y - 10} L ${r} ${y + 10}`} stroke={film.metal} strokeWidth={2} fill="none" />
      </svg>
      <div
        style={{
          position: "absolute",
          left: 960,
          top: y - 13,
          transform: "translateX(-50%)",
          padding: "2px 16px",
          background: film.ink,
          fontFamily: font.mono,
          fontSize: 17,
          letterSpacing: "0.14em",
          color: film.metal,
          whiteSpace: "nowrap",
        }}
      >
        WIDTH = MARKET
      </div>
    </div>
  );
};

export const Vision: React.FC = () => {
  const frame = useCurrentFrame();
  const l2 = lineAt("vision", 2);

  // The tree recedes behind the moat; later data flows up its roots, then it clears for the ring.
  const recede = ramp(frame, l2.from - 4, l2.from + 30);
  const clear = ramp(frame, wordAt("vision", 2, "proprietary") - 10, wordAt("vision", 2, "proprietary") + 20);
  const treeOpacity = lerp(1, 0.13, recede) * (1 - clear);
  const flow = ramp(frame, wordAt("vision", 2, "request"), wordAt("vision", 2, "request") + 20) * (1 - clear);
  const glow = ramp(frame, w0("evolves") - 10, w0("evolves") + 20);

  // Start partway into the beam's ease so it enters on the first frame instead of idling.
  const sweep = 0.22 + 0.78 * (frame / SWEEP);
  const x = Math.max(0, Math.min(W, beamX(sweep)));
  const swept = sweep >= 1;

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ clipPath: swept ? undefined : `inset(0 ${W - x}px 0 0)` }}>
        <Paper variant="film" glow={1}>
          <AbsoluteFill style={{ opacity: treeOpacity, filter: recede > 0 ? `blur(${6 * recede}px)` : undefined }}>
            <div style={{ position: "absolute", left: TOOTH.left, top: TOOTH.top, filter: `drop-shadow(0 0 ${24 + 18 * glow}px rgba(170,210,190,0.35))` }}>
              <ToothSprite variant="xray" rotationSpeed={0} size={TOOTH.size} spotlight={0.7} />
            </div>
            <Platform />
            <RootTree branches={BRANCHES} nodes={NODES} flow={flow} />
            <Reach frame={frame} opacity={1 - recede} />
          </AbsoluteFill>

          {/* Field-guide plate label: a callback to the cold open. */}
          <div style={{ position: "absolute", left: 72, top: 64, opacity: window01(frame, 6, l2.from + 10, 16) }}>
            <div style={{ fontFamily: font.mono, fontSize: 17, letterSpacing: "0.14em", color: film.boneDim }}>FIG. 2</div>
            <div style={{ fontFamily: font.display, fontStyle: "italic", fontSize: 44, color: film.bone, marginTop: 6 }}>Praeauctorizatio evolvens</div>
            <div style={{ fontFamily: font.mono, fontSize: 19, color: film.boneDim, marginTop: 6 }}>the preauthorization, evolving</div>
          </div>

          <Tally
            start={w1("CDCP") - 6}
            opacity={1 - recede}
            steps={[
              { at: w1("CDCP"), value: 3.4, note: "CDCP $3.4B" },
              { at: w1("NIHB"), value: 3.8, note: "NIHB $0.4B" },
              { at: w1("plans"), value: 3.8, plus: true, note: "provinces +" },
              { at: w1("twelve"), value: 16.4, note: "private $12.6B" },
            ]}
            extras={[
              { at: w1("sent"), text: "+ every claim, before it's sent" },
              { at: w1("paid", 1), text: "+ every claim already paid" },
            ]}
            sources="Sources: CDCP benefits funding 2026–27, Health Canada · NIHB dental 2023–24, Indigenous Services Canada · private insurers' dental claims 2024, CLHIA Facts 2025"
          />

          <MoatStage />
        </Paper>
      </AbsoluteFill>

      {/* Scene A: Market frozen on its last frame. Freeze mutes its audio, so its narration never replays. */}
      {!swept && (
        <AbsoluteFill style={{ clipPath: `inset(0 0 0 ${x}px)` }}>
          <Sequence durationInFrames={marketFrames} layout="none" name="Market (frozen)">
            <Freeze frame={marketFrames - 1}>
              <Market />
            </Freeze>
          </Sequence>
        </AbsoluteFill>
      )}
      <XrayBeam progress={sweep} />

      <Narration section="vision" />
      <Sfx name="xray-sweep" at={0} volume={0.4} />
      <Sfx name="grow" at={w0("foundation") + 6} volume={0.45} />
      <Sfx name="grow" at={w1("grows") - 6} volume={0.4} />
      <Sfx name="pop" at={w1("CDCP")} volume={0.3} />
      <Sfx name="pop" at={w1("NIHB")} volume={0.25} />
      <Sfx name="pop" at={w1("plans")} volume={0.25} />
      <Sfx name="grow" at={w1("insurers")} volume={0.45} />
      <Sfx name="counter" at={w1("twelve")} volume={0.25} />
      <Sfx name="pop" at={w1("sent")} volume={0.25} />
      <Sfx name="pop" at={w1("paid", 1)} volume={0.25} />
      <Sfx name="whoosh" at={l2.from - 4} volume={0.25} />
    </AbsoluteFill>
  );
};
