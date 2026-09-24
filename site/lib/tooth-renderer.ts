import * as THREE from "three";
import { createStudio } from "./tooth-studio";
import type { ToothMesh } from "./tooth-mesh";

export type ToothControls = { xray: (enabled: boolean) => void; dispose: () => void };

export async function createToothViewer(host: HTMLDivElement, mesh: ToothMesh, onFacingAway?: (away: boolean) => void): Promise<ToothControls> {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "low-power" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
  renderer.setClearColor(0x000000, 0);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, 1, .1, 50);
  camera.position.set(0, .75, 6.5);
  camera.lookAt(0, -.05, 0);
  const sculpture = new THREE.Group();
  sculpture.rotation.set(.17, -.35, -.21);
  scene.add(sculpture);
  const studio = createStudio(renderer, scene, sculpture, mesh);
  // Where the browser compiles shaders in the background, the sculpture's main shaders finish there before the first
  // frame instead of freezing the page on it.
  if (renderer.extensions.has("KHR_parallel_shader_compile")) await renderer.compileAsync(scene, camera);

  // An original enamel sculpture: all material/lighting is live, not a rotating bitmap.
  host.appendChild(renderer.domElement);
  let disposed = false;
  let frame = 0;
  let targetY = -.35;
  let targetX = .17;
  let visible = true;
  let dragging = false;
  let lastX = 0;
  let lastY = 0;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  function render() {
    frame = 0;
    if (disposed || !visible || document.hidden) return;
    const ease = reduced.matches ? 1 : .16;
    sculpture.rotation.y += (targetY - sculpture.rotation.y) * ease;
    sculpture.rotation.x += (targetX - sculpture.rotation.x) * ease;
    const animating = studio.step(performance.now());
    renderer.render(scene, camera);
    if (animating || Math.abs(targetY-sculpture.rotation.y)+Math.abs(targetX-sculpture.rotation.x) > .001) frame = requestAnimationFrame(render);
  }
  function requestRender() { if (!frame && !disposed) frame = requestAnimationFrame(render); }
  // Reports when a turn comes to rest with the tooth's back to the viewer; spinning past it doesn't count.
  let facingAway = false;
  function settle() {
    const away = Math.cos(targetY + .35) < -.5;
    if (away !== facingAway) { facingAway = away; onFacingAway?.(away); }
  }
  function resize() {
    const { width, height } = host.getBoundingClientRect();
    if (!width || !height) return;
    camera.aspect = width/height;
    camera.position.z = width < 360 ? 7 : 6.5;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
    requestRender();
  }
  const resizeObserver = new ResizeObserver(resize);
  resizeObserver.observe(host);
  const intersectionObserver = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; if (visible) requestRender(); });
  intersectionObserver.observe(host);
  function down(event: PointerEvent) {
    if (event.button !== 0) return;
    dragging = true; lastX = event.clientX; lastY = event.clientY;
    host.setPointerCapture(event.pointerId);
  }
  function move(event: PointerEvent) {
    if (!dragging) return;
    targetY += (event.clientX-lastX)*.012;
    // Vertical touch movement is reserved for scrolling the page.
    if (event.pointerType !== "touch") targetX = THREE.MathUtils.clamp(targetX+(event.clientY-lastY)*.008,-.7,.7);
    lastX=event.clientX; lastY=event.clientY;
    requestRender();
  }
  function up() { if (dragging) settle(); dragging = false; }
  function keydown(event: KeyboardEvent) {
    if (!["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Home"].includes(event.key)) return;
    event.preventDefault();
    if (event.key === "ArrowLeft") targetY -= .3;
    if (event.key === "ArrowRight") targetY += .3;
    if (event.key === "ArrowUp") targetX = Math.max(-.7,targetX-.2);
    if (event.key === "ArrowDown") targetX = Math.min(.7,targetX+.2);
    if (event.key === "Home") { targetY=-.35; targetX=.17; }
    settle();
    requestRender();
  }
  function visibility() { if (!document.hidden) requestRender(); }
  host.addEventListener("pointerdown",down);
  host.addEventListener("pointermove",move);
  host.addEventListener("pointerup",up);
  host.addEventListener("pointercancel",up);
  host.addEventListener("lostpointercapture",up);
  host.addEventListener("keydown",keydown);
  document.addEventListener("visibilitychange",visibility);
  resize();
  return {
    xray(enabled) { studio.setXray(enabled, reduced.matches); requestRender(); },
    dispose() {
      disposed=true; cancelAnimationFrame(frame);
      resizeObserver.disconnect(); intersectionObserver.disconnect();
      host.removeEventListener("pointerdown",down); host.removeEventListener("pointermove",move);
      host.removeEventListener("pointerup",up); host.removeEventListener("pointercancel",up); host.removeEventListener("lostpointercapture",up);
      host.removeEventListener("keydown",keydown); document.removeEventListener("visibilitychange",visibility);
      studio.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    },
  };
}

