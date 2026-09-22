import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

export type Studio = { setXray: (on: boolean, instant: boolean) => void; step: (now: number) => boolean; dispose: () => void };

// Shared shading vocabulary. Coordinates are the sculpture's object space (crown up, roots down).
const GLSL_COMMON = /* glsl */ `
varying vec3 vObj;
vec3 srgb(vec3 c) { return pow(c, vec3(2.2)); }
float hash3(vec3 p) { p = fract(p * .3183099 + .1); p *= 17.; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float noise3(vec3 x) {
  vec3 i = floor(x), f = fract(x); f = f * f * (3. - 2. * f);
  return mix(mix(mix(hash3(i), hash3(i + vec3(1,0,0)), f.x), mix(hash3(i + vec3(0,1,0)), hash3(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(hash3(i + vec3(0,0,1)), hash3(i + vec3(1,0,1)), f.x), mix(hash3(i + vec3(0,1,1)), hash3(i + vec3(1,1,1)), f.x), f.y), f.z);
}
float fbm3(vec3 p) { float s = 0., a = .5; for (int i = 0; i < 4; i++) { s += a * noise3(p); p *= 2.03; a *= .5; } return s; }
// Where enamel meets root: scalloped, rising on the sides that face neighbouring teeth.
float cervicalLine(vec3 p) { return -.02 + .07 * cos(2. * atan(p.z, p.x)); }
`;

const ENAMEL = /* glsl */ `
void surface(vec3 p, out vec3 color, out float rough, out float coat, out float height) {
  float line = cervicalLine(p);
  float crown = smoothstep(line - .09, line + .09, p.y);
  // Cusp tips are thin enamel over little dentin, so they read cooler and more glassy.
  vec3 enamel = mix(srgb(vec3(.965, .94, .885)), srgb(vec3(.925, .93, .915)), smoothstep(.95, 1.4, p.y));
  enamel *= .97 + .06 * fbm3(p * 5.);
  vec3 root = mix(srgb(vec3(.93, .895, .82)), srgb(vec3(.86, .8, .69)), smoothstep(-.2, -1.4, p.y)) * (.95 + .08 * fbm3(p * 9.));
  color = mix(root, enamel, crown);
  rough = mix(.7, .26, crown);
  coat = crown * .8;
  // Perikymata: fine growth ridges circling the crown, strongest near the gumline.
  float cervical = crown * (1. - smoothstep(line + .05, line + .45, p.y));
  float ridges = sin(p.y * 150. + fbm3(p * 4.) * 5.);
  height = cervical * ridges * .00035 + (fbm3(p * 22.) - .5) * mix(.0024, .0008, crown);
}
`;

// A physical material keeps three's lighting and shadows; these hooks swap in the procedural enamel.
function enamelMaterial() {
  const material = new THREE.MeshPhysicalMaterial({ roughness: .3, clearcoat: 1, clearcoatRoughness: .2, ior: 1.62, envMapIntensity: .75 });
  material.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nattribute float aOcclusion;\nattribute float aThickness;\nvarying vec3 vObj;\nvarying float vOcc;\nvarying float vThick;")
      .replace("#include <begin_vertex>", "#include <begin_vertex>\nvObj = position; vOcc = aOcclusion; vThick = aThickness;");
    shader.fragmentShader = shader.fragmentShader
      .replace("#include <clipping_planes_pars_fragment>", `#include <clipping_planes_pars_fragment>\nvarying float vOcc;\nvarying float vThick;\n${GLSL_COMMON}\n${ENAMEL}
vec3 bumpNormal(vec3 n, float h) {
  vec3 pos = -vViewPosition, dpx = dFdx(pos), dpy = dFdy(pos);
  vec3 r1 = cross(dpy, n), r2 = cross(n, dpx);
  float det = dot(dpx, r1);
  return normalize(abs(det) * n - sign(det) * (dFdx(h) * r1 + dFdy(h) * r2));
}`)
      .replace("#include <color_fragment>", "#include <color_fragment>\nvec3 sColor; float sRough, sCoat, sHeight;\nsurface(vObj, sColor, sRough, sCoat, sHeight);\ndiffuseColor.rgb = sColor;")
      .replace("#include <roughnessmap_fragment>", "#include <roughnessmap_fragment>\nroughnessFactor = sRough;")
      .replace("#include <normal_fragment_maps>", "#include <normal_fragment_maps>\nnormal = bumpNormal(normal, sHeight);")
      .replace("#include <clearcoat_normal_fragment_maps>", "#include <clearcoat_normal_fragment_maps>\n#ifdef USE_CLEARCOAT\nclearcoatNormal = normalize(mix(clearcoatNormal, normal, .5));\n#endif")
      .replace("#include <emissivemap_fragment>", `#include <emissivemap_fragment>
// Thin walls let warm light through, most visibly at the silhouette.
float rim = 1. - clamp(dot(nonPerturbedNormal, normalize(vViewPosition)), 0., 1.);
totalEmissiveRadiance += srgb(vec3(1., .82, .62)) * (1. - vThick) * (.25 + .75 * rim * rim) * .16;`)
      .replace("#include <lights_physical_fragment>", "#include <lights_physical_fragment>\n#ifdef USE_CLEARCOAT\nmaterial.clearcoat *= sCoat;\n#endif")
      .replace("#include <aomap_fragment>", `#include <aomap_fragment>
float studioAo = smoothstep(.62, 1., vOcc);
reflectedLight.indirectDiffuse *= studioAo;
reflectedLight.directDiffuse *= mix(.55, 1., studioAo);
reflectedLight.indirectSpecular *= studioAo;`);
  };
  return material;
}

