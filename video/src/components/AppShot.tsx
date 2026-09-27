import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, useCurrentFrame } from "remotion";
import { color, font } from "../theme";

// Capture sidecar written by scripts/video-capture.py: boxes are CSS px of a 1440×900 viewport, the PNG is 2x.
export type Box = { x: number; y: number; w: number; h: number };
export type ShotMeta = {
  url?: string;
  scrollY?: number;
  viewport: { w: number; h: number };
  boxes: Record<string, Box>;
  click?: Box;
  full?: { height: number; boxes: Record<string, Box>; click?: Box };
};
export type Shot = { src: string; meta: ShotMeta; mode?: "viewport" | "full" };

// Camera move: starting at frame `at`, glide to `focus` over `dur` frames, then hold.
// focus: a box name from the active shot, an explicit page-space Box, or "full" (whole window).
export type CameraKey = { at: number; focus: string | Box | "full"; zoom?: number; pad?: number; dur?: number; scroll?: number };
// Cursor move: from `at`, glide to the centre of `to` over `dur` frames; `click` ripples on arrival.
export type CursorKey = { at: number; to: string | { x: number; y: number }; dur?: number; click?: boolean };
export type HighlightKey = { from: number; to: number; box: string | Box; style: "ring" | "dim-others" | "underline"; color?: string; radius?: number };
// State change: cross-fade to another capture of the same screen (e.g. a toast appears); camera continues.
export type ShotState = { at: number; shot: Shot; dur?: number };

type Props = {
  shot: Shot;
  states?: ShotState[];
  camera?: CameraKey[];
  cursor?: CursorKey[];
  highlights?: HighlightKey[];
  url?: string;
  chrome?: boolean;
  // When zoomed past the window, keep the view inside it instead of showing the desk.
  clampToWindow?: boolean;
};

const SCREEN_W = 1920;
const SCREEN_H = 1080;
const BAR = 34;
const MAX_ZOOM = 2.6;
const camEase = Easing.bezier(0.45, 0, 0.12, 1); // slow start, long settle: reads as a damped camera

type Cam = { px: number; py: number; zoom: number; scroll: number };

const boxesOf = (s: Shot) => (s.mode === "full" && s.meta.full ? s.meta.full.boxes : s.meta.boxes);
const pageH = (s: Shot) => (s.mode === "full" && s.meta.full ? s.meta.full.height : s.meta.viewport.h);
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

