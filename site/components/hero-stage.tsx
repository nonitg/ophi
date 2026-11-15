"use client";

import { useEffect, useRef, useState, type PointerEvent, type ReactNode } from "react";
import { AnimatePresence, MotionConfig, motion, useMotionValue, useSpring, useTransform, type MotionValue } from "motion/react";
import { copy } from "@/lib/copy";
import { MOMENTS, lastHeroBeat, shownAt, type HeroRow, type Said } from "@/lib/hero";
import { CareMark } from "@/components/care-mark";
import { Icon } from "@/components/icons";
import { settle, pop, leave, usePrefersReduced, Swap, Voice, Bubble, Ping } from "@/components/motion";
import { useInView } from "@/components/use-in-view";

const words = copy.hero;
const CLINIC = copy.team.clinic;
// How long a finished conversation stays before the next patient's begins.
const HOLD_MS = 3600;
const runMs = (i: number) => MOMENTS[i].beats.slice(1).reduce((sum, { wait }) => sum + wait, 0) + HOLD_MS;
const firstName = (name: string) => name.split(" ")[0];
const clockOf = (when: string) => when.match(/\d{1,2}:\d{2}/)?.[0] ?? "9:41";

const finePointer = () => matchMedia("(pointer: fine)").matches;

// One feel for everything that arrives: a soft spring that settles without bounce, and a pop for what's tapped.

// The hero's picture of the product: the patient's phone, and floating over its edge what Ophi read from the clinic's
// records and what it wrote back. Three patients take turns, one per door (call, text, their page): the same
// assistant for every patient.
export function HeroStage() {
  const root = useRef<HTMLDivElement>(null);
  const seen = useInView(root, 0.3);
  // Wholly off screen, its voice bars stop too: left running, they keep a phone's main thread busy below the fold.
  const onScreen = useInView(root, 0, false, true);
  const [hovered, setHovered] = useState(false);
  const m = useMoments(seen, hovered);
  const { sx, sy, move, reset } = useParallax(m.reduced);
  const back = useDepth(sx, sy, -6);
  const phone = useDepth(sx, sy, 6);
  const front = useDepth(sx, sy, 15);

  return (
    <MotionConfig reducedMotion="user">
      <div ref={root} className={`relative mx-auto h-[620px] w-full max-w-[560px] phone:flex phone:h-[682px] phone:flex-col small:h-[702px] tiny:h-[716px] ${onScreen ? "" : "[&_*]:[animation-play-state:paused]"}`} onPointerEnter={() => setHovered(true)} onPointerLeave={() => { setHovered(false); reset(); }} onPointerMove={move}>
        <p className="sr-only">{`${m.name} reaches the clinic by ${words.channel[m.door].toLowerCase()}. Ophi answers from ${m.name}’s care in your records, then: ${m.did}.`}</p>

        {/* A soft disc of light under the phone. */}
        <motion.div style={back} className="absolute top-[30px] right-[-24px] size-[560px] rounded-full bg-[radial-gradient(circle_at_50%_40%,#ecefe2_0%,var(--sage)_62%,#dde2d0_100%)] phone:top-[10px] phone:right-1/2 phone:size-[440px] phone:translate-x-1/2" aria-hidden="true" />

        {/* The patient's phone: on the right, or on top in one narrow column, with the cards tucked under it in turn. */}
        <motion.div style={phone} className="absolute top-0 right-0 phone:relative phone:self-center" aria-hidden="true">
          <Phone m={m} />
          <Dots step={m.step} progress={m.progress} className="mt-5 flex phone:hidden" />
        </motion.div>

        {/* What Ophi read, and what it wrote back: in front of the phone, over its left edge (under it on phones). */}
        <motion.div style={front} className="absolute top-[112px] right-[262px] w-[296px] phone:relative phone:top-auto phone:right-auto phone:-mt-5 phone:w-[min(296px,calc(100%-28px))]" aria-hidden="true">
          <CareCard m={m} />
        </motion.div>
        <motion.div style={front} className="absolute top-[436px] right-[266px] phone:relative phone:top-auto phone:right-auto phone:-mt-3 phone:self-end" aria-hidden="true">
          <Toast m={m} />
        </motion.div>
        {/* One column: whose turn it is sits at the foot of the stage, under the cards. */}
        <Dots step={m.step} progress={m.progress} className="mt-auto hidden phone:flex" />
      </div>
    </MotionConfig>
  );
}

