import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { color, ease, font } from "../../theme";
import { Clock, ToothGlyph } from "./Glyphs";
import { lerp, pop, prog } from "./util";

type Times = {
  at: number; // diagram appears
  send: number; // Teresa's request leaves the clinic
  home: number; // patient has gone home; denial comes back
  back: number; // resubmission drops to the back of the queue
  twice: number; // "reviewed twice"
  money: number; // "public money"
};

// Fills the frame with 120px margins.
const NODE_W = 420;
const CLINIC = { x: 120 + NODE_W / 2, y: 500 };
const REVIEW = { x: 1920 - 120 - NODE_W / 2, y: 500 };
const R = 120; // node circle radius
const QUEUE_X0 = 600; // back of the queue (Teresa's landing slot)
const QUEUE_GAP = 124;
const QUEUE_N = 7;

type Pt = { x: number; y: number };
const quad = (a: Pt, c: Pt, b: Pt, t: number): Pt => ({
  x: (1 - t) ** 2 * a.x + 2 * (1 - t) * t * c.x + t ** 2 * b.x,
  y: (1 - t) ** 2 * a.y + 2 * (1 - t) * t * c.y + t ** 2 * b.y,
});
// Outbound arc over the queue, return arc under it.
const OUT = { a: { x: CLINIC.x + 150, y: CLINIC.y - 130 }, c: { x: 960, y: CLINIC.y - 470 }, b: { x: REVIEW.x - 150, y: CLINIC.y - 130 } };
const RET = { a: { x: REVIEW.x - 150, y: CLINIC.y + 140 }, c: { x: 960, y: CLINIC.y + 470 }, b: { x: QUEUE_X0, y: CLINIC.y + 165 } };
const d = (k: typeof OUT) => `M ${k.a.x} ${k.a.y} Q ${k.c.x} ${k.c.y} ${k.b.x} ${k.b.y}`;

const Node: React.FC<{ x: number; y: number; title: string; sub: string; p: number; children?: React.ReactNode }> = ({ x, y, title, sub, p, children }) => (
  <div style={{ position: "absolute", left: x - NODE_W / 2, top: y - R, width: NODE_W, textAlign: "center", opacity: p, transform: `translateY(${(1 - p) * 20}px)` }}>
    <div style={{ width: R * 2, height: R * 2, margin: "0 auto", borderRadius: 999, background: "#fbfaf4", boxShadow: "0 18px 44px rgba(15,36,29,0.14)", position: "relative", display: "flex", alignItems: "center", justifyContent: "center", overflow: "visible" }}>
      {children}
    </div>
    <div style={{ fontFamily: font.sans, fontWeight: 500, fontSize: 42, color: color.forest, marginTop: 22 }}>{title}</div>
    <div style={{ fontFamily: font.mono, fontSize: 24, letterSpacing: "0.06em", color: color.muted, marginTop: 8 }}>{sub}</div>
  </div>
);

type Tone = "plain" | "teresa" | "denied";
const Card: React.FC<{ x: number; y: number; w: number; tone?: Tone; scale?: number; opacity?: number; label?: string; labelBelow?: boolean }> = ({
  x,
  y,
  w,
  tone = "plain",
  scale = 1,
  opacity = 1,
  label,
  labelBelow,
}) => {
  const h = w * 1.28;
  return (
    <div style={{ position: "absolute", left: x - w / 2, top: y - h / 2, width: w, height: h, opacity, transform: `scale(${scale})` }}>
      <div
        style={{
          width: w,
          height: h,
          borderRadius: w * 0.14,
          background: tone === "plain" ? "#fbfaf4" : tone === "teresa" ? color.forest : color.orange,
          border: tone === "plain" ? "2px solid rgba(25,58,48,0.28)" : "none",
          boxShadow: tone === "plain" ? "0 8px 18px rgba(15,36,29,0.12)" : "0 18px 36px rgba(15,36,29,0.22)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          paddingTop: w * 0.2,
          gap: w * 0.1,
          boxSizing: "border-box",
        }}
      >
        <ToothGlyph size={w * 0.42} stroke={tone === "plain" ? color.forest : color.ivory} width={1.4} />
        <div style={{ width: w * 0.56, height: w * 0.05, borderRadius: 3, background: tone === "plain" ? "rgba(25,58,48,0.2)" : "rgba(244,242,233,0.6)" }} />
        <div style={{ width: w * 0.36, height: w * 0.05, borderRadius: 3, background: tone === "plain" ? "rgba(25,58,48,0.12)" : "rgba(244,242,233,0.4)" }} />
      </div>
      {label && (
        <div
          style={{
            position: "absolute",
            left: "50%",
            transform: "translateX(-50%)",
            ...(labelBelow ? { top: h + 16 } : { bottom: h + 16 }),
            whiteSpace: "nowrap",
            fontFamily: font.mono,
            fontWeight: 500,
            fontSize: 28 / Math.max(scale, 0.72),
            letterSpacing: "0.06em",
            color: tone === "denied" ? color.orange : color.forest,
          }}
        >
          {label}
        </div>
      )}
    </div>
  );
};

