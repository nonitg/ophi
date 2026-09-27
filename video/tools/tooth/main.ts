// Capture page for the pitch video: the site's enamel tooth (renderer imported read-only from site/lib),
// on a transparent canvas, spun about its own long axis so frame 0 matches the homepage pose.
import * as THREE from "three";
import { createStudio } from "../../../site/lib/tooth-studio";
import { decodeToothMesh } from "../../../site/lib/tooth-mesh";

type Mode = "normal" | "normal-noshadow" | "xray";
const FRAMES = 120;
const FIT = 0.8; // share of the frame the tooth's widest extent fills

async function boot() {
  const res = await fetch("/site/public/tooth.bin");
  const buf = await new Response(res.body!.pipeThrough(new DecompressionStream("gzip"))).arrayBuffer();
  const mesh = decodeToothMesh(buf);

  const canvas = document.createElement("canvas");
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1);
  renderer.setClearColor(0x000000, 0);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 50);
  camera.position.set(0, 0.75, 6.5);
  camera.lookAt(0, -0.05, 0);
  const sculpture = new THREE.Group();
  sculpture.rotation.set(0.17, -0.35, -0.21);
  scene.add(sculpture);
  const studio = createStudio(renderer, scene, sculpture, mesh);
  // Spin inside the homepage tilt, about the tooth's own axis.
  const spinner = new THREE.Group();
  for (const child of [...sculpture.children]) { sculpture.remove(child); spinner.add(child); }
  sculpture.add(spinner);
  const floor = scene.children.find((o) => (o as THREE.Mesh).isMesh && ((o as THREE.Mesh).material as THREE.Material).type === "ShadowMaterial")!;

  let view = { zoom: 1, fx: 0, fy: 0 };
  function setup(mode: Mode, size: number) {
    studio.setXray(mode === "xray", true);
    floor.visible = mode === "normal";
    renderer.setSize(size, size, false);
    camera.aspect = 1;
    camera.zoom = view.zoom;
    camera.setViewOffset(size, size, view.fx * size, view.fy * size, size, size);
    camera.updateProjectionMatrix();
  }
  function draw(i: number) {
    spinner.rotation.y = (2 * Math.PI * i) / FRAMES;
    renderer.shadowMap.needsUpdate = true;
    renderer.render(scene, camera);
  }
  // Union of the tooth's alpha bounds over the whole turn, in pixels.
  function measure(size: number) {
    setup("normal-noshadow", size);
    const gl = renderer.getContext();
    const px = new Uint8Array(size * size * 4);
    let x0 = size, y0 = size, x1 = 0, y1 = 0;
    for (let i = 0; i < FRAMES; i++) {
      draw(i);
      gl.readPixels(0, 0, size, size, gl.RGBA, gl.UNSIGNED_BYTE, px);
      for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
        if (px[(y * size + x) * 4 + 3] > 8) {
          const yy = size - 1 - y;
          if (x < x0) x0 = x; if (x > x1) x1 = x; if (yy < y0) y0 = yy; if (yy > y1) y1 = yy;
        }
      }
    }
    return { x0, y0, x1, y1 };
  }
  function frame(i: number, mode: Mode, size: number, ss = 2) {
    setup(mode, size * ss);
    draw(i);
    const out = document.createElement("canvas");
    out.width = out.height = size;
    const ctx = out.getContext("2d")!;
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(canvas, 0, 0, size, size);
    return out.toDataURL("image/png");
  }
  // Fit: scale so the widest extent fills FIT of the frame, then shift its centre to the frame centre.
  function frameUp() {
    const S = 400;
    view = { zoom: 1, fx: 0, fy: 0 };
    let b = measure(S);
    view.zoom = (FIT * S) / Math.max(b.x1 - b.x0, b.y1 - b.y0);
    b = measure(S);
    view.fx = ((b.x0 + b.x1) / 2 - S / 2) / S;
    view.fy = ((b.y0 + b.y1) / 2 - S / 2) / S;
    const check = measure(S);
    return { view, bounds: check };
  }
  (window as any).tooth = { frameUp, frame, measure, FRAMES };
  (window as any).toothReady = true;
}
boot();