export const AppShot: React.FC<Props> = ({
  shot,
  states = [],
  camera = [{ at: 0, focus: "full" }],
  cursor = [],
  highlights = [],
  url = "ophi.app",
  chrome = true,
  clampToWindow = true,
}) => {
  const frame = useCurrentFrame();
  const vw = shot.meta.viewport.w;
  const vh = shot.meta.viewport.h;
  // Window content scale so the whole window (bar + viewport) fits the frame with a margin at zoom 1.
  const cs = (SCREEN_H - 2 * 56 - BAR) / vh;
  const winW = vw * cs;
  const winH = vh * cs + (chrome ? BAR : 0);
  const winX = (SCREEN_W - winW) / 2;
  const winY = (SCREEN_H - winH) / 2;
  const contentY = winY + (chrome ? BAR : 0);

  const shots = [{ at: -Infinity, shot, dur: 0 }, ...states].sort((a, b) => a.at - b.at);
  const activeAt = (f: number) => shots.filter((s) => s.at <= f).pop()!.shot;
  const findBox = (name: string, f: number): Box => {
    const b = boxesOf(activeAt(f))[name] ?? shots.map((s) => boxesOf(s.shot)[name]).find(Boolean);
    if (!b) throw new Error(`AppShot: no box named "${name}"`);
    return b;
  };
  const resolveBox = (b: string | Box, f: number) => (typeof b === "string" ? findBox(b, f) : b);

  // Keep a zoomed view inside the window (like a screen-recording zoom). Clamping the keyframe targets,
  // not the interpolated camera, keeps every move a smooth ease with no stop against an edge.
  const clampCam = (c: Cam): Cam => {
    if (!clampToWindow) return c;
    const barP = (chrome ? BAR : 0) / cs;
    const halfW = SCREEN_W / 2 / c.zoom / cs;
    const halfH = SCREEN_H / 2 / c.zoom / cs;
    const top = c.scroll - barP;
    const bottom = c.scroll + vh;
    const px = vw <= halfW * 2 ? vw / 2 : Math.min(vw - halfW, Math.max(halfW, c.px));
    const py = bottom - top <= halfH * 2 ? (top + bottom) / 2 : Math.min(bottom - halfH, Math.max(top + halfH, c.py));
    return { ...c, px, py };
  };

  const target = (k: CameraKey): Cam => clampCam(rawTarget(k));
  const rawTarget = (k: CameraKey): Cam => {
    const s = activeAt(k.at);
    const maxScroll = Math.max(0, pageH(s) - vh);
    if (k.focus === "full") {
      const scroll = Math.min(maxScroll, Math.max(0, k.scroll ?? 0));
      return { px: vw / 2, py: scroll + vh / 2, zoom: k.zoom ?? 1, scroll };
    }
    const b = resolveBox(k.focus, k.at);
    const pad = k.pad ?? 48;
    const scroll = k.scroll ?? Math.min(maxScroll, Math.max(0, b.y + b.h / 2 - vh / 2));
    const fit = Math.min((SCREEN_W * 0.86) / ((b.w + pad * 2) * cs), (SCREEN_H * 0.8) / ((b.h + pad * 2) * cs));
    return { px: b.x + b.w / 2, py: b.y + b.h / 2, zoom: k.zoom ?? Math.max(1, Math.min(MAX_ZOOM, fit)), scroll };
  };

  const keys = [...camera].sort((a, b) => a.at - b.at);
  const camAt = (f: number, upto: number): Cam => {
    let c = target(keys[0]);
    for (let i = 1; i <= upto; i++) {
      if (f < keys[i].at) break;
      const start = camAt(keys[i].at, i - 1);
      const t = camEase(Math.min(1, (f - keys[i].at) / (keys[i].dur ?? 30)));
      const end = target(keys[i]);
      // Zoom interpolates in log space so a 1→2.4 push feels even, not front-loaded.
      c = {
        px: lerp(start.px, end.px, t),
        py: lerp(start.py, end.py, t),
        scroll: lerp(start.scroll, end.scroll, t),
        zoom: Math.exp(lerp(Math.log(start.zoom), Math.log(end.zoom), t)),
      };
    }
    return c;
  };
  const cam = camAt(frame, keys.length - 1);

  // Page point → world point (window on the desk at zoom 1) → screen point.
  const toWorld = (x: number, y: number) => ({ x: winX + x * cs, y: contentY + (y - cam.scroll) * cs });
  const focusW = toWorld(cam.px, cam.py);
  const toScreen = (x: number, y: number) => {
    const w = toWorld(x, y);
    return { x: (w.x - focusW.x) * cam.zoom + SCREEN_W / 2, y: (w.y - focusW.y) * cam.zoom + SCREEN_H / 2 };
  };
  const screenBox = (b: Box) => {
    const a = toScreen(b.x, b.y);
    return { x: a.x, y: a.y, w: b.w * cs * cam.zoom, h: b.h * cs * cam.zoom };
  };

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: SCREEN_W,
          height: SCREEN_H,
          transformOrigin: "0 0",
          transform: `translate(${SCREEN_W / 2}px, ${SCREEN_H / 2}px) scale(${cam.zoom}) translate(${-focusW.x}px, ${-focusW.y}px)`,
        }}
      >
        <Window x={winX} y={winY} w={winW} h={winH} chrome={chrome} url={url}>
          <div style={{ position: "absolute", left: 0, top: 0, width: winW, transform: `translateY(${-cam.scroll * cs}px)` }}>
            {shots.map((s, i) => {
              const o = i === 0 ? 1 : interpolate(frame, [s.at, s.at + (s.dur ?? 10)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
              if (o <= 0) return null;
              return <Img key={i} src={s.shot.src} style={{ position: "absolute", left: 0, top: 0, width: winW, height: pageH(s.shot) * cs, opacity: o }} />;
            })}
          </div>
        </Window>
      </div>
      {highlights.map((h, i) => (
        <Highlight key={i} h={h} frame={frame} rect={screenBox(resolveBox(h.box, h.from))} zoom={cam.zoom} />
      ))}
      <Cursor keys={cursor} frame={frame} resolve={(t, f) => (typeof t === "string" ? centre(findBox(t, f)) : t)} toScreen={toScreen} zoom={cam.zoom} />
    </AbsoluteFill>
  );
};