// The rework loop: Teresa's request goes out after she has left, comes back denied, and re-enters at the
// back of the queue to be reviewed a second time on public money, while the clinic's clock drains.
export const QueueLoop: React.FC<Times> = ({ at, send, home, back, twice, money }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const show = pop(frame, at, fps, "critical");

  const leave = prog(frame, send + 20, home - send - 20, ease.inOut);
  const out = prog(frame, send, 44, ease.inOut);
  const arrive = send + 44;
  const ret = prog(frame, home - 22, 30, ease.inOut);
  const fixAt = back - 34; // "The fix goes…": a new x-ray, days later
  const drop = prog(frame, back - 16, 22, ease.inOut);
  const convey = (f: number) => interpolate(f, [at, money + 30], [0, 1]) * 40;
  const conveyor = convey(frame);
  const creep = frame >= back + 6 ? conveyor - convey(back + 6) : 0;

  let pos: Pt;
  if (frame < home - 22) pos = quad(OUT.a, OUT.c, OUT.b, out);
  else if (frame < back - 16) pos = quad(RET.a, RET.c, RET.b, ret);
  else {
    const q = { x: QUEUE_X0, y: CLINIC.y };
    pos = { x: lerp(RET.b.x, q.x, drop), y: lerp(RET.b.y, q.y, drop) - Math.sin(Math.PI * drop) * 90 };
  }
  // The request disappears into review, then re-emerges on the return path.
  // Fade back in once clear of the review node's caption.
  const cardO = frame < home - 26 ? 1 - prog(frame, arrive - 4, 8) : prog(frame, home - 12, 8);
  const denied = frame >= home - 8;
  const tone: Tone = denied && frame < fixAt ? "denied" : "teresa";
  const onReturn = frame >= home - 22 && frame < back - 16;
  const cardLabel = frame < home - 26 ? "SENT" : frame < fixAt ? "DENIED · MISSING X-RAY" : frame < back - 16 ? "NEW X-RAY, NEW VISIT" : frame < back + 10 ? "RESUBMITTED" : undefined;
  const cardScale = lerp(1, 0.72, drop);

  const reviews = frame >= twice ? 2 : frame >= arrive ? 1 : 0;
  const bump = frame >= twice ? pop(frame, twice, fps, "overshoot") : pop(frame, arrive, fps, "overshoot");
  const twiceP = pop(frame, twice, fps, "overshoot");
  const moneyP = pop(frame, money, fps, "overshoot");
  const drain = prog(frame, at, money + 20 - at, ease.inOut);

  // Track: a thick dashed path; the stretch already travelled is drawn solid.
  const track = (k: typeof OUT, done: number, hot: boolean) => (
    <>
      <path d={d(k)} fill="none" stroke={hot ? color.orange : color.forest} strokeOpacity={hot ? 0.55 : 0.3} strokeWidth={6} strokeDasharray="16 16" strokeLinecap="round" />
      <path d={d(k)} fill="none" stroke={hot ? color.orange : color.forest} strokeOpacity={hot ? 0.9 : 0.55} strokeWidth={6} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - done} />
    </>
  );
  const arrow = (k: typeof OUT, hot: boolean) => {
    const e = k.b;
    const p2 = quad(k.a, k.c, k.b, 0.96);
    const ang = (Math.atan2(e.y - p2.y, e.x - p2.x) * 180) / Math.PI;
    return <path d="M -18 -13 L 4 0 L -18 13" transform={`translate(${e.x} ${e.y}) rotate(${ang})`} fill="none" stroke={hot ? color.orange : color.forest} strokeOpacity={hot ? 0.9 : 0.5} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round" />;
  };

  return (
    <div style={{ position: "absolute", inset: 0, opacity: show }}>
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        {track(OUT, out, false)}
        {arrow(OUT, false)}
        {track(RET, frame >= home - 22 ? ret : 0, denied)}
        {arrow(RET, denied)}
      </svg>

      <Node x={CLINIC.x} y={CLINIC.y} title="The clinic" sub={leave > 0.9 ? "PATIENT HAS GONE HOME" : "PATIENT IN THE CHAIR"} p={show}>
        <div style={{ width: 84, height: 84, borderRadius: 99, background: color.orange, transform: `translateX(${-leave * 150}px)`, opacity: 1 - leave }} />
        {leave > 0.9 && <div style={{ position: "absolute", width: 84, height: 84, borderRadius: 99, border: `4px dashed rgba(25,58,48,0.3)` }} />}
      </Node>
      <Node x={REVIEW.x} y={REVIEW.y} title="Sun Life review" sub="REVIEWS OF THIS REQUEST" p={show}>
        <div style={{ fontFamily: font.display, fontSize: 170, color: reviews === 2 ? color.orange : color.forest, lineHeight: 1, transform: `scale(${reviews ? 0.85 + 0.15 * bump : 1})` }}>{reviews}</div>
      </Node>

      {/* every clinic's requests, creeping toward review */}
      {Array.from({ length: QUEUE_N }, (_, i) => {
        const x = QUEUE_X0 + (i + 1) * QUEUE_GAP + conveyor;
        return <Card key={i} x={x} y={CLINIC.y} w={84} opacity={interpolate(x, [1370, 1430], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />;
      })}
      <div style={{ position: "absolute", left: QUEUE_X0 + QUEUE_GAP - 42, top: CLINIC.y + 78, fontFamily: font.mono, fontSize: 24, letterSpacing: "0.06em", color: color.muted }}>
        THE QUEUE · EVERY CLINIC'S REQUESTS
      </div>

      {/* Teresa's request */}
      {frame >= send - 4 && (
        <Card x={pos.x + creep} y={pos.y} w={132} tone={tone} label={cardLabel} labelBelow={onReturn} scale={cardScale * pop(frame, send - 4, fps, "snappy")} opacity={cardO} />
      )}

      {/* the clinic's time */}
      <div style={{ position: "absolute", left: 120, top: 96, display: "flex", alignItems: "center", gap: 22, opacity: prog(frame, at + 10, 16) }}>
        <Clock turns={drain * 5} drain={drain} size={124} />
        <div style={{ fontFamily: font.mono, fontSize: 24, letterSpacing: "0.08em", color: color.muted, lineHeight: 1.45 }}>
          THE CLINIC'S
          <br />
          TIME
        </div>
      </div>

      {/* the cost */}
      <div style={{ position: "absolute", left: REVIEW.x - 260, top: REVIEW.y + 250, width: 520, display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
        <div style={{ padding: "18px 40px", borderRadius: 999, background: color.forest, color: color.ivory, fontFamily: font.sans, fontWeight: 500, fontSize: 50, whiteSpace: "nowrap", transform: `scale(${twiceP})`, opacity: twiceP > 0.01 ? 1 : 0 }}>
          Reviewed twice
        </div>
        <div style={{ padding: "18px 40px", borderRadius: 999, background: color.orange, color: color.ink, fontFamily: font.sans, fontWeight: 500, fontSize: 50, whiteSpace: "nowrap", transform: `scale(${moneyP})`, opacity: moneyP > 0.01 ? 1 : 0 }}>
          On public money
        </div>
      </div>
    </div>
  );
};
