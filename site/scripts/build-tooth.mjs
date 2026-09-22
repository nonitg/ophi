// Original stylized tooth, not a patient scan or a clinical model: smoothed, indexed meshes of the
// enamel shell and pulp, with baked occlusion and wall thickness so the renderer can shade crevices
// and translucency.
// Run with: node scripts/build-tooth.mjs
import { MarchingCubes } from 'three/examples/jsm/objects/MarchingCubes.js';
import { BufferGeometry, Float32BufferAttribute, MeshBasicMaterial } from 'three';
import { mergeVertices } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { writeFileSync } from 'node:fs';
import { toothDistance, pulpDistance } from './tooth-field.mjs';

const TOOTH_BOUNDS = [1.6, 1.9, 1.6];
const PULP_BOUNDS = [.8, 1.6, .5];

function polygonize(distance, resolution, bounds) {
  const material = new MeshBasicMaterial();
  const mc = new MarchingCubes(resolution, material, false, false, 90000);
  mc.isolation = 0;
  for(let z=0;z<resolution;z++) for(let y=0;y<resolution;y++) for(let x=0;x<resolution;x++) {
    mc.field[x+y*resolution+z*resolution*resolution] = -distance((x/resolution*2-1)*bounds[0],(y/resolution*2-1)*bounds[1],(z/resolution*2-1)*bounds[2]);
  }
  mc.update();
  const positions = new Float32Array(mc.count*3);
  for (let i=0;i<mc.count*3;i++) positions[i] = mc.positionArray[i]*bounds[i%3];
  const soup = new BufferGeometry();
  soup.setAttribute('position', new Float32BufferAttribute(positions, 3));
  const geometry = mergeVertices(soup, 1e-5);
  soup.dispose(); mc.geometry.dispose(); material.dispose();
  return geometry;
}

// Taubin smoothing removes the marching-cubes terracing without shrinking the form.
function smooth(geometry, passes) {
  const position = geometry.attributes.position.array;
  const index = geometry.index.array;
  const count = position.length/3;
  const neighbours = Array.from({ length: count }, () => new Set());
  for (let i=0;i<index.length;i+=3) {
    const [a,b,c] = [index[i],index[i+1],index[i+2]];
    neighbours[a].add(b).add(c); neighbours[b].add(a).add(c); neighbours[c].add(a).add(b);
  }
  const step = (factor) => {
    const next = new Float32Array(position);
    for (let v=0;v<count;v++) {
      let sx=0,sy=0,sz=0;
      for (const n of neighbours[v]) { sx+=position[n*3]; sy+=position[n*3+1]; sz+=position[n*3+2]; }
      const k = neighbours[v].size || 1;
      next[v*3]   += factor*(sx/k-position[v*3]);
      next[v*3+1] += factor*(sy/k-position[v*3+1]);
      next[v*3+2] += factor*(sz/k-position[v*3+2]);
    }
    position.set(next);
  };
  for (let p=0;p<passes;p++) { step(.5); step(-.53); }
  geometry.computeVertexNormals();
}

// Occlusion: how much of the surface's outward neighbourhood is filled by the tooth itself.
function occlusion(x,y,z,nx,ny,nz) {
  let occ = 0, weight = 1;
  for (let i=1;i<=5;i++) {
    const h = .035*i;
    occ += weight*(h - toothDistance(x+nx*h,y+ny*h,z+nz*h));
    weight *= .5;
  }
  return Math.min(Math.max(1 - 3.2*occ, 0), 1);
}
// Thickness: distance travelled inward before leaving the tooth, capped at 1.2 units.
function thickness(x,y,z,nx,ny,nz) {
  for (let t=.03;t<1.2;t+=.03) if (toothDistance(x-nx*t,y-ny*t,z-nz*t) > 0) return t/1.2;
  return 1;
}

function bake(geometry) {
  const p = geometry.attributes.position.array, n = geometry.attributes.normal.array;
  const out = new Float32Array(p.length/3*5);
  for (let v=0;v<p.length/3;v++) {
    const [x,y,z] = [p[v*3],p[v*3+1],p[v*3+2]], [nx,ny,nz] = [n[v*3],n[v*3+1],n[v*3+2]];
    out.set([x,y,z, occlusion(x,y,z,nx,ny,nz), thickness(x,y,z,nx,ny,nz)], v*5);
  }
  return out;
}

function indices(geometry) {
  if (geometry.attributes.position.count > 65535) throw new Error('Mesh too dense for 16-bit indices');
  const index = Uint16Array.from(geometry.index.array);
  // Keep the next Float32 section 4-byte aligned.
  return index.length % 2 ? Uint16Array.from([...index, 0]) : index;
}

const tooth = polygonize(toothDistance, 88, TOOTH_BOUNDS);
smooth(tooth, 6);
const pulp = polygonize(pulpDistance, 60, PULP_BOUNDS);
smooth(pulp, 4);
const toothVertices = bake(tooth), toothIndex = indices(tooth);
const pulpVertices = Float32Array.from(pulp.attributes.position.array), pulpIndex = indices(pulp);
// Layout: four counts, tooth [x y z occlusion thickness], tooth indices, pulp [x y z], pulp indices.
const header = Uint32Array.from([tooth.attributes.position.count, tooth.index.count, pulp.attributes.position.count, pulp.index.count]);
const file = Buffer.concat([header, toothVertices, toothIndex, pulpVertices, pulpIndex].map((a) => Buffer.from(a.buffer, a.byteOffset, a.byteLength)));
writeFileSync(new URL('../public/tooth.bin', import.meta.url), file);
const ao = toothVertices.filter((_, i) => i%5===3), th = toothVertices.filter((_, i) => i%5===4);
console.log(`tooth ${tooth.index.count/3} triangles, pulp ${pulp.index.count/3} triangles, ${file.byteLength} bytes`);
console.log(`occlusion ${Math.min(...ao).toFixed(2)}–${Math.max(...ao).toFixed(2)}, thickness ${Math.min(...th).toFixed(2)}–${Math.max(...th).toFixed(2)}`);
tooth.dispose(); pulp.dispose();
