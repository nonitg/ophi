import React from "react";
import { Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { Box } from "../AppShot";
import { color, font, springs } from "../../theme";
import { STAGE } from "./Overlays";

// Sun Life's decision coming back, told as a motion piece: the letter, Ophi's letter reader naming the
// reason, then the two next steps. Self-contained so a real capture of the app reading a letter can
// replace it later. The letter text is the fake EOB note from the ABELDent lab (capture 33).
const LETTER = "Predetermination not approved. A current periapical radiograph of tooth 24 was not received. Resubmit with the radiograph.";
const KEY = [3, 13]; // word range [from, to) of the reason phrase: "A current periapical … not received."

// The 16 reasons Laya's decision head chooses from (ophi/outcomes/laya_questions.REASON_KEYS), in the
// app's plain words (ophi/outcomes/past_view.REASONS).
const REASONS = [
  "Missing X-ray",
  "X-ray over 12 months old",
  "No full perio chart",
  "Note didn't describe the damage",
  "Crowned in the last 8 years",
  "Patient under 18",
  "Wisdom tooth, molars still in place",
  "Sent twice",
  "Retired lab fee code",
  "Fillings or cleaning still to do",
  "Tooth not broken down enough",
  "Root canal not healed yet",
  "Weak gum or bone support",
  "Too little tooth above the gum",
  "Crack, sensitivity or looks only",
  "Crown criteria not met",
];
const PICK = 0;
// Where the selector hops before it lands, like a classifier weighing options.
const HOPS = [10, 5, 3, 1, PICK];

const out = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export type DecisionCues = { arrive: number; read: number; reason: number; book: number; expires: number; or: number; fix: number; resubmit: number };

export const DecisionBeat: React.FC<{ cue: DecisionCues }> = ({ cue }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const x0 = STAGE.x;
  const y0 = STAGE.y;

  // Phase A: letter + reader. Exits as the next steps come in.
  // Phase A holds until the approved step comes in; the reason card stays and moves up beside the steps.
  const aOut = interpolate(f, [cue.book - 18, cue.book - 2], [0, 1], { ...clamp, easing: Easing.bezier(0.65, 0, 0.35, 1) });
  const drop = spring({ frame: f - cue.arrive, fps, config: { damping: 16, stiffness: 120, mass: 0.9 } });
  const scan = interpolate(f, [cue.read, cue.read + 30], [0, 1], { ...clamp, easing: Easing.bezier(0.45, 0, 0.55, 1) });
  const mark = interpolate(f, [cue.reason - 4, cue.reason + 12], [0, 1], { ...clamp, easing: out });
  const words = LETTER.split(" ");
  const L = { x: x0 + 70, y: y0 + 60, w: 800, h: 680 };

  // The reasons grid, right of the letter.
  const G = { x: x0 + 960, y: y0 + 96, cw: 206, ch: 78, gap: 12 };
  const hopDur = Math.max(2, Math.floor((cue.reason - (cue.read + 18)) / HOPS.length));
  const hopI = Math.min(HOPS.length - 1, Math.max(0, Math.floor((f - (cue.read + 18)) / hopDur)));
  const selecting = f >= cue.read + 18;
  const landed = f >= cue.read + 18 + hopDur * (HOPS.length - 1);
  const land = spring({ frame: f - (cue.read + 18 + hopDur * (HOPS.length - 1)), fps, config: springs.overshoot });
  const pick = { x: G.x + (PICK % 4) * (G.cw + G.gap), y: G.y + Math.floor(PICK / 4) * (G.ch + G.gap) };
  const wire = interpolate(f, [cue.reason + 4, cue.reason + 20], [0, 1], { ...clamp, easing: out });
  const rule = spring({ frame: f - (cue.reason + 12), fps, config: springs.snappy });

  // Phase B: the two next steps.
  const pA = spring({ frame: f - (cue.book - 8), fps, config: springs.critical });
  const pB = spring({ frame: f - (cue.or - 4), fps, config: springs.critical });

  return (
    <div style={{ position: "absolute", inset: 0 }}>
      {aOut < 1 && (
        <div style={{ position: "absolute", inset: 0, opacity: 1 - aOut, transform: `translateY(${-60 * aOut}px) scale(${1 - 0.04 * aOut})` }}>
          {/* The letter */}
          <div
            style={{
              position: "absolute",
              left: L.x,
              top: L.y,
              width: L.w,
              height: L.h,
              transform: `translateY(${(1 - drop) * -700}px) rotate(${(1 - drop) * -6 - 1.2}deg)`,
              background: "#fffdf8",
              borderRadius: 8,
              boxShadow: "0 2px 4px rgba(15,36,29,0.1), 0 30px 70px rgba(15,36,29,0.22)",
              padding: "46px 56px",
              boxSizing: "border-box",
              overflow: "hidden",
            }}
          >
            <div style={{ fontFamily: font.mono, fontSize: 18, letterSpacing: "0.14em", color: color.muted }}>PREDETERMINATION RESPONSE · CDCP</div>
            <div style={{ fontFamily: font.sans, fontWeight: 500, fontSize: 34, color: color.ink, marginTop: 18 }}>Crown 27211 · tooth 24</div>
            <div style={{ fontFamily: font.sans, fontSize: 22, color: color.muted, marginTop: 8 }}>Decision dated Sep 17, 2026</div>
            <div style={{ height: 1, background: "rgba(25,58,48,0.18)", margin: "30px 0 28px" }} />
            <div style={{ fontFamily: font.mono, fontSize: 17, letterSpacing: "0.12em", color: color.muted, marginBottom: 14 }}>MESSAGE</div>
            <div style={{ position: "relative", fontFamily: font.display, fontSize: 44, lineHeight: 1.32, color: color.ink }}>
              {words.map((w, i) => {
                const seen = scan >= (i + 1) / words.length || scan >= 1;
                const key = i >= KEY[0] && i < KEY[1];
                const hl = key ? Math.max(0, Math.min(1, mark * (KEY[1] - KEY[0]) - (i - KEY[0]))) : 0;
                return (
                  <span key={i} style={{ position: "relative", opacity: f < cue.read ? 0.55 : seen ? 1 : 0.55 }}>
                    {key && (
                      <span
                        style={{
                          position: "absolute",
                          left: -3,
                          right: -3,
                          top: "18%",
                          bottom: "4%",
                          background: color.orangeSoft,
                          transformOrigin: "0 50%",
                          transform: `scaleX(${hl})`,
                          borderRadius: 4,
                          zIndex: -1,
                        }}
                      />
                    )}
                    {w}{" "}
                  </span>
                );
              })}
              {/* Reader scan beam */}
              {f >= cue.read && scan < 1 && (
                <div
                  style={{
                    position: "absolute",
                    left: -56,
                    right: -56,
                    top: `${scan * 100}%`,
                    height: 3,
                    background: color.orange,
                    boxShadow: "0 0 18px 6px rgba(239,134,91,0.45)",
                  }}
                />
              )}
            </div>
            <div style={{ position: "absolute", left: 56, bottom: 36, fontFamily: font.mono, fontSize: 16, color: color.muted, letterSpacing: "0.08em" }}>
              SAMPLE LETTER · FICTIONAL PATIENT
            </div>
          </div>

          {/* The reason set */}
          {f >= cue.read + 6 && (
            <div style={{ position: "absolute", left: G.x, top: G.y - 50, fontFamily: font.mono, fontSize: 19, letterSpacing: "0.12em", color: color.forestSoft, opacity: interpolate(f, [cue.read + 6, cue.read + 16], [0, 1], clamp) }}>
              THE 16 REASONS SUN LIFE CAN GIVE
            </div>
          )}
          {REASONS.map((r, i) => {
            const at = cue.read + 6 + i * 1.2;
            const s = spring({ frame: f - at, fps, config: springs.snappy });
            if (f < at) return null;
            const cx = G.x + (i % 4) * (G.cw + G.gap);
            const cy = G.y + Math.floor(i / 4) * (G.ch + G.gap);
            const chosen = landed && i === PICK;
            const dim = landed && i !== PICK;
            return (
              <div
                key={r}
                style={{
                  position: "absolute",
                  left: cx,
                  top: cy,
                  width: G.cw,
                  height: G.ch,
                  boxSizing: "border-box",
                  padding: "0 14px",
                  display: "flex",
                  alignItems: "center",
                  borderRadius: 12,
                  background: chosen ? color.orange : "#faf9f4",
                  color: chosen ? color.ink : color.forest,
                  border: `1.5px solid ${chosen ? color.orange : "rgba(25,58,48,0.16)"}`,
                  boxShadow: chosen ? "0 12px 30px rgba(239,134,91,0.45)" : "0 2px 6px rgba(15,36,29,0.08)",
                  fontFamily: font.sans,
                  fontWeight: chosen ? 700 : 500,
                  fontSize: 19,
                  lineHeight: 1.18,
                  opacity: s * (dim ? 0.42 : 1),
                  transform: `scale(${(0.9 + 0.1 * s) * (chosen ? 1 + 0.08 * land : 1)})`,
                }}
              >
                {r}
              </div>
            );
          })}

          {/* Selector: glides between candidates, like a classifier weighing them, then settles on one */}
          {selecting && !landed && (() => {
            const t = Math.min(1, ((f - (cue.read + 18)) % hopDur) / hopDur);
            const from = HOPS[Math.max(0, hopI - 1)];
            const to = HOPS[hopI];
            const e = Easing.bezier(0.45, 0, 0.3, 1)(hopI === 0 ? 1 : t);
            const cx = (k: number) => G.x + (k % 4) * (G.cw + G.gap);
            const cy = (k: number) => G.y + Math.floor(k / 4) * (G.ch + G.gap);
            return (
              <div
                style={{
                  position: "absolute",
                  left: cx(from) + (cx(to) - cx(from)) * e - 5,
                  top: cy(from) + (cy(to) - cy(from)) * e - 5,
                  width: G.cw + 10,
                  height: G.ch + 10,
                  borderRadius: 15,
                  border: `3px solid ${color.orange}`,
                  boxShadow: "0 0 20px rgba(239,134,91,0.4)",
                }}
              />
            );
          })()}

          {/* Phrase → reason wire */}
          {wire > 0 && (
            <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
              <path
                d={`M ${L.x + L.w - 20} ${L.y + 420} C ${L.x + L.w + 60} ${L.y + 420}, ${pick.x - 60} ${pick.y + G.ch / 2}, ${pick.x - 6} ${pick.y + G.ch / 2}`}
                fill="none"
                stroke={color.orange}
                strokeWidth={4}
                strokeLinecap="round"
                pathLength={1}
                strokeDasharray={1}
                strokeDashoffset={1 - wire}
              />
              <circle cx={L.x + L.w - 20} cy={L.y + 420} r={7} fill={color.orange} opacity={wire} />
            </svg>
          )}

        </div>
      )}

      {/* Reason → the rule it points to */}
      {f >= cue.reason + 12 && (
        <div
          style={{
            position: "absolute",
            left: G.x,
            top: G.y + (4 * (G.ch + G.gap) + 22) * (1 - aOut),
            width: 4 * G.cw + 3 * G.gap,
            opacity: rule,
            transform: `translateY(${(1 - rule) * 20}px)`,
            boxSizing: "border-box",
            padding: "18px 22px",
            borderRadius: 16,
            background: color.film,
            boxShadow: "0 14px 36px rgba(15,36,29,0.28)",
          }}
        >
          <div style={{ fontFamily: font.mono, fontSize: 18, letterSpacing: "0.12em", color: color.orange }}>SUN LIFE'S REASON · MISSING X-RAY</div>
          <div style={{ fontFamily: font.sans, fontSize: 24, color: color.bone, marginTop: 8, lineHeight: 1.3 }}>
            Required by <b style={{ fontWeight: 700 }}>Matrix</b> Restorative services — PA+BW (R&amp;L) ≤ 12 mo
          </div>
        </div>
      )}

      {/* Phase B: approved → book it; denied → fix and resubmit */}
      {f >= cue.book - 8 && (
        <Step
          p={pA}
          x={x0 + 40}
          y={y0 + 34}
          w={900}
          kicker="IF SUN LIFE APPROVES"
          dot="#3f8f5f"
          src="app-v2/16-book-the-crown.png"
          box={{ x: 28, y: 331, w: 700, h: 258 }}
          ring={{ box: { x: 46, y: 387, w: 490, h: 32 }, from: cue.expires - 6 }}
        />
      )}
      {f >= cue.or - 4 && (
        <Step
          p={pB}
          x={x0 + 40}
          y={y0 + 440}
          w={900}
          kicker="IF SUN LIFE DENIES"
          dot="#c2412d"
          src="app-v2/33-rec-denied-eob.png"
          box={{ x: 28, y: 331, w: 712, h: 158 }}
          fade
          ring={{ box: { x: 46, y: 388, w: 684, h: 54 }, from: cue.fix - 4 }}
          tag={{ from: cue.fix - 2, text: "Fix: take the periapical, resend" }}
        />
      )}
    </div>
  );
};

// One next-step panel: a crop of the real case page at readable scale, a ring on the line that matters.
const Step: React.FC<{
  p: number;
  x: number;
  y: number;
  w: number;
  kicker: string;
  dot: string;
  src: string;
  box: Box;
  fade?: boolean;
  ring: { box: Box; from: number };
  tag?: { from: number; text: string };
}> = ({ p, x, y, w, kicker, dot, src, box, fade, ring, tag }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = w / box.w;
  const h = box.h * s;
  const r = interpolate(f, [ring.from, ring.from + 12], [0, 1], { ...clamp, easing: out });
  const t = tag ? spring({ frame: f - tag.from, fps, config: springs.snappy }) : 0;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: w, opacity: p, transform: `translateY(${(1 - p) * 60}px)` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, fontFamily: font.mono, fontSize: 20, letterSpacing: "0.12em", color: color.forest, marginBottom: 16 }}>
        <span style={{ width: 12, height: 12, borderRadius: 6, background: dot }} />
        {kicker}
      </div>
      <div
        style={{
          position: "relative",
          width: w,
          height: h,
          overflow: "hidden",
          borderRadius: 18,
          boxShadow: "0 2px 4px rgba(15,36,29,0.08), 0 24px 60px rgba(15,36,29,0.18)",
          WebkitMaskImage: fade ? "linear-gradient(to bottom, #000 78%, transparent 100%)" : undefined,
        }}
      >
        <Img src={staticFile(src)} style={{ position: "absolute", left: -box.x * s, top: -box.y * s, width: 1440 * s }} />
        {r > 0 && (
          <div
            style={{
              position: "absolute",
              left: (ring.box.x - box.x) * s - 6,
              top: (ring.box.y - box.y) * s - 6,
              width: ring.box.w * s + 12,
              height: ring.box.h * s + 12,
              borderRadius: 10,
              border: `3.5px solid ${color.orange}`,
              boxShadow: "0 0 0 6px rgba(239,134,91,0.18), 0 0 30px rgba(239,134,91,0.35)",
              opacity: r,
              transform: `scale(${1 + (1 - r) * 0.05})`,
            }}
          />
        )}
      </div>
      {tag && f >= tag.from && (
        <div
          style={{
            position: "absolute",
            left: w + 40,
            top: 40 + h / 2 - 34,
            whiteSpace: "nowrap",
            display: "inline-flex",
            alignItems: "center",
            gap: 12,
            padding: "14px 22px",
            borderRadius: 14,
            background: color.orange,
            color: color.ink,
            fontFamily: font.sans,
            fontWeight: 500,
            fontSize: 26,
            opacity: t,
            transform: `translateX(${(1 - t) * -24}px)`,
          }}
        >
          {tag.text}
        </div>
      )}
    </div>
  );
};
