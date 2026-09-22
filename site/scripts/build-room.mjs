// The room the page sits in: cotton paper grain, and afternoon window light with a few leaves.
// Original procedural art. Run with: node scripts/build-room.mjs
import { writeFileSync } from 'node:fs';

// Drawn over the page with plain transparency: sunlit panes are fully clear, so the brand colours
// show exactly as printed; the window bars and leaves lay a thin cool-dark shade over them.
const SHADE = '#232a2e';
const DEPTH = .1;
const round = (n) => +n.toFixed(1);

// Seeded so every build draws the same leaves.
function random(seed) {
  return () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
}

// Light enters from the upper left, so window panes land on the page as parallelograms
// leaning down and to the right, the same direction the tooth's key light throws its shadow.
function panes({ left, top, width, height, columns, rows, mullion, transom, lean }) {
  const shapes = [];
  for (let row = 0; row < rows; row++) for (let column = 0; column < columns; column++) {
    const t = top + row * (height + transom), b = t + height;
    const x = (y) => round(left + lean * (y - top) + column * (width + mullion));
    shapes.push(`<path d="M${x(t)} ${t}H${round(x(t) + width)}L${round(x(b) + width)} ${b}H${x(b)}Z"/>`);
  }
  return shapes.join('');
}

// Leaves along a curved stem, alternating sides. Drawn into the shade mask, so white means shadow.
function branch(next, [x0, y0], [cx, cy], [x1, y1], count, size) {
  const leaves = [`<path d="M${x0} ${y0}Q${cx} ${cy} ${x1} ${y1}" fill="none" stroke="#fff" stroke-width="${round(size * .07)}" stroke-linecap="round"/>`];
  for (let i = 0; i < count; i++) {
    const t = .12 + .88 * i / (count - 1);
    const x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1;
    const y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1;
    const along = Math.atan2(2 * (1 - t) * (cy - y0) + 2 * t * (y1 - cy), 2 * (1 - t) * (cx - x0) + 2 * t * (x1 - cx)) * 180 / Math.PI;
    const side = i % 2 ? 1 : -1;
    const angle = along + side * (38 + next() * 28);
    const scale = size * (.7 + next() * .5) * (1 - t * .35) / 100;
    leaves.push(`<use href="#leaf" transform="translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${angle.toFixed(1)}) scale(${scale.toFixed(3)})"/>`);
  }
  return leaves.join('');
}

function room({ width, height, window, branches, paneBlur, leafBlur }) {
  const next = random(11);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMin slice">
<defs>
<path id="leaf" d="M0 0C22-20 64-24 100 0C62 16 24 22 0 0Z"/>
<filter id="pane" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="${paneBlur}"/></filter>
<filter id="scatter" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="${paneBlur * 6}"/></filter>
<filter id="leaves" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="${leafBlur}"/></filter>
<linearGradient id="spill" x1="0" y1="0" x2="0" y2="1"><stop offset=".84" stop-opacity="0"/><stop offset="1"/></linearGradient>
<!-- Where the mask is white the page is in shade; the window panes and the bottom edge cut it away. -->
<mask id="shade" maskUnits="userSpaceOnUse" x="0" y="0" width="${width}" height="${height}">
<rect width="${width}" height="${height}" fill="#fff"/>
<g filter="url(#scatter)" opacity=".4">${panes(window)}</g>
<g filter="url(#pane)">${panes(window)}</g>
<g fill="#fff" filter="url(#leaves)">${branches.map((b) => branch(next, ...b)).join('')}</g>
<rect width="${width}" height="${height}" fill="url(#spill)"/>
</mask>
</defs>
<rect width="${width}" height="${height}" fill="${SHADE}" fill-opacity="${DEPTH}" mask="url(#shade)"/>
</svg>
`;
}

// Faint cotton-paper grain, tiled beneath the content.
const paper = `<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="2" seed="9" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .24  0 0 0 0 .21  0 0 0 0 .15  0 0 0 .3 -.12"/></filter>
<rect width="256" height="256" filter="url(#grain)"/>
</svg>
`;

const wide = room({
  width: 1600, height: 1000, paneBlur: 12, leafBlur: 6,
  // A tall window: its bars fall between the headline lines and down the gutter beside the signup.
  window: { left: 8, top: -233, width: 689, height: 600, columns: 3, rows: 2, mullion: 44, transom: 44, lean: .35 },
  branches: [
    [[700, -60], [880, 30], [1000, 200], 6, 120],
    [[1680, 90], [1540, 150], [1420, 330], 6, 115],
  ],
});
const tall = room({
  width: 800, height: 1600, paneBlur: 10, leafBlur: 5,
  window: { left: -300, top: -100, width: 803, height: 1163, columns: 2, rows: 2, mullion: 40, transom: 33, lean: .2 },
  branches: [
    [[860, 150], [700, 230], [600, 420], 6, 110],
  ],
});

// X-ray mode: developed film has a finer, pale silver grain in place of cotton fibres.
const film = `<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="1.15" numOctaves="2" seed="4" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .86  0 0 0 0 .93  0 0 0 0 .89  0 0 0 .32 -.12"/></filter>
<rect width="256" height="256" filter="url(#grain)"/>
</svg>
`;

// A film packet exposed back to front records the embossed lead foil behind it: rows of dashes
// leaning alternately, the herringbone every dental assistant learns to recognise.
const herringbone = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="16" viewBox="0 0 32 16">
<g fill="none" stroke="#e6ece3" stroke-opacity=".1" stroke-width="1.6" stroke-linecap="round">
${[0, 8, 16, 24].map((x) => `<path d="M${x + 1} 6.5L${x + 6} 1.5M${x + 1} 9.5L${x + 6} 14.5"/>`).join('')}
</g>
</svg>
`;

const out = (name, content) => { writeFileSync(new URL(`../public/${name}`, import.meta.url), content); console.log(`${name} ${content.length} bytes`); };
out('light-wide.svg', wide);
out('light-tall.svg', tall);
out('paper.svg', paper);
out('film.svg', film);
out('herringbone.svg', herringbone);
