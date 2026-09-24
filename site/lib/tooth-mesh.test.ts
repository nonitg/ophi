import { readFileSync } from "node:fs";
import { afterEach, describe, expect, it, vi } from "vitest";
import { loadToothMesh } from "./tooth-mesh";

afterEach(() => vi.unstubAllGlobals());

describe("loadToothMesh", () => {
  it("decodes public/tooth.bin into an indexed tooth and pulp", async () => {
    vi.stubGlobal("fetch", async () => new Response(readFileSync(new URL("../public/tooth.bin", import.meta.url))));
    const { tooth, toothIndex, pulp, pulpIndex } = await loadToothMesh(new AbortController().signal);
    const toothVertices = tooth.length / 5;
    expect(toothIndex.length % 3).toBe(0);
    expect(Math.max(...toothIndex)).toBe(toothVertices - 1);
    expect(Math.max(...pulpIndex)).toBe(pulp.length / 3 - 1);
    // Occlusion and thickness stay normalized.
    const baked = tooth.filter((_, i) => i % 5 > 2);
    expect(Math.min(...baked)).toBeGreaterThan(0);
    expect(Math.max(...baked)).toBeLessThanOrEqual(1);
  });
});
