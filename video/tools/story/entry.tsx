// Preview entry for the story scenes only (cold, patient, problem), so they render while other scenes are mid-build.
import React from "react";
import { Composition, registerRoot } from "remotion";
import { Cold } from "../../src/scenes/Cold";
import { Patient } from "../../src/scenes/Patient";
import { Problem } from "../../src/scenes/Problem";
import { FPS, HEIGHT, WIDTH } from "../../src/theme";
import { voSeconds } from "../../src/vo";

const f = (id: string) => Math.round(voSeconds(id) * FPS);
const Root: React.FC = () => (
  <>
    <Composition id="Story-cold" component={Cold} durationInFrames={f("cold")} fps={FPS} width={WIDTH} height={HEIGHT} />
    <Composition id="Story-patient" component={Patient} durationInFrames={f("patient")} fps={FPS} width={WIDTH} height={HEIGHT} />
    <Composition id="Story-problem" component={Problem} durationInFrames={f("problem")} fps={FPS} width={WIDTH} height={HEIGHT} />
  </>
);
registerRoot(Root);
