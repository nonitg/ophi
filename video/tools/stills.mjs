// Render several stills of one composition from a single bundle (much faster than repeated `remotion still`).
// Usage: node tools/stills.mjs <compositionId> <outDir> <frame> [frame...] [--scale=0.5]
import path from "node:path";
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";

const args = process.argv.slice(2);
const scale = Number((args.find((a) => a.startsWith("--scale=")) ?? "--scale=1").split("=")[1]);
const [id, outDir, ...frames] = args.filter((a) => !a.startsWith("--"));
const root = path.resolve(import.meta.dirname, "..");
const serveUrl = await bundle({ entryPoint: path.join(root, "src/index.ts"), publicDir: path.join(root, "public") });
const composition = await selectComposition({ serveUrl, id, chromiumOptions: { gl: "angle" } });
for (const f of frames.map(Number)) {
  const output = path.resolve(outDir, `${id}-${String(f).padStart(5, "0")}.png`);
  await renderStill({ serveUrl, composition, frame: f, output, scale, chromiumOptions: { gl: "angle" } });
  console.log(output);
}
