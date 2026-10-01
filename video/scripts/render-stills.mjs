// Renders review stills of the promo at given frames.
// Usage: node scripts/render-stills.mjs 30 120 300 ...   (output: out/stills/frame-<n>.jpg)
import { mkdirSync } from "node:fs";
import path from "node:path";
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";

const root = path.resolve(import.meta.dirname, "..");
const frames = process.argv.slice(2).map(Number);
const compId = process.env.COMP ?? "FranChinaPromo";
const outDir = path.join(root, "out", "stills");
mkdirSync(outDir, { recursive: true });

const serveUrl = await bundle({ entryPoint: path.join(root, "src", "index.ts"), publicDir: path.join(root, "public") });
const composition = await selectComposition({ serveUrl, id: compId });
for (const frame of frames) {
  const output = path.join(outDir, `${compId}-${frame}.jpg`);
  await renderStill({ composition, serveUrl, frame, output, imageFormat: "jpeg", jpegQuality: 85, scale: Number(process.env.SCALE ?? 0.5) });
  console.log("saved", path.relative(root, output));
}
