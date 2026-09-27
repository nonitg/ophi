import React from "react";
import { AbsoluteFill, interpolate, staticFile, useCurrentFrame, Easing } from "remotion";
import { DemoTag, Paper } from "../components";
import type { Box, Shot, ShotMeta } from "../components";
import { Cut } from "../components/demo/Cut";
import { StageShot } from "../components/demo/StageShot";
import { Callout, Dot, PmsFlow, STAGE, StageRail, Stamp, TechChip, WatchMotif } from "../components/demo/Overlays";
import { FilmTimeline } from "../components/demo/FilmTimeline";
import { PacketFan } from "../components/demo/PacketFan";
import { DecisionBeat } from "../components/demo/DecisionBeat";
import { Narration, Sfx } from "../audio";
import { lineAt, wordAt } from "../vo";

import m01 from "../../public/app-v2/01-board.json";
import m03 from "../../public/app-v2/03-case-teresa.json";
import m04 from "../../public/app-v2/04-case-teresa-requirements.json";
import m05 from "../../public/app-v2/05-case-teresa-fix-plan.json";
import m06 from "../../public/app-v2/06-board-first-taken.json";
import m07 from "../../public/app-v2/07-board-chair-closed.json";
import m09 from "../../public/app-v2/09-dentist-review.json";
import m13 from "../../public/app-v2/13-send-to-sun-life.json";
import m14a from "../../public/app-v2/14a-case-with-sun-life.json";
import m14c from "../../public/app-v2/14c-okafor-overdue.json";
import m17 from "../../public/app-v2/17-crown-booked.json";
import m23 from "../../public/app-v2/23-past-outcomes.json";
import m31 from "../../public/app-v2/31-rec-paper-answer.json";

const shot = (name: string, meta: unknown, mode: "viewport" | "full" = "viewport"): Shot => ({
  src: staticFile(`app-v2/${name}${mode === "full" ? "-full" : ""}.png`),
  meta: meta as ShotMeta,
  mode,
});

const BOARD = shot("01-board", m01);
const TAKEN_1 = shot("06-board-first-taken", m06);
const TAKEN_2 = shot("07-board-chair-closed", m07);
const CASE = shot("03-case-teresa", m03, "full");
// The raw full-page capture has the sticky nav baked in mid-page; public/demo-v2/04-reqs-full.png patches it out.
const REQS: Shot = { src: staticFile("demo-v2/04-reqs-full.png"), meta: m04 as unknown as ShotMeta, mode: "full" };
const FIXPLAN = shot("05-case-teresa-fix-plan", m05);
const OUTCOMES = shot("23-past-outcomes", m23);
const REVIEW = shot("09-dentist-review", m09);
const SEND = shot("13-send-to-sun-life", m13);
const WAITING = shot("14a-case-with-sun-life", m14a);
const ABELDENT = shot("31-rec-paper-answer", m31);
const OVERDUE = shot("14c-okafor-overdue", m14c);
const BOOKED = shot("17-crown-booked", m17);

