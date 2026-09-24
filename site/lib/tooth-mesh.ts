// The sculpture's mesh, written by scripts/build-tooth.mjs. The file is gzip (hosts send a .bin uncompressed) over
// four counts, the quantization bounds, then 16-bit streams, each delta-coded and stored high bytes first, which
// compress to a third of the raw floats. Kept free of three.js so it downloads alongside it.
export type ToothMesh = { tooth: Float32Array; toothIndex: Uint16Array; pulp: Float32Array; pulpIndex: Uint16Array };

export async function loadToothMesh(signal: AbortSignal): Promise<ToothMesh> {
  const response = await fetch("/tooth.bin", { signal });
  if (!response.ok || !response.body) throw new Error("Tooth artwork unavailable");
  return decodeToothMesh(await new Response(response.body.pipeThrough(new DecompressionStream("gzip"))).arrayBuffer());
}

export function decodeToothMesh(buffer: ArrayBuffer): ToothMesh {
  const [toothVertices, toothIndices, pulpVertices, pulpIndices] = new Uint32Array(buffer, 0, 4);
  const [tx, ty, tz, px, py, pz] = new Float32Array(buffer, 16, 6);
  const bytes = new Uint8Array(buffer, 40);
  const half = bytes.length / 2;
  let at = 0;
  function stream(count: number) {
    const out = new Uint16Array(count);
    let value = 0;
    for (let i = 0; i < count; i++, at++) out[i] = value = (value + (bytes[at] << 8 | bytes[half + at])) & 0xffff;
    return out;
  }
  // Streams hold 0..65535 across ±bound; interleaves them into floats.
  function vertices(count: number, bounds: number[]) {
    const out = new Float32Array(count * bounds.length);
    bounds.forEach((bound, k) => {
      const values = stream(count);
      for (let i = 0; i < count; i++) out[i * bounds.length + k] = bound ? (values[i] / 65535 * 2 - 1) * bound : values[i] / 65535;
    });
    return out;
  }
  // Tooth [x y z occlusion thickness]; occlusion and thickness are already 0..1 (bound 0).
  const tooth = vertices(toothVertices, [tx, ty, tz, 0, 0]);
  const toothIndex = stream(toothIndices);
  const pulp = vertices(pulpVertices, [px, py, pz]);
  const pulpIndex = stream(pulpIndices);
  return { tooth, toothIndex, pulp, pulpIndex };
}
