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

function ToothFallback() {
  return <svg className="tooth-fallback" viewBox="0 0 300 360" aria-hidden="true"><defs><linearGradient id="enamel" x1="0" y1="0" x2="1" y2=".7"><stop stopColor="#fffef6" /><stop offset=".6" stopColor="#f4e9d3" /><stop offset="1" stopColor="#c8c5aa" /></linearGradient></defs><g transform="rotate(-12 150 180)"><path d="M66 54C86 29 112 34 146 47C175 33 213 31 234 56C267 95 246 147 230 173C215 204 224 282 202 312C177 335 173 232 151 216C129 205 123 314 103 316C78 319 85 244 75 205C67 173 41 140 45 102C46 82 54 64 66 54Z" fill="url(#enamel)" /><path d="M92 61Q117 73 147 62Q174 53 209 65" stroke="#d5cdb8" strokeWidth="4" fill="none" strokeLinecap="round" /></g></svg>;
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
    <div className="tooth-viewer" data-ready={ready}>
      {!ready && <ToothFallback />}
      <XrayFilters />
      <div ref={host} className="tooth-canvas" tabIndex={ready ? 0 : undefined} role="group" aria-label={ready ? "Interactive tooth sculpture. Drag or use arrow keys to rotate. Home resets the view." : "An ivory tooth sculpture"} />
      {slot && createPortal(<button type="button" className="view-mode" aria-pressed={xray} onClick={toggleXray}>X-ray</button>, slot)}
      {ready && <p className="xray-note" role="status">{note && copy.xray[note]}</p>}
    </div>
  );
}