// Radiograph: dense enamel glows at the crown's edges, dentin is grey, the pulp is dark.
function xrayMaterials() {
  const vertex = /* glsl */ `
varying vec3 vObj; varying vec3 vN; varying vec3 vV;
void main() {
  vObj = position;
  vec4 mv = modelViewMatrix * vec4(position, 1.);
  vV = -mv.xyz; vN = normalMatrix * normal;
  gl_Position = projectionMatrix * mv;
}`;
  const fade = { value: 0 };
  const common = { transparent: true, depthTest: false, depthWrite: false, vertexShader: vertex };
  const shell = new THREE.ShaderMaterial({ ...common, uniforms: { uFade: fade }, fragmentShader: /* glsl */ `
uniform float uFade; varying vec3 vN; varying vec3 vV;
${GLSL_COMMON}
void main() {
  float facing = abs(dot(normalize(vN), normalize(vV)));
  float line = cervicalLine(vObj);
  float crown = smoothstep(line - .1, line + .1, vObj.y);
  float density = pow(facing, .7) * .5 + crown * (pow(1. - facing, 2.2) * .7 + .2);
  density += (hash3(vec3(gl_FragCoord.xy, 1.)) - .5) * .07;
  gl_FragColor = vec4(.91, .94, .9, clamp(density, 0., 1.) * uFade);
}` });
  const pulp = new THREE.ShaderMaterial({ ...common, uniforms: { uFade: fade }, fragmentShader: /* glsl */ `
uniform float uFade; varying vec3 vN; varying vec3 vV; varying vec3 vObj;
void main() {
  float facing = abs(dot(normalize(vN), normalize(vV)));
  // The page's film colour: the pulp reads as radiolucent, as if the film shows through.
  gl_FragColor = vec4(.055, .122, .098, (.45 + .4 * pow(facing, .5)) * uFade);
}` });
  return { shell, pulp, fade };
}

// The page itself is the floor. The shadow fades out before the canvas edges, so a narrow screen
// never shows it sliced off by a hard line.
function shadowFloor() {
  const material = new THREE.ShadowMaterial({ color: 0x323a34, opacity: .2 });
  material.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nvarying vec4 vClip;")
      .replace("#include <project_vertex>", "#include <project_vertex>\nvClip = gl_Position;");
    shader.fragmentShader = shader.fragmentShader
      .replace("#include <common>", "#include <common>\nvarying vec4 vClip;")
      .replace("#include <tonemapping_fragment>", `vec2 edge = abs(vClip.xy / vClip.w);
gl_FragColor.a *= (1. - smoothstep(.72, .98, edge.x)) * (1. - smoothstep(.72, .98, edge.y));
#include <tonemapping_fragment>`);
  };
  return material;
}

