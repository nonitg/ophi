// Stills for the story scenes from their own entry. Usage: node tools/story/stills.mjs <cold|patient|problem> <frame...> [--scale=0.5]
import path from "node:path";
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
const args = process.argv.slice(2);
const scale = Number((args.find((a) => a.startsWith("--scale=")) ?? "--scale=0.5").split("=")[1]);
const [id, ...frames] = args.filter((a) => !a.startsWith("--"));
const root = path.resolve(import.meta.dirname, "../..");
const serveUrl = await bundle({ entryPoint: path.join(root, "tools/story/entry.tsx"), publicDir: path.join(root, "public") });
const composition = await selectComposition({ serveUrl, id: `Story-${id}`, chromiumOptions: { gl: "angle" } });
for (const f of frames.map(Number)) {
  const output = path.join(root, "out/checks/story", `${id}-${String(f).padStart(5, "0")}.png`);
  await renderStill({ serveUrl, composition, frame: f, output, scale, chromiumOptions: { gl: "angle" } });
}
console.log("done", id, frames.join(","));