// Page-space boxes the captures don't name (CSS px of the 1440×900 viewport, or of the full page).
const OPEN_CASE: Box = { x: 1286, y: 191, w: 104, h: 36 };
const CHAIR_CHIP: Box = { x: 48, y: 244, w: 130, h: 24 };
const BOARD_LEFT: Box = { x: 38, y: 462, w: 200, h: 330 };
const BOARD_RIGHT: Box = { x: 1201, y: 462, w: 200, h: 330 };
const HERO_ROWS: Box = { x: 42, y: 278, w: 790, h: 100 };
const CASE_TOP: Box = { x: 28, y: 140, w: 1028, h: 180 };
const REQ_ROWS: Box = { x: 47, y: 1003, w: 1009, h: 452 };
const NOW_RISK: Box = { x: 36, y: 400, w: 1000, h: 170 };
const COUNTS: Box = { x: 28, y: 216, w: 540, h: 52 };
const CALL_TAGS: Box[] = [
  { x: 68, y: 251, w: 48, h: 20 },
  { x: 68, y: 277, w: 46, h: 20 },
  { x: 68, y: 304, w: 46, h: 20 },
];
const PRE_TAGS: Box[] = [
  { x: 68, y: 480, w: 48, h: 20 },
  { x: 68, y: 609, w: 46, h: 20 },
  { x: 68, y: 718, w: 48, h: 20 },
  { x: 68, y: 744, w: 46, h: 20 },
];
const SUGGESTED: Box[] = [
  { x: 843, y: 456, w: 46, h: 26 },
  { x: 843, y: 585, w: 46, h: 26 },
  { x: 843, y: 694, w: 46, h: 26 },
];
const REVIEW_CALLS: Box = { x: 52, y: 70, w: 980, h: 330 };
const OVERDUE_TOP: Box = { x: 28, y: 148, w: 1028, h: 350 };
const ABEL_TOP: Box = { x: 28, y: 330, w: 1028, h: 270 };
const BOOKED_STAMP: Box = { x: 560, y: 330, w: 300, h: 68 };

const W = (line: number, word: string, nth = 0) => wordAt("demo", line, word, nth);
const L = (line: number) => lineAt("demo", line).from;

// Beat frames (section-relative), each hung on a spoken word so a re-timed voiceover re-times the cut.
const T = {
  sorted: W(0, "sorted"),
  next: W(0, "next."),
  ophi: W(0, "Ophi"),
  database: W(0, "database."),
  l1: L(1),
  chair: W(1, "chair,"),
  checked: W(1, "checked"),
  requirement: W(1, "requirement"),
  guide: W(1, "guide."),
  xray: W(2, "x-ray"),
  three: W(2, "three"),
  old: W(2, "old;"),
  wants: W(2, "wants"),
  gum: W(2, "gum"),
  incomplete: W(2, "incomplete"),
  l3: L(3),
  risk: W(3, "risk"),
  fixes: W(3, "fixes"),
  how: W(3, "how"),
  much: W(3, "much"),
  denial: W(3, "denial."),
  xray2: W(3, "x-ray"),
  l4: L(4),
  pounces: W(4, "pounces."),
  captures: W(4, "captures"),
  before: W(4, "before"),
  door: W(4, "door."),
  l5: L(5),
  language: W(5, "language"),
  read5: W(5, "read"),
  notes: W(5, "notes"),
  prefilled: W(5, "pre-filled"),
  seven5: W(5, "seven"),
  if5: W(5, "If"),
  falls: W(5, "falls"),
  today: W(5, "today,"),
  not: W(5, "not"),
  l6: L(6),
  assembles: W(6, "assembles"),
  signs: W(6, "signs,"),
  staff: W(6, "staff"),
  software: W(6, "software"),
  use: W(6, "use."),
  l7: L(7),
  watching: W(7, "watching."),
  checks: W(7, "checks"),
  practice: W(7, "practice"),
  answer: W(7, "answer,"),
  flags: W(7, "flags"),
  past: W(7, "past"),
  seven: W(7, "seven"),
  days: W(7, "days."),
  l8: L(8),
  arrives: W(8, "arrives,"),
  ai: W(8, "AI"),
  reads: W(8, "reads"),
  reason: W(8, "reason,"),
  book: W(8, "book"),
  expires: W(8, "expires,"),
  or: W(8, "or"),
  fix: W(8, "fix"),
  resubmit: W(8, "resubmit."),
  l9: L(9),
  step: W(9, "step."),
  goal: W(9, "goal"),
};