// Which patient is on, and how far their conversation has got.
function useMoments(seen: boolean, hovered: boolean) {
  const reduced = usePrefersReduced();
  const [step, setStep] = useState(0);
  const [beat, setBeat] = useState(0);
  const moment = MOMENTS[step];
  const playing = seen && !reduced;
  const finished = beat === lastHeroBeat(MOMENTS[step]);

  useEffect(() => {
    if (!playing) return;
    if (!finished) {
      const timer = setTimeout(() => setBeat(beat + 1), MOMENTS[step].beats[beat + 1].wait);
      return () => clearTimeout(timer);
    }
    // A finished conversation waits while the pointer rests on it, so it can be read.
    if (hovered) return;
    const timer = setTimeout(() => { setStep((step + 1) % MOMENTS.length); setBeat(0); }, HOLD_MS);
    return () => clearTimeout(timer);
  }, [playing, finished, hovered, step, beat]);

  return {
    moment, reduced, step,
    shown: shownAt(moment, reduced ? lastHeroBeat(moment) : beat),
    when: moment.when,
    door: moment.door,
    name: firstName(moment.name),
    key: moment.id,
    did: moment.did,
    clock: clockOf(moment.when),
    progress: { ms: runMs(step), running: playing && !(hovered && finished), show: !reduced },
  };
}
type M = ReturnType<typeof useMoments>;

// Pointer parallax: each layer drifts by its own depth, so the stage reads as objects in space. Mouse only.
function useParallax(reduced: boolean) {
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const sx = useSpring(x, { stiffness: 80, damping: 20 });
  const sy = useSpring(y, { stiffness: 80, damping: 20 });
  const move = (event: PointerEvent<HTMLElement>) => {
    if (reduced || event.pointerType !== "mouse" || !finePointer()) return;
    const box = event.currentTarget.getBoundingClientRect();
    x.set(((event.clientX - box.left) / box.width - 0.5) * 2);
    y.set(((event.clientY - box.top) / box.height - 0.5) * 2);
  };
  const reset = () => { x.set(0); y.set(0); };
  return { sx, sy, move, reset };
}

function useDepth(sx: MotionValue<number>, sy: MotionValue<number>, depth: number) {
  return { x: useTransform(sx, (v) => v * depth), y: useTransform(sy, (v) => v * depth) };
}

// The patient's phone. The clinic stays at the top; the screen under it hands over from one door to the next.
function Phone({ m }: { m: M }) {
  const status = m.door === "call" ? (m.shown.lines.length ? words.onCall : words.calling) : m.door === "text" ? words.channel.text : words.page(m.name);
  return (
    <div className="w-[288px] rounded-[52px] bg-[#0d211b] p-[11px] shadow-[0_2px_4px_#0d211b33,0_40px_80px_-30px_#0d211b99,0_80px_120px_-60px_#193a3066] phone:w-[262px] phone:rounded-[46px] phone:p-[9px]">
      <div className="relative flex h-[556px] flex-col overflow-hidden rounded-[42px] bg-paper text-ink [--mark-on:var(--paper)] [--mark:var(--ink)] phone:h-[420px] phone:rounded-[38px]">
        <div className="relative flex h-12 flex-none items-center justify-between px-8 text-[14px] font-medium">
          <Swap id={m.clock} className="tabular-nums">{m.clock}</Swap>
          <span className="absolute top-3 left-1/2 h-[26px] w-[92px] -translate-x-1/2 rounded-full bg-[#0d211b]" />
          <span className="h-2.5 w-4 rounded-[3px] border border-ink/70" />
        </div>

        <div className="flex flex-none flex-col items-center px-5 pt-2 text-center">
          <span className="grid size-[52px] place-items-center rounded-full bg-ink font-serif text-[23px] text-paper phone:size-11 phone:text-[20px]">{CLINIC[0]}</span>
          <p className="mt-2 text-[16px] font-medium">{CLINIC}</p>
          <Swap id={status} className="mt-0.5 block text-[14px] text-muted">{status}</Swap>
        </div>

        <div className="relative min-h-0 flex-1">
          {/* One door hands over to the next: the old screen lifts away first, then the new one settles in, so the
              two never blur over each other. */}
          <AnimatePresence mode="wait" initial={false}>
            <motion.div key={m.key} className="absolute inset-0 flex flex-col"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12, transition: leave }}
              transition={{ ...settle, opacity: { duration: 0.4 } }}>
              {m.door === "call" ? <CallScreen lines={m.shown.lines} name={m.name} />
                : m.door === "text" ? <TextScreen lines={m.shown.lines} when={m.when} typing={m.shown.rows.length > 0 && !m.shown.lines.some(({ who }) => who === "ophi")} />
                : <PageScreen m={m} />}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

