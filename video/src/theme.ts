import { loadFont as loadDMSans } from "@remotion/google-fonts/DMSans";
import { loadFont as loadDMMono } from "@remotion/google-fonts/DMMono";
import { continueRender, delayRender, Easing, staticFile } from "remotion";

// Public Ophi identity (DESIGN.md): ivory paper, forest ink, orange accent; film/bone for X-ray moments.
export const color = {
  ivory: "#f4f2e9",
  forest: "#193a30",
  orange: "#ef865b",
  sage: "#e4e7d9",
  muted: "#5c6557",
  film: "#0e1f19",
  bone: "#e6ece3",
  // Derived tints
  ivoryDeep: "#ebe7d8",
  forestSoft: "#2f5446",
  orangeSoft: "#f7c2a8",
  ink: "#0f241d",
  shade: "#232a2e",
} as const;

// Newsreader is the site's self-hosted 400 instance (opsz axis kept), so display type matches ophi.app.
const NEWSREADER = "Newsreader";
const newsreaderHandle = delayRender("Newsreader");
Promise.all(
  [
    new FontFace(NEWSREADER, `url(${staticFile("fonts/newsreader-400.woff2")}) format("woff2")`, { weight: "400", style: "normal" }),
    new FontFace(NEWSREADER, `url(${staticFile("fonts/newsreader-400-italic.woff2")}) format("woff2")`, { weight: "400", style: "italic" }),
  ].map((f) => f.load().then((loaded) => document.fonts.add(loaded))),
)
  .then(() => continueRender(newsreaderHandle))
  .catch((e) => {
    console.error("Newsreader failed to load", e);
    continueRender(newsreaderHandle);
  });

const dmSans = loadDMSans("normal", { weights: ["400", "500", "700"], subsets: ["latin"] });
const dmMono = loadDMMono("normal", { weights: ["400", "500"], subsets: ["latin"] });

export const font = {
  display: `"${NEWSREADER}", Georgia, serif`,
  sans: `${dmSans.fontFamily}, system-ui, sans-serif`,
  mono: `${dmMono.fontFamily}, ui-monospace, monospace`,
} as const;

// Type scale for a 1920×1080 frame (px).
export const type = {
  hero: 168,
  h1: 112,
  h2: 76,
  h3: 52,
  lead: 40,
  body: 30,
  label: 22,
  foot: 18,
} as const;

export const ease = {
  out: Easing.bezier(0.16, 1, 0.3, 1),
  inOut: Easing.bezier(0.65, 0, 0.35, 1),
  in: Easing.bezier(0.7, 0, 0.84, 0),
  soft: Easing.bezier(0.33, 1, 0.68, 1),
};

// Spring configs for spring({ frame, fps, config }).
export const springs = {
  gentle: { damping: 200, stiffness: 80, mass: 1 },
  critical: { damping: 26, stiffness: 120, mass: 1 },
  overshoot: { damping: 9, stiffness: 140, mass: 0.8 },
  snappy: { damping: 18, stiffness: 220, mass: 0.7 },
} as const;

export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;
