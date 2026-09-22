import { describe, expect, it } from "vitest";
import { exposureCounter } from "./xray-mode";

describe("exposureCounter", () => {
  it("flags the fifth exposure inside the window, then starts counting again", () => {
    const expose = exposureCounter(5, 20_000);
    const burst = [0, 1_000, 2_000, 3_000, 4_000].map(expose);
    expect(burst).toEqual([false, false, false, false, true]);
    expect(expose(5_000)).toBe(false);
  });
});
