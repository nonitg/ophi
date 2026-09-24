"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal, flushSync } from "react-dom";
import type { ToothControls } from "@/lib/tooth-renderer";
import { exposureCounter, setSiteXray } from "@/lib/xray-mode";
import { copy } from "@/lib/copy";
import { XrayFilters } from "@/components/xray-filters";

type Film = { xray: boolean; away: boolean };

// A tooth turned away under X-ray means the film went in back to front.
function markReversed(film: Film) {
  const reversed = film.xray && film.away;
  document.documentElement.toggleAttribute("data-film-reversed", reversed);
  return reversed;
}

const xrayButton = "view-mode h-[30px] rounded-[30px] border border-[#bdc8b3] bg-[#f4f2e9b3] px-3 text-[11px] text-label transition-[background,border-color] duration-200 hover:border-[#7e9374] hover:bg-[#dfe5d3] aria-pressed:border-ink aria-pressed:bg-ink aria-pressed:text-paper aria-pressed:hover:border-ink-soft aria-pressed:hover:bg-ink-soft phone:h-7 phone:px-2.5 phone:text-[10px] xray:border-pill-line xray:bg-[#0e1f19b3] xray:text-muted xray:hover:border-[#e6ece380] xray:hover:bg-[#e6ece31a] xray:aria-pressed:border-ink xray:aria-pressed:bg-ink xray:aria-pressed:text-paper xray:aria-pressed:shadow-[0_0_18px_-4px_#dff3e6b3] xray:aria-pressed:hover:border-white xray:aria-pressed:hover:bg-white";
// Notes found by playing with the X-ray view, written beside the film like a clinician's annotation.
// Phones: beside "Less", above "paperwork.", where X-ray leaves bare film (it casts no shadow). The note's foot sits one
// headline line (13.11vw = .99 × .86 × 15.4vw) above the poster's, less the gap below the sculpture, so these offsets
// follow the phone headline and poster sizes in app/page.tsx. scripts/site-xray-note.py checks the fit.
const xrayNote = "xray-note absolute top-[3%] right-[5%] z-3 w-max max-w-[min(340px,42vw)] text-right font-serif text-[17px] leading-[1.3] text-ink italic phone:top-auto phone:right-0 phone:bottom-[min(calc(13.11vw-28px),61px)] phone:max-w-[min(440px,calc(80vw-56px))] phone:text-[15px] phone:text-balance narrow:bottom-[max(34px,calc(13.11vw-20px))] narrow:max-w-[min(260px,calc(100vw-140px))] narrow:text-[14px] small:bottom-10 small:text-[13px] motion-safe:not-empty:animate-[note-in_.45s_var(--ease-out)_both]";

function ToothFallback() {
  return <svg className="tooth-fallback absolute inset-[10%_14%_15%] h-[75%] w-[72%] drop-shadow-[12px_25px_18px_#4e64552c]" viewBox="0 0 300 360" aria-hidden="true"><defs><linearGradient id="enamel" x1="0" y1="0" x2="1" y2=".7"><stop stopColor="#fffef6" /><stop offset=".6" stopColor="#f4e9d3" /><stop offset="1" stopColor="#c8c5aa" /></linearGradient></defs><g transform="rotate(-12 150 180)"><path d="M66 54C86 29 112 34 146 47C175 33 213 31 234 56C267 95 246 147 230 173C215 204 224 282 202 312C177 335 173 232 151 216C129 205 123 314 103 316C78 319 85 244 75 205C67 173 41 140 45 102C46 82 54 64 66 54Z" fill="url(#enamel)" /><path d="M92 61Q117 73 147 62Q174 53 209 65" stroke="#d5cdb8" strokeWidth="4" fill="none" strokeLinecap="round" /></g></svg>;
}

export function ToothScene() {
  const host = useRef<HTMLDivElement>(null);
  const controls = useRef<ToothControls | null>(null);
  const [ready, setReady] = useState(false);
  const [xray, setXray] = useState(false);
  const [note, setNote] = useState<keyof typeof copy.xray | null>(null);
  // Read by the renderer's callback, which outlives any one render.
  const film = useRef<Film>({ xray: false, away: false });
  const [countExposure] = useState(() => exposureCounter());
  useEffect(() => {
    const container = host.current;
    if (!container) return;
    const abort = new AbortController();
    let cleanup: ToothControls | undefined;
    const observer = new IntersectionObserver(async ([entry]) => {
      if (!entry.isIntersecting) return;
      observer.disconnect();
      try {
        const { createToothViewer } = await import("@/lib/tooth-renderer");
        if (abort.signal.aborted) return;
        cleanup = await createToothViewer(container, abort.signal, (away) => {
          film.current.away = away;
          const reversed = markReversed(film.current);
          setNote((current) => reversed ? "backwards" : current === "backwards" ? null : current);
        });
        if (abort.signal.aborted) { cleanup.dispose(); return; }
        controls.current = cleanup;
        setReady(true);
      } catch (error) {
        // Keep the server-rendered artwork when WebGL or the asset is unavailable.
        if (process.env.NODE_ENV === "development" && !abort.signal.aborted) console.warn("Tooth artwork fallback:", error);
      }
    }, { rootMargin: "120px" });
    observer.observe(container);
    return () => {
      abort.abort(); observer.disconnect(); cleanup?.dispose(); controls.current = null;
      document.documentElement.removeAttribute("data-xray"); document.documentElement.removeAttribute("data-film-reversed");
    };
  }, []);
  // The X-ray button re-exposes the whole page, not just the tooth. The requested state is kept in a ref:
  // the page itself only changes a frame later, and a second press inside that frame must still count.
  function toggleXray() {
    const next = !film.current.xray;
    film.current.xray = next;
    const burst = next && countExposure(performance.now());
    setSiteXray(next, () => {
      controls.current?.xray(next);
      const reversed = markReversed(film.current);
      flushSync(() => { setXray(next); setNote(reversed ? "backwards" : burst ? "alara" : null); });
    });
  }
  // The button lives in the site header (app/page.tsx), since it re-exposes the whole page; its notes stay beside the film.
  const slot = ready ? document.getElementById("xray-slot") : null;
  return (
    <div className="tooth-viewer absolute inset-0" data-ready={ready}>
      {!ready && <ToothFallback />}
      <XrayFilters />
      <div ref={host} className="tooth-canvas absolute inset-0 size-full cursor-grab touch-pan-y outline-offset-[-30px] active:cursor-grabbing [&_canvas]:size-full" tabIndex={ready ? 0 : undefined} role="group" aria-label={ready ? "Interactive tooth sculpture. Drag or use arrow keys to rotate. Home resets the view." : "An ivory tooth sculpture"} />
      {slot && createPortal(<button type="button" className={xrayButton} aria-pressed={xray} onClick={toggleXray}>X-ray</button>, slot)}
      {ready && <p className={xrayNote} role="status">{note && copy.xray[note]}</p>}
    </div>
  );
}
