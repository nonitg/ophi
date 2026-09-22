// Site-wide X-ray: the whole page is re-exposed as a radiograph (styles in app/xray.css).
// Turning it on sweeps the new exposure across the page left to right, the way a panoramic
// unit's arm builds its image; turning it off lets the film fade away.

const SWEEP = { duration: 950, easing: "cubic-bezier(.65, 0, .35, 1)", fill: "both" } as const;
const BEAM_WIDTH = 140;
let latest = 0;

export function setSiteXray(on: boolean, update: () => void) {
  const root = document.documentElement;
  const sweeping = typeof document.startViewTransition === "function" && !matchMedia("(prefers-reduced-motion: reduce)").matches;
  let beam: HTMLDivElement | undefined;
  const apply = () => {
    root.toggleAttribute("data-xray", on);
    // The beam exists only in the new state, so it rides inside the revealed part of the sweep.
    if (on && sweeping) beam = document.body.appendChild(Object.assign(document.createElement("div"), { className: "xray-beam" }));
    update();
  };
  if (!sweeping) { apply(); return; }

  const id = ++latest;
  root.dataset.sweep = on ? "in" : "out";
  const transition = document.startViewTransition(apply);
  if (on) {
    // Started in the same task, the film reveal and the beam share one clock.
    transition.ready.then(() => {
      root.animate({ clipPath: ["inset(0 100% 0 0)", "inset(0 0 0 0)"] }, { ...SWEEP, pseudoElement: "::view-transition-new(root)" });
      beam?.animate([
        { translate: `-${BEAM_WIDTH}px 0`, opacity: 1 },
        { opacity: 1, offset: .9 },
        { translate: `calc(100vw - ${BEAM_WIDTH}px) 0`, opacity: 0 },
      ], SWEEP);
    }, () => {});
  }
  const done = () => { if (id === latest) delete root.dataset.sweep; beam?.remove(); };
  transition.finished.then(done, done);
}

// ALARA: dental radiography keeps exposures as low as reasonably achievable, so a burst of
// exposures earns a reminder. Returns true on the exposure that completes a burst.
export function exposureCounter(limit = 5, windowMs = 20_000) {
  let times: number[] = [];
  return (now: number) => {
    times = [...times.filter((t) => now - t < windowMs), now];
    if (times.length < limit) return false;
    times = [];
    return true;
  };
}