const centre = (b: Box) => ({ x: b.x + b.w / 2, y: b.y + b.h / 2 });

const Window: React.FC<{ x: number; y: number; w: number; h: number; chrome: boolean; url: string; children: React.ReactNode }> = ({ x, y, w, h, chrome, url, children }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      width: w,
      height: h,
      borderRadius: 14,
      overflow: "hidden",
      background: "#fff",
      boxShadow: "0 2px 4px rgba(15,36,29,0.08), 0 24px 60px rgba(15,36,29,0.20), 0 60px 120px rgba(15,36,29,0.14)",
      outline: "1px solid rgba(25,58,48,0.12)",
    }}
  >
    {chrome && (
      <div style={{ position: "absolute", left: 0, top: 0, right: 0, height: BAR, background: "#eeece3", borderBottom: "1px solid rgba(25,58,48,0.10)", display: "flex", alignItems: "center" }}>
        <div style={{ display: "flex", gap: 8, marginLeft: 16 }}>
          {["#e0877a", "#e7c07a", "#8fbf8a"].map((c) => (
            <div key={c} style={{ width: 12, height: 12, borderRadius: 6, background: c, opacity: 0.9 }} />
          ))}
        </div>
        <div
          style={{
            position: "absolute",
            left: "50%",
            transform: "translateX(-50%)",
            height: 22,
            padding: "0 18px",
            borderRadius: 11,
            background: "rgba(25,58,48,0.07)",
            fontFamily: font.sans,
            fontSize: 13,
            lineHeight: "22px",
            color: color.muted,
          }}
        >
          {url}
        </div>
      </div>
    )}
    <div style={{ position: "absolute", left: 0, right: 0, top: chrome ? BAR : 0, bottom: 0, overflow: "hidden" }}>{children}</div>
  </div>
);

const Highlight: React.FC<{ h: HighlightKey; frame: number; rect: Box; zoom: number }> = ({ h, frame, rect, zoom }) => {
  if (frame < h.from - 1 || frame > h.to + 12) return null;
  const inP = interpolate(frame, [h.from, h.from + 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const outP = interpolate(frame, [h.to, h.to + 12], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const o = Math.min(inP, outP);
  const c = h.color ?? color.orange;
  const r = (h.radius ?? 8) * zoom;
  const pad = 6 * zoom;
  const x = rect.x - pad;
  const y = rect.y - pad;
  const w = rect.w + pad * 2;
  const hh = rect.h + pad * 2;
  if (h.style === "dim-others") {
    return (
      <div
        style={{
          position: "absolute",
          left: x,
          top: y,
          width: w,
          height: hh,
          borderRadius: r,
          boxShadow: `0 0 0 4000px rgba(15,36,29,${0.55 * o})`,
          outline: `${2 * o}px solid rgba(239,134,91,${0.9 * o})`,
        }}
      />
    );
  }
  if (h.style === "underline") {
    return <div style={{ position: "absolute", left: rect.x, top: rect.y + rect.h + 4 * zoom, width: rect.w * inP, height: 4 * zoom, borderRadius: 2 * zoom, background: c, opacity: outP }} />;
  }
  const s = 1 + (1 - inP) * 0.06;
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: w,
        height: hh,
        borderRadius: r,
        opacity: o,
        transform: `scale(${s})`,
        border: `${3.5 * Math.sqrt(zoom)}px solid ${c}`,
        boxShadow: `0 0 0 ${6 * Math.sqrt(zoom)}px rgba(239,134,91,0.18), 0 0 30px rgba(239,134,91,0.35)`,
      }}
    />
  );
};

