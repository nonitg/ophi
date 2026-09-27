import React from "react";
import { Composition, Series } from "remotion";
import { scenes } from "./scenes";
import { Playground, PLAYGROUND_FRAMES } from "./Playground";
import { framesOf, sections, totalFrames } from "./timeline";
import { FPS, HEIGHT, WIDTH } from "./theme";
import { MusicBed } from "./audio";

const Pitch: React.FC = () => (
  <>
  <MusicBed />
  <Series>
    {sections.map((s) => {
      const Scene = scenes[s.id];
      return (
        <Series.Sequence key={s.id} durationInFrames={framesOf(s)} name={s.title}>
          <Scene />
        </Series.Sequence>
      );
    })}
  </Series>
  </>
);

export const Root: React.FC = () => (
  <>
    <Composition id="Pitch" component={Pitch} durationInFrames={totalFrames} fps={FPS} width={WIDTH} height={HEIGHT} />
    {sections.map((s) => (
      <Composition key={s.id} id={`Scene-${s.id}`} component={scenes[s.id]} durationInFrames={framesOf(s)} fps={FPS} width={WIDTH} height={HEIGHT} />
    ))}
    <Composition id="Scene-Playground" component={Playground} durationInFrames={PLAYGROUND_FRAMES} fps={FPS} width={WIDTH} height={HEIGHT} />
  </>
);
