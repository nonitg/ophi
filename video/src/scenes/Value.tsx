import React from "react";
import { AbsoluteFill, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Counter, Footnote, Paper, ToothSprite } from "../components";
import { AppPanel, CareTrack, Chip, Chore, DenialCards, GuideStack, PillarNav, RewindClock, RoiMeter, Rise, SpokenLine, WeeklyWatch, ramp } from "../components/market/parts";
import { Narration, Sfx } from "../audio";
import { wordAt, lineAt } from "../vo";
import { color, ease, font, springs, type } from "../theme";

const w = (line: number, word: string, nth = 0) => wordAt("value", line, word, nth);

// Why a clinic pays: four reasons, each with one number or image, then the ROI made visibly true.
// Page-space boxes (CSS px, 1440-wide) on the Past denials capture, from public/app-v2/22-recover.json.
const RB = {
  headline: { x: 28, y: 119.4, w: 900, h: 35.8 },
  lede: { x: 28, y: 165.2, w: 742.5, h: 24.8 },
  first_why: { x: 404.2, y: 236, w: 487.5, h: 21.7 },
  draft_script: { x: 919.8, y: 359.1, w: 126.8, h: 32 },
  // Row 2 (between the row rules at y≈409 and y≈601), dimmed while row 1 is discussed.
  row_two: { x: 0, y: 409, w: 1440, h: 192 },
  // The whole "Draft what to say" button with a margin, lifted out because its column is outside the crop.
  draft_button: { x: 912, y: 352, w: 141, h: 46 },
};
// The panel's crop: the name and Sun Life reason columns (the actions column starts at x≈919), headline plus
// the first two full rows (row rule at y≈601). Clean column and row boundaries, so no word is cut.
const PAGE = { x: 16, y: 104, w: 889, h: 497 };
const PANEL_W = 1020;
const PS = PANEL_W / PAGE.w;
const DRAFT = { x: (560 - PAGE.x) * PS, y: (318 - PAGE.y) * PS };
export const Value: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const q = { why: w(0, "Why"), would: w(0, "would"), a: w(0, "a"), clinic: w(0, "clinic"), pay: w(0, "pay?") };
  const p1 = { one: w(0, "One:"), treatment: w(0, "treatment"), that: w(0, "that"), happens: w(0, "happens."), single: w(0, "single"), crown: w(0, "crown"), eight: w(0, "eight"), dollars: w(0, "dollars"), ontario: w(0, "Ontario"), complete: w(0, "complete"), moving: w(0, "moving"), care: w(0, "care.") };
  const p2 = { two: w(1, "Two:"), hours: w(1, "hours"), back: w(1, "back."), chart: w(1, "chart"), hunting: w(1, "hunting,"), retyping: w(1, "retyping,"), second: w(1, "second"), visit: w(1, "visit.") };
  const p3 = { three: w(1, "Three:"), rules: w(1, "rules"), that: w(1, "that", 0), keep: w(1, "keep"), up: w(1, "up."), guide: w(1, "guide"), twice: w(1, "twice"), ten: w(1, "ten"), months: w(1, "months;"), checks: w(1, "checks"), every: w(1, "every"), week: w(1, "week.") };
  const p4 = { four: w(2, "Four:"), money: w(2, "money"), table: w(2, "table."), finds: w(2, "finds"), denials: w(2, "denials"), never: w(2, "never"), resubmitted: w(2, "resubmitted,"), drafts: w(2, "drafts"), call: w(2, "call"), patient: w(2, "patient."), demo: w(2, "demo"), eleven: w(2, "eleven"), dollars: w(2, "dollars"), crowns: w(2, "crowns.") };
  const l3 = lineAt("value", 3);
  const roi = { hundred: w(3, "hundred"), month: w(3, "month,"), one: w(3, "one"), crown: w(3, "crown"), every: w(3, "every"), four: w(3, "four"), months: w(3, "months"), pays: w(3, "pays") };

  // Stage changes between reasons.
  const end1 = p2.two - 14;
  const end2 = p3.three - 14;
  const end3 = p4.four - 12;
  const end4 = l3.from - 6;

  // The opening question: centred, then it lifts away as the reasons begin.
  const qLift = ramp(frame, p1.one - 14, 16, ease.inOut);
  const active = frame < end1 ? 0 : frame < end2 ? 1 : frame < end3 ? 2 : frame < end4 ? 3 : -1;

  return (
    <Paper light={0.55}>
      <Narration section="value" />

      {/* Opening question */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: 1 - qLift, transform: `translateY(${-qLift * 120}px) scale(${1 - 0.1 * qLift})` }}>
        <SpokenLine
          size={138}
          words={[
            { text: "Why", at: q.why },
            { text: "would", at: q.would },
            { text: "a", at: q.a },
            { text: "clinic", at: q.clinic },
            { text: "pay?", at: q.pay },
          ]}
        />
      </AbsoluteFill>

      <PillarNav
        start={p1.one - 6}
        out={end4}
        active={active}
        items={[
          { title: "Treatment that happens", at: p1.treatment },
          { title: "Hours back", at: Math.min(p2.hours, p2.two + 10) },
          { title: "Rules that keep up", at: Math.min(p3.rules, p3.three + 10) },
          { title: "Money on the table", at: Math.min(p4.money, p4.four + 10) },
        ]}
      />

      {/* 1 · Treatment that happens */}
      <Stage from={p1.one} to={end1}>
        <Numeral n="1" at={p1.one} />
        <Settle top={250} drop={170} until={p1.eight - 10}>
          <SpokenLine
            size={type.h1}
            words={[
              { text: "Treatment", at: p1.treatment },
              { text: "that", at: p1.that, br: true },
              { text: "happens.", at: p1.happens },
            ]}
          />
          <Rise at={p1.eight - 4} style={{ marginTop: 40, display: "flex", alignItems: "baseline", gap: 28 }}>
            <Counter to={884} start={p1.eight} duration={Math.max(18, p1.dollars - p1.eight + 4)} prefix="$" style={{ fontFamily: font.display, fontSize: 210, color: color.forest, lineHeight: 0.9, letterSpacing: "-0.03em" }} />
            <div style={{ fontFamily: font.sans, fontSize: 32, color: color.muted, lineHeight: 1.3, opacity: ramp(frame, p1.ontario, 12) }}>
              one CDCP crown
              <br />
              to an Ontario clinic
            </div>
          </Rise>
        </Settle>
        <div style={{ position: "absolute", right: 90, top: 250, opacity: ramp(frame, p1.one + 2, 18) }}>
          <ToothSprite size={540} rotationSpeed={0.06} frameOffset={8} spotlight={0.8} />
          <div style={{ textAlign: "center", marginTop: -30, fontFamily: font.mono, fontSize: type.label, letterSpacing: "0.1em", color: color.muted, opacity: ramp(frame, p1.one + 12, 12) }}>
            CROWN · CODE 27211
          </div>
        </div>
        <div style={{ position: "absolute", left: 300, top: 850 }}>
          <CareTrack at={Math.min(p1.complete - 4, p1.treatment + 12)} moveFrom={p1.complete + 6} moveTo={p1.care + 8} width={1240} />
        </div>
        <Footnote text="Crown 27211, Ontario GP benefit grid 2026 (Sun Life): $884.15, before lab fee." start={p1.eight} end={end1} bottom={34} />
      </Stage>

      {/* 2 · Hours back */}
      <Stage from={end1} to={end2}>
        <Numeral n="2" at={Math.min(p2.two, end1 + 6)} />
        <Settle top={250} drop={150} until={p2.chart - 12}>
          <SpokenLine
            size={type.h1}
            words={[
              { text: "Hours", at: Math.min(p2.hours, p2.two + 10) },
              { text: "back.", at: Math.min(p2.back, p2.two + 16) },
            ]}
          />
          <div style={{ marginTop: 44 }}>
            <Chore text="Chart hunting" at={p2.chart - 3} strikeAt={p2.hunting + 8} />
            <Chore text="Retyping" at={p2.retyping - 3} strikeAt={p2.retyping + 14} />
            <Chore text="A second visit" at={p2.second - 3} strikeAt={p2.visit + 6} />
          </div>
        </Settle>
        <div style={{ position: "absolute", right: 170, top: 260 }}>
          <RewindClock at={Math.min(p2.hours, p2.two + 10)} dur={Math.max(40, p2.visit - Math.min(p2.hours, p2.two + 10))} size={470} />
        </div>
      </Stage>

      {/* 3 · Rules that keep up */}
      <Stage from={end2} to={end3}>
        <Numeral n="3" at={Math.min(p3.three, end2 + 6)} />
        <Settle top={250} drop={170} until={p3.guide - 10} width={840}>
          <SpokenLine
            size={type.h1}
            words={[
              { text: "Rules", at: Math.min(p3.rules, p3.three + 10) },
              { text: "that", at: Math.min(p3.that, p3.three + 14) },
              { text: "keep", at: Math.min(p3.keep, p3.three + 18), br: true },
              { text: "up.", at: Math.min(p3.up, p3.three + 22) },
            ]}
          />
          <Rise at={p3.twice - 4} style={{ marginTop: 40, fontFamily: font.display, fontSize: 52, color: color.forest, lineHeight: 1.1 }}>
            2 guide changes <span style={{ color: color.muted }}>in 10 months</span>
          </Rise>
          <div style={{ marginTop: 34 }}>
            <WeeklyWatch at={p3.guide - 2} sweepTo={p3.months + 4} changesAt={p3.twice} pulseAt={p3.every} width={800} />
          </div>
        </Settle>
        <div style={{ position: "absolute", right: 150, top: 200 }}>
          <GuideStack firstAt={Math.min(p3.guide - 4, p3.three + 14)} secondAt={p3.twice} checkAt={p3.checks} />
        </div>
        <div style={{ position: "absolute", left: 300, top: 880 }}>
          <Chip at={p3.checks}>
            <span style={{ color: color.orange }}>✦</span>
            <b style={{ fontWeight: 700 }}>Rules watch</b>
            <span style={{ opacity: 0.8 }}>checks CDCP sources weekly · flags changes for a dentist</span>
          </Chip>
        </div>
        <Footnote text="CDCP Dental Benefits Guide: versions effective Dec 7, 2025 and Apr 1, 2026." start={p3.guide} end={end3} bottom={34} />
      </Stage>

      {/* 4 · Money already on the table */}
      <Stage from={end3} to={end4}>
        <Numeral n="4" at={Math.min(p4.four, end3 + 6)} />
        <div style={{ position: "absolute", left: 300, top: 250 }}>
          <SpokenLine
            size={type.h1}
            words={[
              { text: "Money", at: Math.min(p4.money, p4.four + 10) },
              { text: "already", at: Math.min(w(2, "already"), p4.four + 14) },
              { text: "on", at: Math.min(w(2, "on"), p4.four + 18) },
              { text: "the", at: Math.min(w(2, "the"), p4.four + 20) },
              { text: "table.", at: Math.min(p4.table, p4.four + 24) },
            ]}
          />
        </div>
        <div style={{ position: "absolute", left: 300, top: 400, width: 440 }}>
          <Rise at={Math.min(p4.money, p4.four + 12)} style={{ fontFamily: font.display, fontSize: 50, lineHeight: 1.1, color: color.forest }}>
            10 past denials
            <br />
            <span style={{ color: color.muted }}>never resubmitted</span>
          </Rise>
          <div style={{ marginTop: 30 }}>
            <DenialCards at={Math.min(p4.money, p4.four + 16)} flipFrom={p4.drafts} flipTo={p4.patient + 4} />
          </div>
          <Rise at={p4.eleven - 6} style={{ marginTop: 34 }}>
            <Counter to={11455} start={p4.eleven} duration={Math.max(18, p4.dollars - p4.eleven + 6)} prefix="$" style={{ fontFamily: font.display, fontSize: 116, color: color.orange, letterSpacing: "-0.03em", lineHeight: 1 }} />
            <div style={{ fontFamily: font.sans, fontSize: 28, color: color.forest, marginTop: 10, opacity: ramp(frame, p4.crowns - 4, 10) }}>of crowns that haven't happened</div>
          </Rise>
        </div>
        <div style={{ position: "absolute", left: 800, top: 378 }}>
          <AppPanel
            src={staticFile("app-v2/22-recover.png")}
            width={PANEL_W}
            aspect={PAGE.w / PAGE.h}
            at={Math.min(p4.money, p4.four + 12)}
            regions={[{ at: 0, x: PAGE.x, y: PAGE.y, w: PAGE.w }]}
            dims={[{ box: RB.row_two, from: p4.resubmitted - 6, to: p4.eleven - 6 }]}
            rings={[
              { box: RB.headline, from: p4.finds, to: p4.resubmitted - 8 },
              { box: RB.first_why, from: p4.resubmitted, to: p4.eleven - 8 },
              { box: { x: RB.lede.x, y: RB.lede.y, w: 430, h: RB.lede.h }, from: p4.eleven },
            ]}
            insets={[{ box: RB.draft_button, x: DRAFT.x, y: DRAFT.y, zoom: 2, from: p4.drafts - 4, to: p4.eleven - 8 }]}
            cursor={{ point: { x: DRAFT.x + RB.draft_button.w * 1.2, y: DRAFT.y + RB.draft_button.h * 1.1 }, from: p4.resubmitted + 4, clickAt: p4.drafts + 6, until: p4.eleven - 14 }}
          />
        </div>
        <Footnote text="Demo clinic, fictional data: the app's Past denials page." start={p4.finds} end={end4} bottom={34} />
      </Stage>

      {/* ROI */}
      <Stage from={end4 + 10} to={durationInFrames + 30}>
        <div style={{ position: "absolute", left: 210, top: 150 }}>
          <Rise at={end4 + 10}>
            <div style={{ fontFamily: font.mono, fontSize: type.label, letterSpacing: "0.1em", color: color.muted }}>THE MATH</div>
          </Rise>
          <div style={{ marginTop: 18, display: "flex", alignItems: "baseline", gap: 26 }}>
            <Rise at={roi.hundred - 4}>
              <span style={{ fontFamily: font.display, fontSize: 150, color: color.forest, letterSpacing: "-0.03em", lineHeight: 1 }}>$199</span>
            </Rise>
            <Rise at={roi.month - 2}>
              <span style={{ fontFamily: font.display, fontSize: 64, color: color.muted }}>a month</span>
            </Rise>
          </div>
        </div>
        <div style={{ position: "absolute", left: 210, top: 470 }}>
          <RoiMeter crownAt={roi.month - 4} crownLabelAt={roi.crown - 2} monthAts={[roi.month + 4, roi.every, roi.four, roi.months]} paidAt={roi.pays} width={1500} />
        </div>
        <Rise at={roi.four} style={{ position: "absolute", left: 210, top: 860, fontFamily: font.sans, fontSize: 32, color: color.forest }}>
          4 months of Ophi, <b style={{ fontWeight: 700 }}>$796</b>, is less than one crown, <b style={{ fontWeight: 700 }}>$884</b>.
        </Rise>
        <Footnote text="Crown 27211, Ontario GP benefit grid 2026 (Sun Life): $884.15, before lab fee. Ophi pricing: $199 per location per month." start={roi.one} bottom={34} />
      </Stage>

      {/* Sound */}
      <Sfx name="whoosh" at={p1.one - 10} volume={0.25} />
      <Sfx name="pop" at={p1.one} volume={0.35} />
      <Sfx name="counter" at={p1.eight} volume={0.3} />
      <Sfx name="whoosh" at={end1} volume={0.25} />
      <Sfx name="pop" at={p2.two} volume={0.35} />
      <Sfx name="click" at={p2.hunting + 8} volume={0.3} />
      <Sfx name="click" at={p2.retyping + 14} volume={0.3} />
      <Sfx name="click" at={p2.visit + 6} volume={0.3} />
      <Sfx name="whoosh" at={end2} volume={0.25} />
      <Sfx name="pop" at={p3.three} volume={0.35} />
      <Sfx name="paper-slide" at={p3.twice} volume={0.4} />
      <Sfx name="chime" at={p3.checks + 4} volume={0.35} />
      <Sfx name="whoosh" at={end3} volume={0.25} />
      <Sfx name="pop" at={p4.four} volume={0.35} />
      <Sfx name="click" at={p4.drafts + 6} volume={0.35} />
      <Sfx name="counter" at={p4.eleven} volume={0.3} />
      <Sfx name="coin" at={p4.dollars + 4} volume={0.3} />
      <Sfx name="whoosh" at={end4} volume={0.25} />
      {[roi.month + 4, roi.every, roi.four, roi.months].map((at, i) => (
        <Sfx key={i} name="pop" at={at} volume={0.3} />
      ))}
      <Sfx name="stamp" at={roi.pays} volume={0.45} />
      <Sfx name="coin" at={roi.pays + 4} volume={0.35} />
    </Paper>
  );
};

