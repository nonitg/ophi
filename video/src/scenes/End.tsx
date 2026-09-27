import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Paper, Wordmark } from "../components";
import { Sfx } from "../audio";
import { color, font, springs } from "../theme";
import { lerp, ramp } from "../components/vision/util";

// Teresa's case closes (the goal was her crown), then the wordmark and who built it.
export const End: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const card = spring({ frame: frame - 2, fps, config: springs.critical });
  const stampAt = 16;
  const stamp = spring({ frame: frame - stampAt, fps, config: { damping: 14, stiffness: 260, mass: 0.6 } });
  const shake = frame >= stampAt && frame < stampAt + 6 ? Math.sin((frame - stampAt) * 2.4) * (6 - (frame - stampAt)) * 0.8 : 0;
  const info = (i: number) => ramp(frame, 44 + i * 6, 60 + i * 6);
  const fromBlack = 1 - ramp(frame, 0, 8);

  return (
    <Paper drift={-40}>
      <AbsoluteFill>
        {/* Teresa's card with the stamp */}
        <div
          style={{
            position: "absolute",
            left: 250,
            top: 372,
            width: 620,
            padding: "36px 40px",
            borderRadius: 14,
            background: "#fbfaf4",
            boxShadow: "0 24px 60px rgba(35,42,46,0.16), 0 2px 6px rgba(35,42,46,0.08)",
            transform: `translate(${shake}px, ${(1 - card) * -60}px) rotate(${lerp(-8, -3, card)}deg)`,
            opacity: card,
          }}
        >
          <div style={{ fontFamily: font.mono, fontSize: 18, letterSpacing: "0.12em", color: color.muted }}>CDCP PREAUTHORIZATION</div>
          <div style={{ fontFamily: font.display, fontSize: 64, color: color.forest, marginTop: 10, lineHeight: 1.05 }}>Teresa, 64</div>
          <div style={{ fontFamily: font.sans, fontSize: 26, color: color.muted, marginTop: 8 }}>Crown on #46 · fictional patient</div>
          <div style={{ marginTop: 26, height: 1, background: "rgba(25,58,48,0.14)" }} />
          <div style={{ fontFamily: font.sans, fontSize: 22, color: color.forest, marginTop: 18 }}>Oct 15 · Op 2</div>
          {frame >= stampAt && (
            <div
              style={{
                position: "absolute",
                right: 26,
                bottom: 22,
                padding: "10px 22px",
                border: `5px solid ${color.orange}`,
                borderRadius: 10,
                color: color.orange,
                fontFamily: font.mono,
                fontWeight: 500,
                fontSize: 34,
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                transform: `rotate(-7deg) scale(${lerp(1.8, 1, stamp)})`,
                transformOrigin: "70% 60%",
                opacity: Math.min(1, stamp * 1.4) * 0.92,
                mixBlendMode: "multiply",
              }}
            >
              Crown booked
            </div>
          )}
        </div>

        {/* wordmark and credits */}
        <div style={{ position: "absolute", left: 1010, top: 352 }}>
          <Wordmark start={32} size={210} />
          <div style={{ fontFamily: font.mono, fontSize: 32, color: color.orange, marginTop: 18, opacity: info(0), transform: `translateY(${(1 - info(0)) * 12}px)` }}>ophi.app</div>
          <div style={{ fontFamily: font.sans, fontSize: 30, color: color.forest, marginTop: 26, opacity: info(1), transform: `translateY(${(1 - info(1)) * 12}px)` }}>
            Nonit Gupta · Jinay Patel
          </div>
          <div style={{ fontFamily: font.sans, fontSize: 24, color: color.muted, marginTop: 10, opacity: info(2), transform: `translateY(${(1 - info(2)) * 12}px)` }}>
            AF Hacks: Growing Canada 2026
          </div>
        </div>

        <div style={{ position: "absolute", left: 0, right: 0, bottom: 40, textAlign: "center", opacity: info(3), fontFamily: font.sans, fontSize: 17, color: color.muted }}>
          Demo data is fictional. Model results so far are from simulated data. Sources on screen.
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "#000", opacity: fromBlack }} />
      <Sfx name="paper-slide" at={2} volume={0.35} />
      <Sfx name="stamp" at={stampAt - 1} volume={0.6} />
    </Paper>
  );
};
