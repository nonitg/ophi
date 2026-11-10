"use client";

import { Fragment, useCallback, useEffect, useEffectEvent, useRef, useState, type KeyboardEvent, type PointerEvent } from "react";
import type { DemoCall } from "@/lib/calls";
import { copy } from "@/lib/copy";
import { Icon } from "@/components/icons";
import { HEAR_EVENT, NOW_EVENT, type HearDetail, type NowDetail } from "@/components/hear-it";

// "starting": play was pressed and sound is expected any moment. "loading": the wait has grown long enough to say so.
type Status = "idle" | "starting" | "loading" | "playing" | "paused" | "ended" | "error";

const clock = (seconds: number) => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;

// The call as a trace: one stroke per reading, the caller above the line and Ophi below it.
// Strokes keep their pixel width at any size, so the trace fills its column without thickening.
function Trace({ bars, className }: { bars: DemoCall["bars"]; className: string }) {
  const lane = (values: number[], side: 1 | -1) => values.map((v, i) => `M${i + .5} ${50 - side * 5}V${(50 - side * (5 + Math.max(.5, v * 42))).toFixed(1)}`).join("");
  return (
    <svg className={`pointer-events-none absolute inset-0 size-full ${className}`} viewBox={`0 0 ${bars.ophi.length} 100`} preserveAspectRatio="none" fill="none" strokeLinecap="round" aria-hidden="true">
      <path d={lane(bars.caller, 1)} className="stroke-sage-deep [stroke-width:2.5px] phone:[stroke-width:1.5px]" vectorEffect="non-scaling-stroke" />
      <path d={lane(bars.ophi, -1)} className="stroke-ink [stroke-width:2.5px] phone:[stroke-width:1.5px]" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

// The listening room: pick a recorded call, hear it, and read what Ophi did behind each line.
export function CallPlayer({ calls, note: provenance }: { calls: DemoCall[]; note: string }) {
  const [slug, setSlug] = useState(calls[0].slug);
  const [status, setStatus] = useState<Status>("idle");
  // Quarter-second steps: enough for the transcript to follow. The playhead moves every frame, outside React.
  const [time, setTime] = useState(0);
  const audio = useRef<HTMLAudioElement>(null);
  const trace = useRef<HTMLDivElement>(null);
  const scroller = useRef<HTMLOListElement>(null);
  const sheet = useRef<HTMLDivElement>(null);
  // Where playback is, or will start once the recording loads.
  const position = useRef(0);
  // Where the clock stood when play was pressed: "playing" means it has moved on from there.
  const pressedAt = useRef(0);
  const dragging = useRef(false);
  // The "Hear it" button that started this playback, so it can show itself as the one playing.
  const [source, setSource] = useState<string | null>(null);
  const call = calls.find((c) => c.slug === slug) ?? calls[0];
  const started = status !== "idle";
  const now = started ? call.turns.findLastIndex((turn) => turn.start <= time + .05) : -1;

  const paint = useCallback((seconds: number, length: number) => {
    position.current = seconds;
    trace.current?.style.setProperty("--p", String(Math.min(1, seconds / length)));
    setTime(Math.floor(seconds * 4) / 4);
  }, []);

  const live = status === "starting" || status === "loading" || status === "playing";
  const slow = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(slow.current), []);
  function awaitSound() {
    pressedAt.current = position.current;
    setStatus("starting");
    clearTimeout(slow.current);
    slow.current = setTimeout(() => setStatus((current) => current === "starting" ? "loading" : current), 500);
  }

  useEffect(() => {
    if (!live) return;
    let frame = requestAnimationFrame(function tick() {
      const el = audio.current;
      // Not while a new recording is still arriving: its clock reads zero until it knows where to start.
      if (el && el.readyState > 0 && !el.seeking && !dragging.current) {
        // Sound, not the browser's say-so, ends the wait: a speaker that is slow to wake still reads as loading.
        if (!el.paused && el.currentTime > pressedAt.current + .05) setStatus((current) => current === "starting" || current === "loading" ? "playing" : current);
        paint(el.currentTime, call.duration);
      }
      frame = requestAnimationFrame(tick);
    });
    return () => cancelAnimationFrame(frame);
  }, [live, call.duration, paint]);

  // The transcript follows the call, moving only its own column, never the page. A finished call rests on what it left the team.
  useEffect(() => {
    const list = scroller.current;
    const row = list?.querySelector<HTMLElement>("[data-now]");
    if (!list || !row) return;
    const top = status === "ended" ? list.scrollHeight : row.offsetTop - (list.clientHeight - row.offsetHeight) / 2;
    list.scrollTo({ top, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }, [now, slug, status]);

  // "Hear it" buttons show which of them is playing.
  useEffect(() => {
    window.dispatchEvent(new CustomEvent<NowDetail>(NOW_EVENT, { detail: { source: live ? source : null } }));
  }, [live, source]);

  function play(next: DemoCall, from?: number) {
    const el = audio.current;
    if (!el) return;
    if (next.slug !== slug || !el.getAttribute("src")) {
      // Set here, not by React: assigning src again, even unchanged, would restart the load.
      el.src = next.src;
      // The same call keeps wherever the trace was moved to before it first played.
      if (from === undefined) from = next.slug === slug ? position.current : 0;
      setSlug(next.slug);
      scroller.current?.scrollTo({ top: 0 });
    } else if (status === "error") {
      el.load();
    }
    if (from !== undefined) {
      const start = from;
      paint(start, next.duration);
      if (el.readyState > 0) el.currentTime = start;
      // A fresh recording already starts at zero; seeking there would only delay it.
      else if (start > 0) el.addEventListener("loadedmetadata", () => { el.currentTime = start; }, { once: true });
    }
    awaitSound();
    // A newer play() or pause() interrupting this one is not a failure.
    el.play().catch((error: Error) => { if (error.name !== "AbortError") setStatus("error"); });
  }

  // Bring the call sheet into view when the press that started a call came from somewhere it can't be seen.
  function reveal(always: boolean) {
    const el = sheet.current;
    if (!el) return;
    const box = el.getBoundingClientRect();
    const seen = box.top > -80 && box.top < innerHeight * .55;
    if (always || !seen) el.scrollIntoView({ block: box.height > innerHeight * .85 ? "start" : "center" });
  }

  // Presses inside the listening room. Whatever "Hear it" button was playing no longer is.
  function start(next: DemoCall, from?: number) {
    setSource(null);
    play(next, from);
  }

  function toggle() {
    if (live) audio.current?.pause();
    else start(call, status === "ended" ? 0 : undefined);
  }

  // "Hear it" buttons elsewhere on the page play the moment they describe, where the reader is.
  const hear = useEffectEvent((event: Event) => {
    const { slug: wanted, t, source: from, show } = (event as CustomEvent<HearDetail>).detail;
    const next = calls.find((c) => c.slug === wanted);
    if (!next) return;
    if (live && source === from) { audio.current?.pause(); return; }
    setSource(from);
    play(next, t);
    if (show) reveal(true);
  });
  useEffect(() => {
    window.addEventListener(HEAR_EVENT, hear);
    return () => window.removeEventListener(HEAR_EVENT, hear);
  }, []);

  const pointed = (event: PointerEvent<HTMLDivElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    return Math.min(1, Math.max(0, (event.clientX - box.left) / box.width)) * call.duration;
  };
  function scrub(event: KeyboardEvent<HTMLDivElement>) {
    const to = { ArrowLeft: position.current - 5, ArrowRight: position.current + 5, Home: 0, End: call.duration }[event.key];
    if (to === undefined) return;
    event.preventDefault();
    const seconds = Math.min(call.duration, Math.max(0, to));
    paint(seconds, call.duration);
    if (audio.current && audio.current.readyState > 0) audio.current.currentTime = seconds;
  }

  const line = {
    idle: `Recorded call · ${clock(call.duration)}`,
    starting: `${clock(time)} / ${clock(call.duration)}`,
    loading: "Loading the recording…",
    playing: `${clock(time)} / ${clock(call.duration)}`,
    paused: `Paused at ${clock(time)} / ${clock(call.duration)}`,
    ended: `Ended · ${clock(call.duration)}`,
    error: "Couldn’t load the recording. Check your connection and press play again.",
  }[status];
  const note = (text: string, t: number) => (
    <li key={`${t}-${text}`} className={`grid grid-cols-[52px_minmax(0,1fr)] gap-x-3 py-1.5 transition-opacity duration-300 phone:grid-cols-1 ${started && t > time ? "opacity-45" : ""}`}>
      <span className="sr-only">Ophi did:</span>
      <p className="col-start-2 flex w-fit items-center gap-2 rounded-[14px] bg-sage py-1 pr-3 pl-1.5 text-[12px] leading-[1.45] text-label phone:col-start-1 xray:text-ink-soft">
        <span className="grid size-[18px] flex-none place-items-center rounded-full bg-paper"><Icon name="check" className="size-3" /></span>{text}
      </p>
    </li>
  );

  return (
    // Side by side, the list sits under the heading. Stacked, the call sheet comes first: the play button is the point.
    <div className="grid grid-cols-[minmax(0,340px)_minmax(0,1fr)] grid-rows-[auto_1fr] gap-x-[5%] [grid-template-areas:'head_sheet'_'list_sheet'] tablet:grid-cols-1 tablet:grid-rows-none tablet:[grid-template-areas:'head'_'sheet'_'list']">
      <h2 id="listen-title" className="text-[length:clamp(34px,3.3vw,48px)] leading-[1.04] tracking-[-.04em] text-balance [grid-area:head] tablet:pb-7 phone:px-1.5 phone:pb-6">Don’t take our word for it. <em className="block">Listen.</em></h2>
      <div className="flex flex-col pt-8 [grid-area:list] tablet:pt-6 phone:pt-4">
        <ul className="call-list grid gap-1 tablet:grid-cols-2 tablet:gap-x-3 phone:grid-cols-1">
          {calls.map((c) => {
            const chosen = c.slug === call.slug;
            return (
              <li key={c.slug}>
                {/* Choosing a call plays it from the top: one press to hear it. */}
                <button type="button" aria-pressed={chosen} onClick={() => { start(c, 0); reveal(false); }} className="group/call flex w-full items-baseline gap-3 rounded-[20px] px-4 py-3 text-left transition-[background] duration-200 hover:bg-paper/55 aria-pressed:bg-paper">
                  <span className="min-w-0 flex-1">
                    <span className="block font-serif text-[19px] leading-[1.25] tracking-[-.3px]">{c.title}</span>
                    <span className="mt-1 block text-[12.5px] leading-[1.5] text-label xray:text-muted">{c.blurb}</span>
                  </span>
                  {/* Fixed width: "Playing" must not squeeze the words beside it onto another line. */}
                  <span className="w-[42px] flex-none text-right text-[11px] text-label tabular-nums xray:text-muted">{chosen && status === "playing" ? "Playing" : clock(c.duration)}</span>
                </button>
              </li>
            );
          })}
        </ul>
        <p className="mt-auto max-w-[330px] pt-6 text-[12px] leading-[1.6] text-label tablet:max-w-none phone:px-1.5 phone:pb-3 phone:text-pretty xray:text-muted">{provenance}</p>
      </div>
      <div ref={sheet} className="call-sheet flex min-w-0 scroll-mt-4 flex-col rounded-[28px] bg-paper p-7 [grid-area:sheet] phone:-mx-1.5 phone:rounded-[22px] phone:px-4 phone:py-5">
        <audio ref={audio} preload="none" onWaiting={awaitSound} onPause={(event) => { if (event.currentTarget.paused) setStatus((current) => current === "ended" || current === "error" ? current : "paused"); }} onEnded={() => { paint(call.duration, call.duration); setStatus("ended"); }} onError={() => setStatus("error")} />
        <noscript><audio controls preload="none" src={calls[0].src} className="mb-4 w-full" /></noscript>
        <div className="flex items-center gap-4.5 phone:gap-3.5">
          <button type="button" onClick={toggle} aria-label={`${live ? "Pause" : status === "ended" ? "Play again" : "Play"} the call: ${call.title}`} className="play-button grid size-[60px] flex-none place-items-center rounded-full bg-ink text-paper transition-[background,scale] duration-200 hover:bg-ink-soft active:scale-[.96] phone:size-[52px]">
            {status === "loading"
              // Words carry the wait when motion is off (the status line); the ring carries it otherwise.
              ? <span className="size-[22px] rounded-full border-2 border-paper/30 border-t-paper motion-safe:animate-spin" />
              : <Icon name={live ? "pause" : "play"} className={`size-[26px] ${live ? "[stroke-width:2]" : "translate-x-px"}`} />}
          </button>
          {/* Phones hold room for a two-line title, so switching calls never moves what's below the sheet. */}
          <div className="min-w-0 flex-1 phone:flex phone:min-h-[74px] phone:flex-col phone:justify-center">
            <h3 className="font-serif text-[24px] leading-[1.2] tracking-[-.5px] phone:text-[21px]">{call.title}</h3>
            <p className={`mt-1 text-[12px] leading-[1.5] tabular-nums ${status === "error" ? "text-error" : "text-muted"}`} role="status">{line}</p>
          </div>
        </div>
        <div className="mt-6 flex items-stretch gap-3 phone:mt-5 phone:gap-2">
          <div className="flex w-[52px] flex-none flex-col justify-between py-2.5 text-[11px] leading-none text-muted phone:w-11" aria-hidden="true"><span className="truncate">{call.caller}</span><span>Ophi</span></div>
          {/* Press or drag anywhere on the trace to hear the call from there. */}
          <div ref={trace} role="slider" tabIndex={0} aria-label="Position in the call" aria-valuemin={0} aria-valuemax={Math.round(call.duration)} aria-valuenow={Math.round(time)} aria-valuetext={`${clock(time)} of ${clock(call.duration)}`}
            className="call-trace relative h-[84px] min-w-0 flex-1 cursor-pointer touch-pan-y rounded-[10px] [--p:0] phone:h-[68px]" onKeyDown={scrub}
            onPointerDown={(event) => { event.currentTarget.setPointerCapture(event.pointerId); dragging.current = true; paint(pointed(event), call.duration); }}
            onPointerMove={(event) => { if (dragging.current) paint(pointed(event), call.duration); }}
            onPointerUp={(event) => { if (!dragging.current) return; dragging.current = false; start(call, pointed(event)); }}
            onPointerCancel={() => { dragging.current = false; }}>
            <Trace bars={call.bars} className="opacity-35" />
            <Trace bars={call.bars} className="[clip-path:inset(0_calc(100%-var(--p)*100%)_0_0)]" />
            <span className="pointer-events-none absolute inset-y-0 left-[calc(var(--p)*100%)] w-[1.5px] -translate-x-1/2 bg-orange" aria-hidden="true"><span className="absolute top-1/2 left-1/2 size-[7px] -translate-1/2 rounded-full bg-orange" /></span>
          </div>
        </div>
        {/* Legible in full before anything plays; once it does, what hasn't been said yet steps back.
            Lines fade at both edges of the column, so a scrolled line is never cut mid-letter. */}
        <ol ref={scroller} className="transcript relative min-h-[372px] flex-[1_1_0] overflow-y-auto pt-5 pb-14 [scrollbar-width:none] [mask-image:linear-gradient(transparent,#000_20px,#000_calc(100%-48px),transparent)] phone:min-h-[340px] phone:pt-4 [&::-webkit-scrollbar]:hidden" aria-label={`Transcript: ${call.title}`}>
          {call.turns.map((turn, i) => (
            <Fragment key={`${call.slug}-${i}`}>
              {call.notes.filter((n) => n.before === i).map((n) => note(n.text, n.t))}
              <li data-now={i === now || undefined} className={`grid grid-cols-[52px_minmax(0,1fr)_auto] gap-x-3 py-2 transition-opacity duration-300 phone:grid-cols-[minmax(0,1fr)_auto] ${started && turn.start > time ? "opacity-50" : ""}`}>
                <span className="pt-[5px] text-[11px] leading-[1.5] text-muted phone:col-span-2 phone:pt-0">{turn.who === "ophi" ? "Ophi" : call.caller}</span>
                <p className={turn.who === "ophi" ? "font-serif text-[19px] leading-[1.38] tracking-[-.2px] phone:text-[18px]" : "pt-[3px] text-[14px] leading-[1.6] text-ink-soft"}>{turn.text}</p>
                <button type="button" onClick={() => start(call, turn.start)} aria-label={`Play from ${clock(turn.start)}`} className="-mr-2 h-7 self-start rounded-full px-2 text-[11px] text-muted tabular-nums transition-[background,color] duration-200 hover:bg-sage hover:text-ink">{clock(turn.start)}</button>
              </li>
            </Fragment>
          ))}
          {call.notes.filter((n) => n.before === call.turns.length).map((n) => note(n.text, n.t))}
          {call.summary && (
            <li className={`grid grid-cols-[52px_minmax(0,1fr)] gap-x-3 pt-3 transition-opacity duration-300 phone:grid-cols-1 ${started && status !== "ended" && time < call.turns[call.turns.length - 1].end ? "opacity-50" : ""}`}>
              <div className="col-start-2 rounded-[18px] border border-line px-4 py-3.5 phone:col-start-1">
                <p className="text-[11px] text-muted">{copy.listen.summary}</p>
                <p className="mt-1 text-[13.5px] leading-[1.6] text-ink-soft">{call.summary}</p>
              </div>
            </li>
          )}
        </ol>
      </div>
    </div>
  );
}