const Cursor: React.FC<{
  keys: CursorKey[];
  frame: number;
  resolve: (t: CursorKey["to"], f: number) => { x: number; y: number };
  toScreen: (x: number, y: number) => { x: number; y: number };
  zoom: number;
}> = ({ keys, frame, resolve, toScreen, zoom }) => {
  if (keys.length === 0 || frame < keys[0].at) return null;
  const ks = [...keys].sort((a, b) => a.at - b.at);
  let p = resolve(ks[0].to, ks[0].at);
  let clickAt: number | null = ks[0].click ? ks[0].at : null;
  for (let i = 1; i < ks.length; i++) {
    const k = ks[i];
    if (frame < k.at) break;
    const from = p;
    const to = resolve(k.to, k.at);
    const dur = k.dur ?? 22;
    const t = Easing.bezier(0.5, 0, 0.2, 1)(Math.min(1, (frame - k.at) / dur));
    // Slight arc, like a hand moving a mouse.
    const mx = (from.x + to.x) / 2 - (to.y - from.y) * 0.12;
    const my = (from.y + to.y) / 2 + (to.x - from.x) * 0.12;
    p = {
      x: (1 - t) * (1 - t) * from.x + 2 * (1 - t) * t * mx + t * t * to.x,
      y: (1 - t) * (1 - t) * from.y + 2 * (1 - t) * t * my + t * t * to.y,
    };
    if (k.click) clickAt = k.at + dur;
  }
  const s = toScreen(p.x, p.y);
  const appear = interpolate(frame, [ks[0].at, ks[0].at + 8], [0, 1], { extrapolateRight: "clamp" });
  const since = clickAt === null ? Infinity : frame - clickAt;
  const press = since >= 0 && since < 8 ? 1 - Math.sin((since / 8) * Math.PI) * 0.18 : 1;
  const size = 30 * Math.min(1.8, Math.sqrt(zoom));
  return (
    <>
      {since >= 0 && since < 22 && (
        <div
          style={{
            position: "absolute",
            left: s.x,
            top: s.y,
            width: 0,
            height: 0,
          }}
        >
          <div
            style={{
              position: "absolute",
              left: -(10 + since * 3.2),
              top: -(10 + since * 3.2),
              width: 2 * (10 + since * 3.2),
              height: 2 * (10 + since * 3.2),
              borderRadius: "50%",
              border: `3px solid rgba(239,134,91,${1 - since / 22})`,
              background: `rgba(239,134,91,${0.18 * (1 - since / 22)})`,
            }}
          />
        </div>
      )}
      <svg
        width={size}
        height={size * 1.4}
        viewBox="0 0 20 28"
        style={{ position: "absolute", left: s.x - size * 0.12, top: s.y - size * 0.05, opacity: appear, transform: `scale(${press})`, transformOrigin: "10% 5%", filter: "drop-shadow(0 3px 5px rgba(0,0,0,0.3))" }}
      >
        <path d="M2 1 L2 21 L7 16.5 L10.5 25 L14 23.5 L10.6 15.3 L17.5 15.3 Z" fill="#111" stroke="#fff" strokeWidth={1.6} strokeLinejoin="round" />
      </svg>
    </>
  );
};
