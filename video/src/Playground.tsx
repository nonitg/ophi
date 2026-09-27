import React from "react";
import { AbsoluteFill, interpolate, Sequence, staticFile, useCurrentFrame } from "remotion";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { AppShot, Counter, DemoTag, Footnote, Letterbox, Paper, ToothSprite, TypeOn, Wordmark, XraySweep, xraySweep } from "./components";
import type { ShotMeta } from "./components";
import { color, ease, font, type } from "./theme";
import board from "../public/app/01-board.json";
import boardTaken from "../public/app/06-board-first-taken.json";
import reqs from "../public/app/04-case-teresa-requirements.json";

export const PLAYGROUND_FRAMES = 840;

const shot = (name: string, meta: unknown, mode: "viewport" | "full" = "viewport") => ({
  src: staticFile(`app/${name}${mode === "full" ? "-full" : ""}.png`),
  meta: meta as ShotMeta,
  mode,
});

const Specimen: React.FC<{ variant: "normal" | "xray" }> = ({ variant }) => {
  const frame = useCurrentFrame();
  const open = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp", easing: ease.out });
  const body = (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <ToothSprite variant={variant} size={640} rotationSpeed={0.06} spotlight={1} />
      <div style={{ position: "absolute", left: 180, bottom: 240 }}>
        <TypeOn text={"Corona approbata\nstatus: rare"} start={20} color={variant === "xray" ? color.bone : color.forest} size={26} />
      </div>
      <Footnote text="Playground · component check, not script copy" start={10} dark={variant === "xray"} bottom={170} />
    </AbsoluteFill>
  );
  return (
    <>
      {variant === "xray" ? <Paper variant="film">{body}</Paper> : <Paper drift={-40}>{body}</Paper>}
      <Letterbox open={open} />
    </>
  );
};

const Numbers: React.FC = () => (
  <Paper>
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 40 }}>
      <Wordmark start={6} size={240} />
      <div style={{ fontFamily: font.display, fontSize: type.h2, color: color.forest }}>
        <Counter to={17857} start={30} duration={50} />
        <span style={{ fontFamily: font.sans, fontSize: type.body, color: color.muted, marginLeft: 18 }}>clinics</span>
      </div>
      <div style={{ fontFamily: font.display, fontStyle: "italic", fontSize: type.h3, color: color.orange }}>
        <Counter to={42.6} decimals={1} prefix="$" suffix="M" start={50} duration={40} />
      </div>
    </AbsoluteFill>
    <DemoTag start={10} />
  </Paper>
);

const Sweep: React.FC = () => {
  const frame = useCurrentFrame();
  return <XraySweep progress={interpolate(frame, [0, 36], [0, 1], { extrapolateRight: "clamp" })} from={<Specimen variant="normal" />} to={<Specimen variant="xray" />} />;
};

const Demo: React.FC = () => (
  <Paper light={0.8} lightOver={false}>
    <AppShot
      shot={shot("01-board", board)}
      states={[{ at: 118, shot: shot("06-board-first-taken", boardTaken), dur: 8 }]}
      camera={[
        { at: 0, focus: "full" },
        { at: 20, focus: "hero_card", dur: 36 },
        { at: 80, focus: "mark_taken_pa", zoom: 2.2, dur: 30 },
        { at: 150, focus: "toast", dur: 30 },
        { at: 210, focus: "full", dur: 40 },
      ]}
      cursor={[
        { at: 40, to: "hero_title" },
        { at: 86, to: "mark_taken_pa", dur: 26, click: true },
      ]}
      highlights={[
        { from: 150, to: 205, box: "toast", style: "ring" },
        { from: 250, to: 300, box: "teresa_card", style: "dim-others" },
      ]}
    />
    <DemoTag />
  </Paper>
);

const Scroll: React.FC = () => (
  <Paper light={0.8} lightOver={false}>
    <AppShot
      shot={shot("04-case-teresa-requirements", reqs, "full")}
      camera={[
        { at: 0, focus: "full" },
        { at: 15, focus: "req_pa", dur: 40 },
        { at: 70, focus: "citation_row_guide_635", zoom: 2.4, dur: 30 },
      ]}
      highlights={[{ from: 80, to: 130, box: "citation_row_guide_635", style: "underline" }]}
    />
  </Paper>
);

// Every shared component on one timeline, for eyeballing motion and type.
export const Playground: React.FC = () => (
  <AbsoluteFill style={{ background: color.ivory }}>
    <Sequence durationInFrames={90}>
      <Specimen variant="normal" />
    </Sequence>
    <Sequence from={90} durationInFrames={40}>
      <Sweep />
    </Sequence>
    <Sequence from={130} durationInFrames={60}>
      <Specimen variant="xray" />
    </Sequence>
    <Sequence from={190} durationInFrames={120}>
      <Numbers />
    </Sequence>
    <Sequence from={310} durationInFrames={300}>
      <Demo />
    </Sequence>
    <Sequence from={610} durationInFrames={140}>
      <Scroll />
    </Sequence>
    <Sequence from={750} durationInFrames={90}>
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={50}>
          <Numbers />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={xraySweep()} timing={linearTiming({ durationInFrames: 36 })} />
        <TransitionSeries.Sequence durationInFrames={76}>
          <Specimen variant="xray" />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </Sequence>
  </AbsoluteFill>
);