// A reason's stage: slides in from the right, leaves to the left.
const Stage: React.FC<{ from: number; to: number; children: React.ReactNode }> = ({ from, to, children }) => {
  const frame = useCurrentFrame();
  if (frame < from - 2 || frame > to + 14) return null;
  const i = ramp(frame, from - 2, 14);
  const o = 1 - ramp(frame, to, 10, ease.in);
  // A slow push-in keeps holds alive while the narrator talks.
  const push = 1 + 0.014 * Math.min(1, Math.max(0, (frame - from) / Math.max(1, to - from)));
  return <AbsoluteFill style={{ opacity: Math.min(i, o), transform: `translateX(${(1 - i) * 80 - (1 - o) * 80}px) scale(${push})`, transformOrigin: "40% 45%" }}>{children}</AbsoluteFill>;
};

// Large numeral on the left margin.
const Numeral: React.FC<{ n: string; at: number }> = ({ n, at }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - at, fps, config: springs.overshoot });
  return (
    <div style={{ position: "absolute", left: 120, top: 210, fontFamily: font.display, fontSize: 230, lineHeight: 1, color: color.orange, transform: `scale(${0.6 + 0.4 * p})`, opacity: Math.min(1, p * 1.4), transformOrigin: "50% 70%" }}>
      {n}
    </div>
  );
};

// A reason's text block sits lower (near the frame's optical centre) while it is only a title, then lifts to
// its reading position as the first supporting line arrives, so no frame reads as an empty lower half.
const Settle: React.FC<{ top: number; drop: number; until: number; width?: number; children: React.ReactNode }> = ({ top, drop, until, width, children }) => {
  const frame = useCurrentFrame();
  const lift = ramp(frame, until, 18, ease.inOut);
  return <div style={{ position: "absolute", left: 300, top, width, transform: `translateY(${(1 - lift) * drop}px)` }}>{children}</div>;
};
