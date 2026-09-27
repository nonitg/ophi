// Builds src/components/market/canada-map.json: Canada's outline (Natural Earth 50m via world-atlas),
// projected Lambert conformal conic, plus ~357 dots (1 dot ≈ 50 clinics, 17,857 total) placed around
// population centres. Placement is illustrative, not clinic addresses. Run: node build.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { feature } from "topojson-client";
import { geoConicConformal, geoContains, geoPath, geoGraticule } from "d3-geo";

const W = 1100, H = 780;
const CLINICS = 17857, PER_DOT = 50;
const N = Math.round(CLINICS / PER_DOT);

const topo = JSON.parse(readFileSync(new URL("./node_modules/world-atlas/countries-50m.json", import.meta.url)));
const canada = feature(topo, topo.objects.countries).features.find((f) => f.id === "124");
if (!canada) throw new Error("Canada not found");

const projection = geoConicConformal().parallels([49, 77]).rotate([96, 0]).fitExtent([[10, 10], [W - 10, H - 10]], canada);
const path = geoPath(projection).digits(1);
const outline = path(canada);
const graticule = path(geoGraticule().step([10, 5]).extent([[-150, 40], [-45, 85]])());

// [name, lon, lat, population in thousands] — metro areas, roughly 2021 census scale.
const cities = [
  ["Toronto", -79.38, 43.65, 6200], ["Montréal", -73.57, 45.5, 4300], ["Vancouver", -123.12, 49.28, 2700],
  ["Calgary", -114.07, 51.05, 1600], ["Edmonton", -113.49, 53.55, 1500], ["Ottawa", -75.7, 45.42, 1500],
  ["Winnipeg", -97.14, 49.9, 850], ["Québec", -71.21, 46.81, 840], ["Hamilton", -79.87, 43.26, 800],
  ["Kitchener", -80.49, 43.45, 620], ["London", -81.25, 42.98, 560], ["Halifax", -63.57, 44.65, 480],
  ["Victoria", -123.37, 48.43, 420], ["Oshawa", -78.86, 43.9, 420], ["St. Catharines", -79.24, 43.16, 440],
  ["Windsor", -83.03, 42.31, 430], ["Saskatoon", -106.67, 52.13, 340], ["Regina", -104.62, 50.45, 270],
  ["Sherbrooke", -71.89, 45.4, 230], ["Kelowna", -119.5, 49.89, 230], ["Barrie", -79.69, 44.39, 230],
  ["Abbotsford", -122.31, 49.05, 200], ["St. John's", -52.71, 47.56, 215], ["Kingston", -76.48, 44.23, 175],
  ["Sudbury", -80.99, 46.49, 175], ["Saguenay", -71.07, 48.43, 165], ["Trois-Rivières", -72.54, 46.35, 165],
  ["Guelph", -80.25, 43.55, 165], ["Moncton", -64.78, 46.09, 170], ["Saint John", -66.06, 45.27, 130],
  ["Peterborough", -78.32, 44.3, 130], ["Thunder Bay", -89.25, 48.38, 125], ["Lethbridge", -112.84, 49.69, 125],
  ["Nanaimo", -123.94, 49.17, 115], ["Kamloops", -120.33, 50.68, 115], ["Red Deer", -113.81, 52.27, 110],
  ["Fredericton", -66.64, 45.96, 110], ["Belleville", -77.38, 44.16, 110], ["Brantford", -80.26, 43.14, 145],
  ["Drummondville", -72.48, 45.88, 100], ["Prince George", -122.75, 53.92, 90], ["Charlottetown", -63.13, 46.24, 80],
  ["Sault Ste. Marie", -84.33, 46.52, 75], ["Medicine Hat", -110.68, 50.04, 75], ["Grande Prairie", -118.79, 55.17, 70],
  ["Brandon", -99.95, 49.85, 55], ["Rimouski", -68.52, 48.45, 55], ["North Bay", -79.46, 46.31, 70],
  ["Fort McMurray", -111.38, 56.73, 70], ["Sydney", -60.19, 46.14, 95], ["Whitehorse", -135.06, 60.72, 30],
  ["Yellowknife", -114.37, 62.45, 22], ["Iqaluit", -68.52, 63.75, 8], ["Rouyn-Noranda", -79.02, 48.24, 42],
  ["Vernon", -119.27, 50.27, 65], ["Courtenay", -124.99, 49.69, 70], ["Prince Albert", -105.75, 53.2, 45],
  ["Moose Jaw", -105.53, 50.39, 35], ["Thompson", -97.86, 55.74, 13], ["Sept-Îles", -66.38, 50.21, 25],
  ["Corner Brook", -57.95, 48.95, 30], ["Timmins", -81.33, 48.47, 40], ["Cornwall", -74.73, 45.02, 60],
];

