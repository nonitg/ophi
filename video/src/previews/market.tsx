// Preview entry for the Value and Market scenes only, so they render while other scenes are mid-build.
import React from "react";
import { Composition, registerRoot } from "remotion";
import { Value } from "../scenes/Value";
import { Market } from "../scenes/Market";
import { framesOf, section } from "../timeline";
import { FPS, HEIGHT, WIDTH } from "../theme";

const Root: React.FC = () => (
  <>
    <Composition id="Scene-value" component={Value} durationInFrames={framesOf(section("value"))} fps={FPS} width={WIDTH} height={HEIGHT} />
    <Composition id="Scene-market" component={Market} durationInFrames={framesOf(section("market"))} fps={FPS} width={WIDTH} height={HEIGHT} />
  </>
);
registerRoot(Root);
