"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { AnimatePresence, MotionConfig, motion } from "motion/react";
import { copy } from "@/lib/copy";
import { REAL_CALL, STEPS, frameAt, lastBeat, type Frame, type Line } from "@/lib/story";
import { Icon } from "@/components/icons";
import { spring, settle, pop, glide, leave, usePrefersReduced, Swap, Voice, Bubble, Ping } from "@/components/motion";
import { Thread, toThread } from "@/components/thread";
import { useInView } from "@/components/use-in-view";
import css from "./crown-story.module.css";

const words = copy.story;
const CLINIC = copy.team.clinic;
// How long a finished moment stays on screen before the next begins.
const HOLD_MS = 3400;

// The page's motion language (as in the hero): things settle on springs, text glides, and what leaves goes quickly.


// Where a moment opens: at its first spoken line, so the phone is never blank while the reader waits.
const startBeat = (step: number) => (STEPS[step].door === "page" ? 0 : Math.max(0, STEPS[step].beats.findIndex((b) => b.say)));

// auto: the story plays itself, moment after moment. step: the reader picked a moment; it plays out and stays.
// paused: every moment shows as it ends.
type Mode = "auto" | "step" | "paused";

// One patient's crown, start to finish: pick a moment, watch it happen on Alex's phone. Under 900px the phone comes
// first and one moment shows at a time.
export function CrownStory() {
  const root = useRef<HTMLDivElement>(null);
  const audio = useRef<HTMLAudioElement>(null);
  const list = useRef<HTMLOListElement>(null);
  const seen = useInView(root, 0.3);
  const reduced = usePrefersReduced();
  const [mode, setMode] = useState<Mode>("auto");
  const [step, setStep] = useState(0);
  const [beat, setBeat] = useState(startBeat(0));
  // Seconds into the real recording while it plays.
  const [heard, setHeard] = useState<number | null>(null);

  const still = reduced || mode === "paused";
  const shownBeat = still ? lastBeat(step) : beat;
  const done = shownBeat >= lastBeat(step);
  const ended = step === STEPS.length - 1 && done;

  useEffect(() => {
    if (!seen || still || heard !== null) return;
    if (beat < lastBeat(step)) {
      const timer = setTimeout(() => setBeat(beat + 1), STEPS[step].beats[beat + 1].wait);
      return () => clearTimeout(timer);
    }
    if (mode !== "auto" || step === STEPS.length - 1) return;
    const timer = setTimeout(() => { setStep(step + 1); setBeat(startBeat(step + 1)); }, HOLD_MS);
    return () => clearTimeout(timer);
  }, [seen, still, heard, mode, step, beat]);

  // Each moment's rule opens to the height of the longest one, so the list (and the page under it) keeps one height
  // whichever moment is open.
  useLayoutEffect(() => {
    const ol = list.current;
    if (!ol) return;
    const fit = () => ol.style.setProperty("--proof", `${Math.max(...[...ol.querySelectorAll<HTMLElement>("[data-proof]")].map((el) => el.offsetHeight))}px`);
    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(ol);
    return () => observer.disconnect();
  }, []);

  function go(i: number) {
    setStep(i);
    setBeat(startBeat(i));
  }

  function choose(i: number) {
    audio.current?.pause();
    go(i);
    if (mode === "auto") setMode("step");
  }

  function toggle() {
    if (ended) { go(0); setMode("auto"); return; }
    if (mode === "auto") { setMode("paused"); return; }
    if (done && step < STEPS.length - 1) go(step + 1);
    else if (mode === "paused") setBeat(lastBeat(step));
    setMode("auto");
  }

  function listen() {
    const el = audio.current;
    if (!el) return;
    if (!el.paused) { el.pause(); return; }
    go(0);
    setBeat(lastBeat(0));
    if (mode === "auto") setMode("step");
    el.currentTime = 0;
    void el.play();
  }

  const frame = frameAt(step, shownBeat);
  const now = STEPS[step];
  const lines = heard === null ? frame.lines : REAL_CALL.turns.filter((turn) => turn.start <= heard);
  // Ophi is writing back: Alex has just texted and the reply is still to come.
  const typing = now.door === "text" && !done && lines.at(-1)?.who === "alex";
  // Only what the reader asked for is announced; the story playing itself stays quiet.
  const live = mode !== "auto" || heard !== null;
  const toggleLabel = ended ? "replay" : mode === "auto" ? "pause" : "play";

  return (
    <MotionConfig reducedMotion="user">
      {/* Off screen, the voices stop moving too. */}
      <div ref={root} className={`rounded-[36px] bg-deep p-[clamp(28px,3.6vw,52px)] text-on-deep [--mark-on:var(--deep)] [--mark:var(--on-deep)] phone:rounded-[28px] phone:px-5 phone:py-9 ${seen ? "" : "[&_*]:[animation-play-state:paused]"}`}>
        <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-[clamp(32px,5vw,80px)] gap-y-7 max-[899px]:grid-cols-1">
          <div className="max-[899px]:contents">
            <h2 id="story-title" className="font-serif text-[length:clamp(34px,3.4vw,48px)] leading-[1.05] tracking-[-.035em] text-balance max-[899px]:order-1">{words.title}</h2>
            <ol ref={list} className="mt-7 grid gap-1 max-[899px]:order-4 max-[899px]:mt-0">
              {STEPS.map((s, i) => {
                const active = i === step;
                const passed = i < step || (active && done);
                return (
                  <li key={s.when} className={css.moment} data-active={active || undefined} data-past={i < step || undefined}>
                    <button type="button" onClick={() => choose(i)} aria-current={active ? "step" : undefined}
                      className={`group/step relative grid w-full grid-cols-[28px_minmax(0,1fr)] gap-x-4 rounded-[18px] px-4 py-3 text-left transition-[background] duration-300 ${active ? "" : "hover:bg-on-deep/5"}`}>
                      {/* The current moment's surface glides from one moment to the next, its bar filling as it plays. */}
                      {active && (
                        <motion.span layoutId="story-moment" className="absolute inset-0 overflow-hidden bg-on-deep/10" style={{ borderRadius: 18 }} transition={spring} aria-hidden="true">
                          <motion.span className="absolute inset-x-0 bottom-0 h-[3px] origin-left bg-on-deep/60" initial={{ scaleX: 0 }} animate={{ scaleX: (shownBeat + 1) / s.beats.length }} transition={glide} />
                        </motion.span>
                      )}
                      <span className={`relative mt-0.5 grid size-7 place-items-center rounded-full border text-[14px] transition-[background,color,border-color] duration-500 ${passed ? "border-on-deep bg-on-deep text-deep" : "border-on-deep/40"}`}>{i + 1}</span>
                      <span className="relative">
                        <span className="block text-[14px] text-on-deep-soft">{s.when}</span>
                        <span className={`mt-0.5 block font-serif text-[20px] leading-[1.25] tracking-[-.01em] transition-[color] duration-500 ${active ? "text-on-deep" : "text-on-deep-soft"}`}>{s.title}</span>
                        {/* The rule Ophi kept in this moment: it opens under the current moment and brightens once the
                            moment is done. Narrow screens keep it open, so every moment is measured at full height. */}
                        <span className={`grid transition-[grid-template-rows,opacity] duration-500 ease-(--ease-out) motion-reduce:transition-opacity max-[899px]:grid-rows-[1fr] ${active ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"}`} aria-hidden={!active || undefined}>
                          <span className="min-h-0 overflow-hidden">
                            <span className="block min-h-(--proof)">
                              <span data-proof className={`flex items-center gap-2 pt-2 text-[15px] text-on-deep-soft transition-opacity duration-500 ${active && done ? "opacity-100" : "opacity-50"}`}>
                                <Icon name="check" className={`size-4 flex-none transition-colors duration-500 ${active && done ? "text-on-deep" : ""}`} />{s.proof}
                              </span>
                            </span>
                          </span>
                        </span>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ol>
            {/* Narrow screens show one moment at a time: these move between them. */}
            <div className="hidden items-center gap-1.5 max-[899px]:order-3 max-[899px]:-my-3 max-[899px]:flex">
              {STEPS.map((s, i) => (
                <button key={s.when} type="button" onClick={() => choose(i)} aria-label={`Moment ${i + 1}: ${s.title}`} aria-current={i === step ? "step" : undefined} className="grid h-11 flex-1 place-items-center">
                  <span className={`h-2 w-full rounded-full transition-[background] duration-500 ${i === step ? "bg-orange" : i < step ? "bg-on-deep" : "bg-on-deep/25"}`} />
                </button>
              ))}
            </div>
            <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-3 pl-4 max-[899px]:order-5 max-[899px]:mt-0 max-[899px]:pl-0">
              {!reduced && (
                <button type="button" onClick={toggle} className="flex min-h-11 items-center rounded-full border border-on-deep/30 px-4 text-[15px] [transition:background_.15s,scale_.16s_var(--ease-out)] hover:bg-on-deep/10 active:scale-[.97]">
                  <span className="flex items-center gap-2.5 whitespace-nowrap">
                    <Icon name={ended ? "up" : mode === "auto" ? "pause" : "play"} className={`size-4 ${ended ? "-rotate-90" : ""}`} />
                    {words[toggleLabel]}
                  </span>
                </button>
              )}
              <p className="text-[14px] leading-[1.5] text-on-deep-soft">{words.note}</p>
            </div>
          </div>

          <div className="flex flex-col items-center max-[899px]:order-2">
            <Phone moment={step} clock={now.clock} when={now.when} door={now.door} frame={frame} lines={lines} typing={typing} action={now.action} heard={heard} live={live} />
            <button type="button" onClick={listen} aria-pressed={heard !== null} className="mt-3 flex min-h-11 items-center rounded-full px-4 text-[15px] text-on-deep-soft [transition:background_.15s,color_.15s,scale_.16s_var(--ease-out)] hover:bg-on-deep/10 hover:text-on-deep active:scale-[.97]">
              <span className="flex items-center gap-2.5 whitespace-nowrap">
                <Icon name={heard === null ? "play" : "pause"} className="size-4" />{heard === null ? words.real : words.stop}
              </span>
            </button>
            <audio ref={audio} src={REAL_CALL.src} preload="none" onTimeUpdate={(event) => setHeard(event.currentTarget.paused ? null : event.currentTarget.currentTime)} onPause={() => setHeard(null)} onEnded={() => setHeard(null)} />
          </div>
        </div>
      </div>
    </MotionConfig>
  );
}

type PhoneProps = { moment: number; clock: string; when: string; door: string; frame: Frame; lines: Line[]; typing: boolean; action?: string; heard: number | null; live: boolean };

// Alex's phone, showing whichever door this moment comes through. It prints on paper, so its marks reset to ink.
function Phone({ moment, clock, when, door, frame, lines, typing, action, heard, live }: PhoneProps) {
  return (
    <div className="w-[310px] max-w-full rounded-[50px] bg-[#0d211b] p-2.5 shadow-[0_40px_80px_-30px_#000a] max-[899px]:w-[292px] phone:w-[270px]">
      <div className="relative flex h-[540px] flex-col overflow-hidden rounded-[41px] bg-paper text-ink [--mark-on:var(--paper)] [--mark:var(--ink)] max-[899px]:h-[470px] phone:h-[430px]">
        <div className="flex h-11 flex-none items-center justify-between px-7 text-[14px] font-medium">
          <Swap id={clock}>{clock}</Swap>
          <span className="absolute top-3 left-1/2 h-6 w-24 -translate-x-1/2 rounded-full bg-[#0d211b]" aria-hidden="true" />
          <span className="h-2.5 w-4 rounded-[3px] border border-ink/70" aria-hidden="true" />
        </div>
        {/* One moment hands over to the next: the old screen lifts away first, then the new one settles in, so the
            two never blur over each other. */}
        <div className="relative min-h-0 flex-1" aria-live={live ? "polite" : "off"}>
          <AnimatePresence mode="wait" initial={false}>
            <motion.div key={moment} className="absolute inset-0" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12, transition: leave }} transition={{ ...settle, opacity: { duration: 0.4 } }}>
              {door === "call" && <CallScreen lines={lines} heard={heard} />}
              {door === "text" && <TextScreen lines={lines} when={when} typing={typing} />}
              {door === "page" && <PageScreen frame={frame} action={action} />}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

// A call as live captions: the newest words sit just above the hang-up button. Each new line pushes the others up,
// and the oldest fades as it scrolls out under the top edge, so lines never stack on each other.
function CallScreen({ lines, heard }: { lines: Line[]; heard: number | null }) {
  const line = lines.at(-1);
  const recent = lines.slice(-3);
  const status = heard !== null ? "Real recording" : line ? copy.hero.onCall : copy.hero.calling;
  return (
    <div className="flex h-full flex-col px-6 pb-6 text-center max-[899px]:pb-5 phone:px-5">
      <p className="mt-4 font-serif text-[22px] leading-[1.2] tracking-[-.02em]">{CLINIC}</p>
      <p className="mt-1 flex items-center justify-center gap-1.5 text-[14px] text-muted"><Icon name="phone" className="size-4" /><Swap id={status}>{status}</Swap></p>
      <div className="mt-4"><Voice who={line?.who ?? null} bars={17} /></div>
      <div className="mt-3 flex min-h-0 flex-1 flex-col justify-end gap-3.5 overflow-hidden text-left [mask-image:linear-gradient(to_bottom,transparent,#000_40px)]">
        <AnimatePresence initial={false}>
          {recent.map(({ who, text }, i) => {
            const newest = i === recent.length - 1;
            return (
              <motion.div key={`${lines.length - recent.length + i}-${text.slice(0, 10)}`} layout="position" className="flex-none"
                initial={{ opacity: 0, y: 24 }} animate={{ opacity: newest ? 1 : 0.45, y: 0 }} exit={{ opacity: 0, transition: { duration: 0.3 } }}
                transition={{ ...settle, opacity: { duration: 0.35, delay: newest ? 0.15 : 0 } }}>
                <p className="text-[14px] text-muted">{who === "ophi" ? "Ophi" : "Alex"}</p>
                <p className={who === "ophi" ? "font-serif text-[18px] leading-[1.3] tracking-[-.01em]" : "text-[16px] leading-[1.45] text-ink-soft"}>{text}</p>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
      {/* Hang up: the one control a call screen always has. */}
      <span className="mx-auto mt-5 grid size-[52px] flex-none place-items-center rounded-full bg-rust text-paper max-[899px]:mt-4 max-[899px]:size-12" aria-hidden="true">
        <Icon name="phone" className="size-[22px] rotate-[135deg]" />
      </span>
    </div>
  );
}

// A text thread under its date. Each message springs up from its own corner; on shorter screens the newest stays in
// view and older ones scroll up and out of the top.
function TextScreen({ lines, when, typing }: { lines: Line[]; when: string; typing: boolean }) {
  return (
    <div className="flex h-full flex-col px-4 pb-5">
      <p className="flex flex-none items-center justify-center gap-2 text-[14px] text-muted"><Icon name="speech" className="size-4" />{CLINIC}</p>
      <div className="mt-4 flex min-h-0 flex-1 flex-col gap-2 overflow-hidden max-[899px]:justify-end max-[899px]:[mask-image:linear-gradient(to_bottom,transparent,#000_40px)]">
        <p className="mb-1 flex-none text-center text-[14px] text-muted">{when}</p>
        <AnimatePresence initial={false}>
          {lines.map(({ who, text }, i) => <Bubble key={`${i}-${text.slice(0, 10)}`} who={who}>{text}</Bubble>)}
          {typing && (
            <Bubble key="typing" who="ophi">
              <span className="flex h-[21px] items-center gap-1">
                {[0, 1, 2].map((d) => <motion.span key={d} className="size-[7px] rounded-full bg-ink/45" animate={{ y: [0, -3, 0], opacity: [0.5, 1, 0.5] }} transition={{ duration: 1, delay: d * 0.15, repeat: Infinity }} />)}
              </span>
            </Bubble>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// The personal page: the one thing to do now, then the whole thread, read from the same memory. The button gives
// under the tap, then turns into what it did.
function PageScreen({ frame, action }: { frame: Frame; action?: string }) {
  const tapped = frame.tap === "done";
  return (
    <div className="flex h-full flex-col overflow-hidden px-5 pb-5">
      <p className="flex flex-none items-center justify-center gap-1.5 text-[14px] text-muted"><Icon name="lock" className="size-4" />{CLINIC}</p>
      <p className="mt-4 font-serif text-[26px] leading-[1.1] tracking-[-.02em]">{words.page}</p>
      {action && (
        <motion.div className={`relative mt-4 flex min-h-11 flex-none items-center justify-center overflow-hidden rounded-full px-4 text-center text-[15px] font-medium transition-[background,color] duration-300 ${tapped ? "bg-ink text-paper" : frame.tap === "pressing" ? "bg-[#f59973]" : "bg-orange"}`}
          initial={false} animate={{ scale: frame.tap === "pressing" ? 0.95 : 1 }} transition={pop}>
          <AnimatePresence>
            {frame.tap === "pressing" && (
              <Ping key="ripple" from={0.3} className="top-1/2 left-1/2 -mt-7 -ml-7 size-14 bg-ink/20" />
            )}
          </AnimatePresence>
          <Swap id={tapped ? "done" : "do"} className="flex items-center gap-2">
            {tapped && <motion.span initial={{ scale: 0.4 }} animate={{ scale: 1 }} transition={{ ...pop, delay: 0.1 }}><Icon name="check" className="size-4" /></motion.span>}
            {tapped ? "Done" : action}
          </Swap>
        </motion.div>
      )}
      {/* A shorter phone can't fit the whole plan: the rest fades out at the bottom edge instead of being cut. */}
      <div className="mt-5 min-h-0 flex-1 overflow-hidden max-[899px]:[mask-image:linear-gradient(to_top,transparent,#000_36px)]">
        <Thread steps={toThread(frame.care)} size="sm" />
      </div>
    </div>
  );
}