// Deterministic PRNG (mulberry32) so every render places the same dots.
let seed = 2026;
const rnd = () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
const gauss = () => Math.sqrt(-2 * Math.log(rnd() + 1e-9)) * Math.cos(2 * Math.PI * rnd());

// Largest-remainder allocation of N dots by population, at least one per listed centre.
const total = cities.reduce((n, c) => n + c[3], 0);
let alloc = cities.map((c) => Math.max(1, (c[3] / total) * N));
const floors = alloc.map(Math.floor);
let left = N - floors.reduce((a, b) => a + b, 0);
const order = alloc.map((a, i) => [a - Math.floor(a), i]).sort((a, b) => b[0] - a[0]);
for (const [, i] of order) { if (left <= 0) break; floors[i]++; left--; }
alloc = floors;

const MIN = 10.4; // min screen distance between dot centres (px); dots draw at r≈4.3
const dots = [];
const tooClose = (x, y) => dots.some((d) => (d.x - x) ** 2 + (d.y - y) ** 2 < MIN * MIN);
cities.forEach(([name, lon, lat, pop], ci) => {
  let placed = 0, tries = 0, sigmaKm = 10 + 5 * Math.sqrt(pop / 100);
  while (placed < alloc[ci] && tries < 20000) {
    tries++;
    if (tries % 400 === 0) sigmaKm *= 1.25;
    const la = lat + (gauss() * sigmaKm) / 111;
    const lo = lon + (gauss() * sigmaKm) / (111 * Math.cos((lat * Math.PI) / 180));
    if (!geoContains(canada, [lo, la])) continue;
    const [x, y] = projection([lo, la]);
    if (tooClose(x, y)) continue;
    dots.push({ x: +x.toFixed(1), y: +y.toFixed(1), city: name });
    placed++;
  }
  if (placed < alloc[ci]) console.warn(`${name}: placed ${placed}/${alloc[ci]}`);
});

// Reveal order: a west→east sweep with texture, 0..1.
const xs = dots.map((d) => d.x), x0 = Math.min(...xs), x1 = Math.max(...xs);
dots.forEach((d) => { d.o = +Math.min(1, Math.max(0, 0.85 * ((d.x - x0) / (x1 - x0)) + 0.15 * rnd())).toFixed(3); });

// Two national groups, marked on dots in their main markets (illustrative): ~630 and ~510 clinics.
const pick = (cityList, group) => {
  for (const c of cityList) {
    const d = dots.find((x) => x.city === c && !x.g);
    if (d) d.g = group;
  }
};
pick(["Toronto", "Toronto", "Toronto", "Montréal", "Montréal", "Vancouver", "Calgary", "Edmonton", "Ottawa", "Winnipeg", "Halifax", "Hamilton", "London"], "dc");
pick(["Vancouver", "Vancouver", "Toronto", "Toronto", "Montréal", "Québec", "Calgary", "Victoria", "Kelowna", "Edmonton"], "d123");

const labels = ["Vancouver", "Calgary", "Winnipeg", "Toronto", "Montréal", "Halifax"].map((n) => {
  const c = cities.find((x) => x[0] === n);
  const [x, y] = projection([c[1], c[2]]);
  return { name: n, x: +x.toFixed(1), y: +y.toFixed(1) };
});

const out = { width: W, height: H, perDot: PER_DOT, clinics: CLINICS, outline, graticule, dots, labels };
writeFileSync(new URL("../../src/components/market/canada-map.json", import.meta.url), JSON.stringify(out));
console.log(`dots ${dots.length}/${N}, outline ${(outline.length / 1024).toFixed(0)} KB, dc ${dots.filter((d) => d.g === "dc").length}, d123 ${dots.filter((d) => d.g === "d123").length}`);