// A call as live captions: the newest words sit just above the hang-up button. Each new line pushes the others up,
// and the oldest fades as it scrolls out under the top edge, so lines never stack on each other.
function CallScreen({ lines, name }: { lines: Said[]; name: string }) {
  const recent = lines.slice(-3);
  return (
    <div className="flex h-full flex-col px-6 pt-4 pb-6 phone:px-5 phone:pt-3 phone:pb-5">
      <Voice who={lines.at(-1)?.who ?? null} />
      <div className="mt-4 flex min-h-0 flex-1 flex-col justify-end gap-3.5 overflow-hidden [mask-image:linear-gradient(to_bottom,transparent,#000_40px)]">
        <AnimatePresence initial={false}>
          {recent.map(({ who, text }, i) => {
            const newest = i === recent.length - 1;
            return (
              <motion.div key={`${lines.length - recent.length + i}-${text.slice(0, 10)}`} layout="position" className="flex-none"
                initial={{ opacity: 0, y: 24 }} animate={{ opacity: newest ? 1 : 0.45, y: 0 }} exit={{ opacity: 0, transition: { duration: 0.3 } }}
                transition={{ ...settle, opacity: { duration: 0.35, delay: newest ? 0.15 : 0 } }}>
                <p className="text-[14px] text-muted">{who === "ophi" ? words.ophi : name}</p>
                <p className={who === "ophi" ? "font-serif text-[19px] leading-[1.3] tracking-[-.01em] phone:text-[18px]" : "text-[16px] leading-[1.45] text-ink-soft"}>{text}</p>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
      {/* Hang up: the one control a call screen always has. */}
      <span className="mx-auto mt-6 grid size-[52px] flex-none place-items-center rounded-full bg-rust text-paper phone:mt-4 phone:size-12">
        <Icon name="phone" className="size-[22px] rotate-[135deg]" />
      </span>
    </div>
  );
}

// A text thread under its date. On a phone's shorter screen the newest bubble stays in view and older ones scroll
// up and out of the top.
function TextScreen({ lines, when, typing }: { lines: Said[]; when: string; typing: boolean }) {
  return (
    <div className="flex h-full flex-col px-4 pt-3 pb-5 phone:pb-4">
      <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-hidden phone:justify-end phone:[mask-image:linear-gradient(to_bottom,transparent,#000_48px)]">
        <p className="mb-1 flex-none text-center text-[14px] text-muted">{when}</p>
        <AnimatePresence initial={false}>
          {lines.map(({ who, text }, i) => <Bubble key={`${i}-${text.slice(0, 10)}`} who={who}>{text}</Bubble>)}
          {typing && (
            <Bubble key="typing" who="ophi">
              <span className="flex h-[22px] items-center gap-1">
                {[0, 1, 2].map((d) => <motion.span key={d} className="size-[7px] rounded-full bg-ink/45" animate={{ y: [0, -3, 0], opacity: [0.5, 1, 0.5] }} transition={{ duration: 1, delay: d * 0.15, repeat: Infinity }} />)}
              </span>
            </Bubble>
          )}
        </AnimatePresence>
      </div>
      <span className="mt-3 flex h-11 flex-none items-center justify-between rounded-full bg-sage pr-1.5 pl-4 text-[14px] text-label">
        {words.compose}<span className="grid size-8 place-items-center rounded-full bg-ink/15 text-paper"><Icon name="up" className="size-4" /></span>
      </span>
    </div>
  );
}

// The patient's own page: Ophi's one message, the time it offers, and the one button that books it.
function PageScreen({ m }: { m: M }) {
  const page = m.moment.page!;
  const tap = m.shown.tap;
  return (
    <div className="flex h-full flex-col px-5 pt-4 pb-6 phone:px-4 phone:pt-2 phone:pb-4">
      <div className="flex min-h-0 flex-1 flex-col justify-center">
        <div className="rounded-[24px] bg-sage px-4.5 pt-5 pb-4.5 phone:rounded-[20px] phone:px-3.5 phone:pt-4 phone:pb-3.5">
          <p className="font-serif text-[21px] leading-[1.25] tracking-[-.015em] phone:text-[17px]">{page.text}</p>
          <p className="mt-4 rounded-[14px] bg-card px-3.5 py-2.5 text-center text-[15px] font-medium whitespace-nowrap phone:mt-3 phone:py-2">{page.slot}</p>
          <div className="relative mt-3 phone:mt-2">
            <motion.span animate={{ scale: tap === "pressing" ? 0.95 : 1, backgroundColor: tap === "done" ? "#193a30" : tap === "pressing" ? "#f59973" : "#ef865b", color: tap === "done" ? "#f4f2e9" : "#193a30" }} transition={pop}
              className="flex min-h-12 items-center justify-center rounded-full px-4 text-center text-[15px] font-medium phone:min-h-11">
              <Swap id={tap === "done" ? "done" : "ask"} className="flex items-center gap-2">{tap === "done" && <Icon name="check" className="size-4" />}{tap === "done" ? page.done : page.action}</Swap>
            </motion.span>
            {/* The patient's tap, as a ripple from the middle of the button. */}
            <AnimatePresence>
              {tap === "pressing" && (
                <Ping key="ripple" from={0.3} className="top-1/2 left-1/2 -mt-7 -ml-7 size-14 bg-ink/20" />
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
      {/* Phones' shorter screen keeps the room for the message; the page's own line says it's theirs. */}
      <p className="mt-4 flex items-center justify-center gap-1.5 text-[14px] text-muted phone:hidden"><Icon name="lock" className="size-4" />{words.noLogin}</p>
    </div>
  );
}

// Grows and shrinks to fit what's inside, instead of jumping. A CSS transition, not a motion one: motion measures
// height animations by scrolling the window, which can throw the page down mid-read.
function AutoHeight({ children }: { children: ReactNode }) {
  const inner = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState<number>();
  useEffect(() => {
    const el = inner.current;
    if (!el) return;
    const observer = new ResizeObserver(() => setHeight(el.offsetHeight));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return <div className="overflow-hidden transition-[height] duration-500 ease-(--ease-out) motion-reduce:transition-none" style={{ height }}><div ref={inner}>{children}</div></div>;
}

// What Ophi read from the clinic's records about this patient: reading first, then the rows as they land.
function CareCard({ m }: { m: M }) {
  const rows = m.shown.rows;
  const next = rows.findIndex(({ state }) => state !== "done");
  const reading = rows.length === 0;
  return (
    <div className="rounded-[26px] bg-card px-5 pt-4.5 pb-5 shadow-[0_1px_2px_#193a3014,0_18px_40px_-14px_#193a3038,0_50px_90px_-50px_#193a3055] phone:rounded-[22px] phone:px-4 phone:pt-4 phone:pb-4">
      <p className="flex items-center gap-2 text-[14px] text-label"><Icon name="records" className="size-4 flex-none" /><Swap id={m.name}>{words.record(m.name)}</Swap></p>
      <AutoHeight>
        {/* One patient's rows leave together before the next patient's reading begins. */}
        <AnimatePresence mode="wait" initial={false}>
          <motion.div key={m.key} className="pt-3.5" exit={{ opacity: 0, filter: "blur(4px)", transition: { duration: 0.3 } }}>
            <AnimatePresence initial={false}>
              {reading && (
                <motion.div key="reading" className="grid gap-3.5" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, transition: { duration: 0.15 } }}>
                  {[74, 52].map((w, i) => (
                    <div key={w} className="flex items-center gap-3">
                      <span className="size-[18px] flex-none rounded-full bg-sage" />
                      <motion.span className="h-3.5 rounded-full bg-sage" style={{ width: `${w}%` }} animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 1.1, delay: i * 0.18, repeat: Infinity }} />
                    </div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
            {rows.map((row, i) => <Row key={row.label} row={row} next={i === next} last={i === rows.length - 1} index={i} />)}
          </motion.div>
        </AnimatePresence>
      </AutoHeight>
    </div>
  );
}

function Row({ row, next, last, index }: { row: HeroRow; next: boolean; last: boolean; index: number }) {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ ...settle, delay: index * 0.09 }}
      className={`relative grid grid-cols-[18px_minmax(0,1fr)] gap-x-3 ${last ? "" : "pb-3.5"}`}>
      {!last && <span className="absolute top-[24px] bottom-[2px] left-[8px] w-[2px] rounded-full bg-line" />}
      <CareMark state={row.state} className="mt-[2px]" />
      <div className="grid min-w-0 justify-items-start gap-1">
        <span className="text-[15px] leading-[1.35] text-ink">{row.label}</span>
        <Swap id={row.note} className={`text-[14px] leading-[1.35] ${next ? "rounded-[12px] bg-orange/25 px-2.5 py-0.5 font-medium text-ink" : "text-muted"}`}>{row.note}</Swap>
      </div>
    </motion.div>
  );
}

// What Ophi wrote back to the clinic's records, springing in the moment it's done.
function Toast({ m }: { m: M }) {
  return (
    <div className="min-h-[64px] w-[292px] phone:w-[250px]">
      <AnimatePresence>
        {m.shown.did && (
          <motion.div key={m.key} initial={{ opacity: 0, y: 18, scale: 0.9 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 8, scale: 0.96, transition: { duration: 0.25 } }} transition={pop}
            className="flex items-start gap-3 rounded-[20px] bg-ink px-4 py-3.5 text-paper shadow-[0_18px_40px_-14px_#193a3066]">
            <motion.span initial={{ scale: 0.4 }} animate={{ scale: 1 }} transition={{ ...pop, delay: 0.1 }} className="mt-px grid size-[22px] flex-none place-items-center rounded-full bg-orange text-ink">
              <Icon name="check" className="size-4 [stroke-width:2.2]" />
            </motion.span>
            <span className="text-[15px] leading-[1.4]">{m.did}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Three patients, one assistant: whose turn it is, and how long until the next.
function Dots({ step, progress, className }: { step: number; progress: M["progress"]; className: string }) {
  return (
    <div className={`justify-center gap-2 ${className}`} aria-hidden="true">
      {MOMENTS.map(({ id }, i) => {
        const active = i === step;
        return (
          <motion.span key={id} layout transition={settle} className={`relative h-2 overflow-hidden ${active ? "w-8 bg-ink/15" : "w-2 bg-ink/20"}`} style={{ borderRadius: 4 }}>
            {active && progress.show && (
              <span key={step} className="absolute inset-0 origin-left rounded-full bg-ink/55 motion-safe:animate-[fill-x_linear_both]" style={{ animationDuration: `${progress.ms}ms`, animationPlayState: progress.running ? "running" : "paused" }} />
            )}
          </motion.span>
        );
      })}
    </div>
  );
}
