// Original stylized tooth shape as signed distance fields (positive outside, object units).
// Not a patient scan or a clinical model.
export function smoothMin(a, b, k) {
  const h = Math.max(k - Math.abs(a-b), 0) / k;
  return Math.min(a,b) - h*h*k*.25;
}
export function ellipsoid(x,y,z, rx,ry,rz) {
  return (Math.sqrt((x/rx)**2 + (y/ry)**2 + (z/rz)**2)-1)*Math.min(rx,ry,rz);
}
// Centre line of each root, shared by the outer shape and its canal.
function rootPath(side, t) {
  return [side*(.36+.19*Math.sin(t*2.1)), .05-t*1.49, side*.08*t];
}
export function toothDistance(x,y,z) {
  // Rounded enamel body and four slightly uneven cusps.
  let d = ellipsoid(x,y-.50,z,.79,.72,.66);
  for (const side of [-1,1]) for (const front of [-1,1]) {
    d = smoothMin(d, ellipsoid(x-side*.37,y-(.94+front*.04),z-front*.29,.39,.34,.37),.21);
  }
  // Two gently divergent, tapered roots, fused into the cervical body.
  for (const side of [-1,1]) for(let j=0;j<=23;j++) {
    const t=j/23;
    const [cx,cy,cz]=rootPath(side,t);
    const radius=.345*Math.pow(1-t,.82)+.035;
    d=smoothMin(d,ellipsoid(x-cx,y-cy,z-cz,radius,radius*1.2,radius*.88),.13);
  }
  // A shallow occlusal groove at the centre of the crown.
  const groove=ellipsoid(x,y-1.29,z,.115,.26,.55);
  return -smoothMin(-d,groove,.06);
}
// Pulp chamber with a horn under each cusp, narrowing into one canal per root.
export function pulpDistance(x,y,z) {
  let d = ellipsoid(x,y-.42,z,.34,.25,.26);
  for (const side of [-1,1]) for (const front of [-1,1]) {
    d = smoothMin(d, ellipsoid(x-side*.25,y-.66,z-front*.16,.09,.16,.09),.1);
  }
  for (const side of [-1,1]) for(let j=0;j<=21;j++) {
    const t=j/23;
    const [cx,cy,cz]=rootPath(side,t);
    const radius=.085*Math.pow(1-t,.7)+.018;
    d=smoothMin(d,ellipsoid(x-cx,y-cy,z-cz,radius,radius*1.3,radius),.09);
  }
  return d;
}