// Shot windows (section frames). Consecutive cuts overlap by their entrance length.
const S = {
  board: [0, T.chair + 8],
  case: [T.chair - 2, T.l3 + 2],
  outcomes: [T.l3 - 4, T.fixes + 10],
  fixplan: [T.fixes + 2, T.l4 + 2],
  pounce: [T.l4 - 6, T.l5 + 4],
  review: [T.l5 - 6, T.l6 + 2],
  packet: [T.l6 - 4, T.staff + 16],
  send: [T.staff + 4, T.use + 16],
  waiting: [T.use + 8, T.checks + 4],
  abeldent: [T.checks - 4, T.flags + 6],
  overdue: [T.flags - 2, T.l8 + 6],
  decision: [T.l8 - 4, T.l9 + 12],
  booked: [T.l9, 2400],
};
const rel = (from: number) => (x: number) => x - from;
const ease = Easing.bezier(0.65, 0, 0.35, 1);

// The case page compresses upward while the film timeline sits under it, so the graphic never covers app text.
const TIMELINE_TOP = 598;
const SHRUNK_H = TIMELINE_TOP - 14 - STAGE.y;

const CaseShot: React.FC = () => {
  const f = useCurrentFrame();
  const c = rel(S.case[0]);
  const shrink = Math.min(
    interpolate(f, [c(T.three) - 8, c(T.three) + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease }),
    interpolate(f, [c(T.gum) - 6, c(T.gum) + 12], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease }),
  );
  const frame = { ...STAGE, h: STAGE.h - (STAGE.h - SHRUNK_H) * shrink };
  return (
    <StageShot
      frame={frame}
      fitH={STAGE.h}
      shot={CASE}
      states={[{ at: c(T.checked) + 30, shot: REQS, dur: 14 }]}
      camera={[
        { at: 0, focus: CASE_TOP, zoom: 1.9 },
        { at: c(T.checked), focus: "reqs_fold", zoom: 2.1, pad: 24, dur: 30 },
        { at: c(T.requirement) + 6, focus: REQ_ROWS, zoom: 1.62, dur: 26 },
        { at: c(T.guide) - 4, focus: "citation_row_guide_635", zoom: 2.4, pad: 150, dur: 24 },
        { at: c(T.xray), focus: "req_pa", zoom: 2.1, pad: 30, dur: 26 },
        { at: c(T.gum) - 4, focus: "req_perio", zoom: 2.0, pad: 30, dur: 26 },
      ]}
      highlights={[
        { from: c(T.checked) + 20, to: c(T.requirement) + 6, box: "reqs_count", style: "ring" },
        { from: c(T.guide) + 16, to: c(T.xray) - 2, box: "citation_row_guide_635", style: "ring" },
        { from: c(T.xray) + 20, to: c(T.gum) - 4, box: "req_pa", style: "ring", color: "#c2412d" },
        { from: c(T.incomplete) - 4, to: c(T.l3) + 2, box: "req_perio", style: "ring", color: "#c2412d" },
      ]}
    />
  );
};