function readStudioMesh(buffer: ArrayBuffer) {
  const [toothVertices, toothIndices, pulpVertices, pulpIndices] = new Uint32Array(buffer, 0, 4);
  let offset = 16;
  const toothData = new Float32Array(buffer, offset, toothVertices * 5); offset += toothData.byteLength;
  const toothIndex = new Uint16Array(buffer, offset, toothIndices); offset += Math.ceil(toothIndices / 2) * 4;
  const pulpData = new Float32Array(buffer, offset, pulpVertices * 3); offset += pulpData.byteLength;
  const pulpIndex = new Uint16Array(buffer, offset, pulpIndices);

  const interleaved = new THREE.InterleavedBuffer(toothData, 5);
  const tooth = new THREE.BufferGeometry();
  tooth.setAttribute("position", new THREE.InterleavedBufferAttribute(interleaved, 3, 0));
  tooth.setAttribute("aOcclusion", new THREE.InterleavedBufferAttribute(interleaved, 1, 3));
  tooth.setAttribute("aThickness", new THREE.InterleavedBufferAttribute(interleaved, 1, 4));
  tooth.setIndex(new THREE.BufferAttribute(toothIndex, 1));
  tooth.computeVertexNormals();
  const pulp = new THREE.BufferGeometry();
  pulp.setAttribute("position", new THREE.BufferAttribute(pulpData, 3));
  pulp.setIndex(new THREE.BufferAttribute(pulpIndex, 1));
  pulp.computeVertexNormals();
  return { tooth, pulp };
}

export async function createStudio(renderer: THREE.WebGLRenderer, scene: THREE.Scene, sculpture: THREE.Group, signal: AbortSignal): Promise<Studio> {
  const response = await fetch("/tooth.bin", { signal });
  if (!response.ok) throw new Error("Tooth artwork unavailable");
  const geometry = readStudioMesh(await response.arrayBuffer());
  if (signal.aborted) throw new DOMException("Aborted", "AbortError");

  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = .9;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.VSMShadowMap;
  const pmrem = new THREE.PMREMGenerator(renderer);
  const room = new RoomEnvironment();
  const environment = pmrem.fromScene(room, .04);
  scene.environment = environment.texture;
  room.dispose(); pmrem.dispose();

  // Studio setup: warm key from the upper left casts the page shadow; cool fill and a bright rim
  // separate the form from the ivory page.
  const lights = new THREE.Group();
  lights.add(new THREE.HemisphereLight(0xfff8ec, 0x5d7560, .3));
  const key = new THREE.DirectionalLight(0xfff0d8, 2.6);
  key.position.set(-3.5, 5, 3.5);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -2.5, right: 2.5, top: 2.5, bottom: -2.5, near: 1, far: 16 });
  key.shadow.radius = 14;
  key.shadow.blurSamples = 20;
  key.shadow.bias = -.0004;
  const fill = new THREE.DirectionalLight(0xdde6ee, .55);
  fill.position.set(4, 0, 2.5);
  const rim = new THREE.DirectionalLight(0xffffff, 2.4);
  rim.position.set(2.5, 3, -4);
  lights.add(key, fill, rim);
  scene.add(lights);

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(9, 9), shadowFloor());
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -1.75;
  floor.receiveShadow = true;
  scene.add(floor);

  const enamel = enamelMaterial();
  const xray = xrayMaterials();
  const tooth = new THREE.Mesh<THREE.BufferGeometry, THREE.Material>(geometry.tooth, enamel);
  tooth.castShadow = true;
  const pulp = new THREE.Mesh(geometry.pulp, xray.pulp);
  pulp.renderOrder = 1;
  sculpture.add(tooth, pulp);
  sculpture.scale.setScalar(.84);
  sculpture.position.y = .2;

  let fadeStart = 0;
  // The enamel returns at once; the radiograph fades in over its film.
  function setXray(on: boolean, instant: boolean) {
    tooth.material = on ? xray.shell : enamel;
    tooth.castShadow = !on;
    pulp.visible = on;
    floor.visible = !on;
    fadeStart = on && !instant ? performance.now() : 0;
    xray.fade.value = on && instant ? 1 : 0;
  }
  setXray(false, true);
  return {
    setXray,
    // Advances the radiograph fade-in; true while more frames are needed.
    step(now) {
      if (!fadeStart) return false;
      const t = Math.min((now - fadeStart) / 420, 1);
      xray.fade.value = 1 - Math.pow(1 - t, 3);
      if (t === 1) fadeStart = 0;
      return t < 1;
    },
    dispose() {
      geometry.tooth.dispose(); geometry.pulp.dispose();
      enamel.dispose(); xray.shell.dispose(); xray.pulp.dispose();
      floor.geometry.dispose(); floor.material.dispose();
      key.shadow.dispose();
      environment.dispose();
    },
  };
}