export const Demo: React.FC = () => {
  const b = rel(S.board[0]);
  const o = rel(S.outcomes[0]);
  const x = rel(S.fixplan[0]);
  const p = rel(S.pounce[0]);
  const r = rel(S.review[0]);
  const s = rel(S.send[0]);
  const w = rel(S.waiting[0]);
  const a = rel(S.abeldent[0]);
  const v = rel(S.overdue[0]);
  const d = rel(S.decision[0]);
  const e = rel(S.booked[0]);
  return (
    <AbsoluteFill>
      <Paper lightOver={false} light={0.7} drift={-60} />

      {/* 0 · Board: push in to a readable scale, glide across who-acts-next, pull back to the data source */}
      <Cut from={S.board[0]} to={S.board[1]} enter="rise" enterDur={18} exit="zoom" exitDur={10} name="board">
        <StageShot
          frame={STAGE}
          shot={BOARD}
          camera={[
            { at: 0, focus: "full" },
            { at: 6, focus: BOARD_LEFT, zoom: 2.1, dur: 36 },
            { at: b(T.sorted) - 4, focus: BOARD_RIGHT, zoom: 2.1, dur: b(T.next) - b(T.sorted) + 22 },
            { at: b(T.ophi) - 2, focus: "full", dur: 28 },
            { at: b(T.l1), focus: "hero_card", zoom: 1.6, pad: 16, dur: 24 },
          ]}
          highlights={[
            ...[0, 1, 2, 3, 4, 5].map((i) => ({ from: b(T.sorted) + 4 + i * 7, to: b(T.ophi) - 4, box: `col_${i}`, style: "underline" as const })),
            { from: b(T.l1) + 8, to: b(T.chair) + 8, box: CHAIR_CHIP, style: "ring", radius: 12 },
          ]}
          cursor={[
            { at: b(T.l1), to: { x: 1150, y: 520 } },
            { at: b(T.l1) + 4, to: centreOf(OPEN_CASE), dur: b(T.chair) - b(T.l1) - 10, click: true },
          ]}
        />
      </Cut>
      <PmsFlow start={T.ophi + 6} end={T.l1 + 4} x={120} y={330} toX={372} toY={470} />

      {/* 1–2 · Case: every CDCP requirement checked and cited; the old x-ray on its timeline; the perio chart */}
      <Cut from={S.case[0]} to={S.case[1]} enter="zoom" enterDur={16} exit="fade" exitDur={6} name="case">
        <CaseShot />
      </Cut>
      <FilmTimeline start={T.three - 2} film={T.three + 6} gap={T.old} win={T.wants} end={T.gum + 2} top={TIMELINE_TOP} />

      {/* 3a · The risk model's training data: past outcomes */}
      <Cut from={S.outcomes[0]} to={S.outcomes[1]} enter="push" enterDur={12} exit="zoom" exitDur={8} name="outcomes">
        <StageShot
          frame={STAGE}
          shot={OUTCOMES}
          camera={[
            { at: 0, focus: COUNTS, zoom: 2.3, pad: 40 },
            { at: 10, focus: COUNTS, zoom: 2.2, pad: 40, dur: 60 },
          ]}
          highlights={[{ from: o(T.risk) + 4, to: o(S.outcomes[1]), box: COUNTS, style: "ring", radius: 12 }]}
        />
      </Cut>

      {/* 3b · Fixes ranked by the denial risk each removes */}
      <Cut from={S.fixplan[0]} to={S.fixplan[1]} enter="zoom" enterDur={12} exit="none" name="fix-plan">
        <StageShot
          frame={STAGE}
          shot={FIXPLAN}
          camera={[
            { at: 0, focus: NOW_RISK, zoom: 2.0 },
            { at: x(T.denial) - 4, focus: "fix_1", zoom: 1.72, pad: 24, dur: 26 },
          ]}
          highlights={[
            { from: x(T.how), to: x(T.denial) + 2, box: "risk_levels", style: "ring" },
            { from: x(T.xray2) - 6, to: x(T.l4) + 2, box: "fix_1", style: "ring" },
          ]}
        />
      </Cut>

      {/* 4 · The hygienist pounces: both captures before Teresa leaves */}
      <Cut from={S.pounce[0]} to={S.pounce[1]} enter="whip" enterDur={12} exit="zoom" exitDur={10} name="pounce">
        <StageShot
          frame={STAGE}
          shot={BOARD}
          states={[
            // Layout shifts between these captures, so they swap almost instantly, like the live UI.
            { at: p(T.pounces) + 12, shot: TAKEN_1, dur: 3 },
            { at: p(T.captures) + 8, shot: TAKEN_2, dur: 3 },
          ]}
          camera={[
            { at: 0, focus: HERO_ROWS, zoom: 2.2 },
            { at: p(T.before) + 4, focus: "full", dur: 26 },
          ]}
          highlights={[{ from: p(T.door) - 4, to: p(S.pounce[1]), box: "teresa_card", style: "ring" }]}
          cursor={[
            { at: 4, to: { x: 1000, y: 330 } },
            { at: p(T.pounces) - 2, to: "mark_taken_pa", dur: 12, click: true },
            { at: p(T.captures) - 4, to: "mark_taken_perio", dur: 10, click: true },
          ]}
        />
      </Cut>

      {/* 5 · Dentist review: the language model's pre-fills, and the one call that is the dentist's */}
      <Cut from={S.review[0]} to={S.review[1]} enter="zoom" enterDur={14} exit="fade" exitDur={8} name="review">
        <StageShot
          frame={STAGE}
          shot={REVIEW}
          camera={[
            { at: 0, focus: REVIEW_CALLS, zoom: 1.7 },
            { at: r(T.prefilled) - 6, focus: "prefilled_group", zoom: 1.72, pad: 10, dur: 28 },
            { at: r(T.if5) - 4, focus: "your_call_row_surfaces", zoom: 2.2, pad: 24, dur: 26 },
          ]}
          highlights={[
            ...CALL_TAGS.map((t, i) => ({ from: r(T.read5) + i * 5, to: r(T.prefilled) - 4, box: t, style: "ring" as const, radius: 8 })),
            ...PRE_TAGS.map((t, i) => ({ from: r(T.prefilled) + 18 + i * 5, to: r(T.if5) - 6, box: t, style: "ring" as const, radius: 8 })),
            ...SUGGESTED.map((t, i) => ({ from: r(T.seven5) + i * 5, to: r(T.if5) - 6, box: t, style: "ring" as const, color: "#3f8f5f", radius: 8 })),
            { from: r(T.falls) - 4, to: r(S.review[1]), box: "surfaces_evidence", style: "ring", radius: 6 },
          ]}
        />
      </Cut>

      {/* 6 · Assemble, sign, send from the practice software */}
      <Cut from={S.packet[0]} to={S.packet[1]} enter="fade" enterDur={10} exit="none" name="packet">
        <PacketFan start={2} sign={T.signs - S.packet[0] - 14} />
      </Cut>
      <Cut from={S.send[0]} to={S.send[1]} enter="push" enterDur={14} exit="zoom" exitDur={8} name="send">
        <StageShot
          frame={STAGE}
          shot={SEND}
          camera={[{ at: 0, focus: "now", zoom: 1.85, pad: 16 }]}
          highlights={[{ from: s(T.software) - 8, to: s(S.send[1]), box: "pms_step", style: "ring" }]}
          cursor={[
            { at: 4, to: { x: 700, y: 720 } },
            { at: s(T.use) - 18, to: "mark_sent", dur: 16, click: true },
          ]}
        />
      </Cut>

      {/* 7 · Watch: waiting on Sun Life, the status read from the practice software, the overdue flag */}
      <Cut from={S.waiting[0]} to={S.waiting[1]} enter="zoom" enterDur={12} exit="fade" exitDur={6} name="waiting">
        <StageShot
          frame={STAGE}
          shot={WAITING}
          camera={[{ at: 0, focus: "now", zoom: 1.8, pad: 20 }]}
          highlights={[{ from: w(T.watching) - 4, to: w(S.waiting[1]), box: "turnaround", style: "ring" }]}
        />
      </Cut>
      <Cut from={S.abeldent[0]} to={S.abeldent[1]} enter="push" enterDur={12} exit="fade" exitDur={6} name="abeldent">
        <StageShot
          frame={STAGE}
          shot={ABELDENT}
          camera={[{ at: 0, focus: ABEL_TOP, zoom: 1.95 }]}
          highlights={[
            { from: a(T.practice), to: a(S.abeldent[1]), box: "carrier_ref", style: "ring" },
            { from: a(T.answer), to: a(S.abeldent[1]), box: "paper_lead", style: "underline" },
          ]}
        />
      </Cut>
      <Cut from={S.overdue[0]} to={S.overdue[1]} enter="push" enterDur={12} exit="fade" exitDur={8} name="overdue">
        <StageShot
          frame={STAGE}
          shot={OVERDUE}
          camera={[{ at: 0, focus: OVERDUE_TOP, zoom: 1.75 }]}
          highlights={[
            { from: v(T.past) - 4, to: v(S.overdue[1]), box: "sent_ago", style: "ring", radius: 14 },
            { from: v(T.seven) - 4, to: v(S.overdue[1]), box: "past_turnaround", style: "ring" },
            { from: v(T.days) + 8, to: v(S.overdue[1]), box: "mailbox_line", style: "underline" },
          ]}
        />
      </Cut>

      {/* 8 · The letter comes back: the letter reader names the reason; the two next steps */}
      <Cut from={S.decision[0]} to={S.decision[1]} enter="fade" enterDur={8} exit="fade" exitDur={12} name="decision">
        <DecisionBeat
          cue={{
            arrive: d(T.l8),
            read: d(T.reads),
            reason: d(T.reason),
            book: d(T.book),
            expires: d(T.expires),
            or: d(T.or),
            fix: d(T.fix),
            resubmit: d(T.resubmit),
          }}
        />
      </Cut>

      {/* 9 · The goal is the crown */}
      <Cut from={S.booked[0]} to={S.booked[1]} enter="zoom" enterDur={14} name="booked">
        <StageShot
          frame={STAGE}
          shot={BOOKED}
          camera={[
            { at: 0, focus: "now", zoom: 2.0, pad: 30 },
            { at: e(T.step), focus: "now", zoom: 2.08, pad: 30, dur: 80 },
          ]}
          highlights={[{ from: e(T.step), to: e(T.goal) + 90, box: "booked_line", style: "ring" }]}
          pins={[{ from: e(T.goal), box: BOOKED_STAMP, node: <Stamp at={e(T.goal)} text="CROWN BOOKED" size={0.86} /> }]}
        />
      </Cut>

      {/* The band: tech and AI labels left, plain-words captions right, the stage rail, the demo tag */}
      <TechChip start={T.ophi + 2} end={T.checked} kind="db" label="PRACTICE-SOFTWARE DATABASE" detail="read-only · re-read within 15 s of a chart edit" />
      <TechChip start={T.checked + 2} end={T.l3} kind="rules" label="RULE ENGINE" detail="14 requirements · 31 cited clauses" />
      <TechChip start={T.risk} end={T.l4 - 2} kind="ai" label="RISK MODEL" detail="gradient-boosted trees · trained on 720 past requests (simulated)" />
      <TechChip start={T.language} end={T.today + 10} kind="ai" label="LAYA" detail="421M-parameter language model, fine-tuned on dental notes · ~30 ms" />
      <WatchMotif start={T.watching - 6} end={T.l8 + 2} pms="ABELDent" hot={T.practice} />
      <TechChip start={T.ai} end={T.l9 + 6} kind="ai" label="LETTER READER" detail="Sun Life's words → one of 16 reasons" />

      <Callout start={T.sorted + 4} end={T.ophi} title="One board · sorted by who acts next" tone="paper" />
      <Callout start={T.guide + 12} end={T.three - 6} title="Every check cites its CDCP rule" />
      <Callout start={T.risk + 6} end={T.fixes + 8} title="What the risk model learned from" tone="paper" />
      <Callout start={T.much} end={T.l4} title="Fixes ranked by the denial risk each removes" icon={<Dot />} />
      <Callout start={T.pounces + 12} end={T.captures + 8} title="Taken. Ophi checked the chart again." icon={<Dot c="#7fc59a" />} />
      <Callout start={T.captures + 10} end={T.door} title="Nothing left to take. The patient can go." icon={<Dot c="#7fc59a" />} />
      <Callout start={T.door} end={T.l5 + 2} title="Moved to Dentist review" tone="paper" />
      <Callout start={T.l5 + 6} end={T.prefilled - 2} title="Dentist view · Dr. Priya Lau" tone="paper" />
      <Callout start={T.seven5} end={T.if5 - 4} title="Pre-filled 7 of 9 · from the chart and the note" />
      <Callout start={T.not - 4} end={T.l6} title="Decided in the chair, not after a denial" tone="orange" />
      <Callout start={T.software - 4} end={T.use + 14} title="Ophi never sends. Staff do, from their PMS." />
      <Callout start={T.practice} end={T.flags} title="Status read live from ABELDent" tone="paper" />
      <Callout start={T.seven - 4} end={T.l8 + 2} title="Flagged: past the usual 7 days" tone="orange" />

      <StageRail at={[0, T.l1, T.l3, T.l5, T.l6, T.l7, T.l8]} start={10} />
      <div style={{ position: "absolute", left: 0, top: 972, width: 1920, height: 108 }}>
        <DemoTag start={10} />
      </div>

      <Narration section="demo" />
      <Sfx name="whoosh" at={2} volume={0.25} />
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <Sfx key={i} name="pop" at={T.sorted + 4 + i * 7} volume={0.12} />
      ))}
      <Sfx name="shimmer" at={T.ophi + 6} volume={0.16} />
      <Sfx name="click" at={T.chair - 2} volume={0.4} />
      <Sfx name="whoosh" at={T.chair - 2} volume={0.22} />
      <Sfx name="pop" at={T.guide + 16} volume={0.2} />
      <Sfx name="paper-slide" at={T.three + 2} volume={0.25} />
      <Sfx name="denied" at={T.old + 4} volume={0.2} />
      <Sfx name="whoosh" at={S.outcomes[0]} volume={0.22} />
      <Sfx name="shimmer" at={T.risk} volume={0.16} />
      <Sfx name="pop" at={T.how} volume={0.2} />
      <Sfx name="whoosh" at={S.pounce[0]} volume={0.3} />
      <Sfx name="pounce" at={T.pounces - 2} volume={0.45} />
      <Sfx name="click" at={T.pounces + 10} volume={0.45} />
      <Sfx name="chime" at={T.pounces + 14} volume={0.25} />
      <Sfx name="click" at={T.captures + 6} volume={0.45} />
      <Sfx name="chime" at={T.captures + 10} volume={0.25} />
      <Sfx name="whoosh" at={S.review[0]} volume={0.2} />
      <Sfx name="shimmer" at={T.language} volume={0.16} />
      {[0, 1, 2, 3].map((i) => (
        <Sfx key={`t${i}`} name="pop" at={T.prefilled + 18 + i * 5} volume={0.1} />
      ))}
      {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
        <Sfx key={`p${i}`} name="paper-slide" at={S.packet[0] + 2 + i * 5} volume={0.14} />
      ))}
      <Sfx name="click" at={T.use - 2} volume={0.35} />
      <Sfx name="chime" at={T.use + 12} volume={0.18} />
      <Sfx name="whoosh" at={S.abeldent[0]} volume={0.2} />
      <Sfx name="pop" at={T.practice} volume={0.18} />
      <Sfx name="whoosh" at={S.overdue[0]} volume={0.2} />
      <Sfx name="denied" at={T.seven - 2} volume={0.2} />
      <Sfx name="paper-slide" at={T.l8 + 2} volume={0.3} />
      <Sfx name="xray-sweep" at={T.reads} volume={0.16} />
      <Sfx name="shimmer" at={T.reason} volume={0.18} />
      <Sfx name="approved" at={T.book - 4} volume={0.26} />
      <Sfx name="whoosh" at={T.or - 4} volume={0.2} />
      <Sfx name="whoosh" at={S.booked[0]} volume={0.2} />
      <Sfx name="stamp" at={T.goal} volume={0.55} />
    </AbsoluteFill>
  );
};

const centreOf = (bx: Box) => ({ x: bx.x + bx.w / 2, y: bx.y + bx.h / 2 });
