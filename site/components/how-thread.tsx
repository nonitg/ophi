"use client";

import { useEffect, useLayoutEffect, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { AnimatePresence, MotionConfig, motion } from "motion/react";
import { animate } from "motion";
import { STEPS, frameAt, lastBeat, type CareId, type CareItem, type CareState } from "@/lib/story";
import { Icon, type IconName } from "@/components/icons";
import { spring, settle, soft, usePrefersReduced, Ping, Voice } from "@/components/motion";
import { CareMark } from "@/components/care-mark";
import { title as titleType } from "@/components/type";
import { useInView } from "@/components/use-in-view";
import { copy } from "@/lib/copy";

// How Ophi works, as one patient's care: Alex's crown, from the plan to the fitting. Each moment a different door
// changes it (their page, the clinic's records, a text, a call), and each lands in the same timeline. Every state
// comes from lib/story.ts, so the dates match the hero and the story.

type Door = "page" | "records" | "text" | "call";
type Phase = "reset" | "arrive" | "ask" | "answer" | "fold" | "land";
type Moment = { door: Door; side: "left" | "right"; date: string; target: CareId; from: CareItem[]; to: CareItem[] };

const doorIcon: Record<Door, IconName> = { page: "page", records: "records", text: "speech", call: "phone" };
const words = copy.how;
const DOORS: Door[] = ["call", "text", "page", "records"];
const SHOWN: CareId[] = ["cleaning", "prep", "estimate", "lab", "fitting"];
const pick = (care: CareItem[]) => SHOWN.map((id) => care.find((c) => c.id === id)!);
const at = (step: number, beat: number) => pick(frameAt(step, beat).care);

// The crown, the day the plan landed, then four doors in turn.
const MOMENTS: Moment[] = [
  { door: "page", side: "left", date: "Tue, Nov 10", target: "prep", from: at(2, 0), to: at(2, lastBeat(2)) },
  { door: "records", side: "right", date: "Tue, Dec 1", target: "estimate", from: at(2, lastBeat(2)), to: at(3, 0) },
  { door: "text", side: "left", date: "Tue, Dec 1", target: "fitting", from: at(3, 0), to: at(3, lastBeat(3)) },
  { door: "call", side: "right", date: "Wed, Dec 2", target: "fitting", from: at(3, lastBeat(3)), to: at(4, lastBeat(4)) },
];
// The cleaning was booked by phone, after hours (the story's first call).
const START_VIA: Partial<Record<CareId, Door[]>> = { cleaning: ["call"] };

const ORDER: Phase[] = ["arrive", "ask", "answer", "fold", "land"];
const MS: Record<Phase, number> = { reset: 500, arrive: 600, ask: 900, answer: 1300, fold: 450, land: 1600 };
type Clock = { m: number; phase: Phase };
const next = ({ m, phase }: Clock): Clock => {
  if (phase === "reset") return { m: 0, phase: "arrive" };
  const i = ORDER.indexOf(phase);
  if (i < ORDER.length - 1) return { m, phase: ORDER[i + 1] };
  return m < MOMENTS.length - 1 ? { m: m + 1, phase: "arrive" } : { m: 0, phase: "reset" };
};
const reached = (phase: Phase, step: Phase) => ORDER.indexOf(phase) >= ORDER.indexOf(step);

// Alex's care at a point in the loop: everything else that moved since the last moment is already in; the door's own
// change lands when the fragment folds into the timeline.
function rowsAt({ m, phase }: Clock): CareItem[] {
  if (phase === "reset") return MOMENTS[0].from;
  const now = MOMENTS[m];
  if (phase === "land") return now.to;
  return now.to.map((row) => (row.id === now.target ? now.from.find(({ id }) => id === row.id)! : row));
}

// Which doors have touched each step so far: the door that changed it, or the records for a change no one asked for.
function viaAt({ m, phase }: Clock): Partial<Record<CareId, Door[]>> {
  const via: Partial<Record<CareId, Door[]>> = Object.fromEntries(Object.entries(START_VIA).map(([k, v]) => [k, [...v]]));
  if (phase === "reset") return via;
  MOMENTS.slice(0, m + 1).forEach((moment, i) => {
    moment.to.forEach((row) => {
      const before = moment.from.find(({ id }) => id === row.id)!;
      if (row.id !== moment.target && (before.state !== row.state || before.note !== row.note) && !via[row.id]) via[row.id] = ["records"];
    });
    if (i < m || phase === "land") {
      const list = (via[moment.target] ??= []);
      if (list.at(-1) !== moment.door) list.push(moment.door);
    }
  });
  return via;
}

const WIDE = "(min-width: 1240px)";
const subscribeWide = (fn: () => void) => {
  const q = matchMedia(WIDE);
  q.addEventListener("change", fn);
  return () => q.removeEventListener("change", fn);
};
const isWide = () => matchMedia(WIDE).matches;


export function HowThread() {
  const root = useRef<HTMLDivElement>(null);
  const fold = useRef<HTMLDivElement>(null);
  const marks = useRef<Partial<Record<CareId, HTMLElement | null>>>({});
  const notes = useRef<Partial<Record<CareId, HTMLElement | null>>>({});
  const seen = useInView(root, 0.2);
  const reduced = usePrefersReduced();
  const wide = useSyncExternalStore(subscribeWide, isWide, () => true);
  const [clock, setClock] = useState<Clock>({ m: 0, phase: "reset" });

  const playing = seen && !reduced;
  const shown: Clock = reduced ? { m: MOMENTS.length - 1, phase: "answer" } : clock;
  const moment = MOMENTS[shown.m];
  const rows = reduced ? MOMENTS[MOMENTS.length - 1].to : rowsAt(shown);
  const via = reduced ? viaAt({ m: MOMENTS.length - 1, phase: "land" }) : viaAt(shown);
  const fragment = shown.phase !== "reset" && shown.phase !== "land";
  const lastDone = rows.reduce((last, { state }, i) => (state === "done" ? i : last), 0);

  useEffect(() => {
    if (!playing) return;
    const timer = setTimeout(() => setClock(next(clock)), MS[clock.phase]);
    return () => clearTimeout(timer);
  }, [playing, clock]);

  // Wide screens dock each fragment beside the step it changes.
  useLayoutEffect(() => {
    const place = () => {
      const box = root.current?.getBoundingClientRect();
      const mark = marks.current[moment.target]?.getBoundingClientRect();
      if (box && mark) root.current!.style.setProperty("--row-y", `${mark.top + mark.height / 2 - box.top}px`);
    };
    place();
    const observer = new ResizeObserver(place);
    if (root.current) observer.observe(root.current);
    return () => observer.disconnect();
  }, [moment.target]);

  // The fragment folds into the timeline: into the step's mark from the left, into its note from the right.
  useEffect(() => {
    const el = fold.current;
    if (shown.phase !== "fold" || !el) return;
    const into = (wide && moment.side === "left" ? marks : notes).current[moment.target]?.getBoundingClientRect();
    const from = el.getBoundingClientRect();
    if (!into) return;
    const x = into.left + into.width / 2 - (from.left + from.width / 2);
    const y = into.top + into.height / 2 - (from.top + from.height / 2);
    animate(el, { x, y, scale: 0.16, opacity: 0, filter: "blur(6px)" }, { duration: MS.fold / 1000, ease: [0.77, 0, 0.175, 1] });
  }, [shown.phase, moment, wide]);

  const enterFrom = wide ? { x: moment.side === "left" ? -110 : 110, y: 36, rotate: moment.side === "left" ? -3 : 3 } : { x: 0, y: 48, rotate: 0 };

  return (
    <MotionConfig reducedMotion="user">
      <div ref={root} className={`relative mt-16 phone:mt-10 ${playing ? "" : "[&_*]:[animation-play-state:paused]"}`}>
        {/* Below the widest layout, fragments arrive in this space above the card, then fall into it. Between them, the
            doors wait here, the last one used still lit. */}
        <div className="relative grid h-[300px] place-items-center min-[1240px]:hidden" aria-hidden="true">
          <motion.ul className="flex gap-2.5" animate={{ opacity: fragment ? 0 : 1, scale: fragment ? 0.94 : 1, filter: fragment ? "blur(4px)" : "blur(0px)" }} transition={soft}>
            {DOORS.map((door) => {
              const lit = door === moment.door && shown.phase !== "reset";
              return (
                <li key={door} className="grid justify-items-center gap-2">
                  <span className={`grid size-14 place-items-center rounded-full transition-[background,color,box-shadow] duration-500 ${lit ? "bg-ink text-paper shadow-[0_8px_20px_-8px_#193a3066]" : "bg-card text-ink-soft shadow-[0_1px_2px_#193a301a,0_4px_12px_-4px_#193a301f]"}`}><Icon name={doorIcon[door]} className="size-[22px]" /></span>
                  <span className={`text-[14px] transition-[color] duration-500 ${lit ? "text-ink" : "text-muted"}`}>{words.doors[door]}</span>
                </li>
              );
            })}
          </motion.ul>
        </div>

        <div className="relative mx-auto w-full max-w-[680px] rounded-[36px] bg-card px-10 pt-9 pb-8 shadow-[0_1px_2px_#193a300d,0_24px_48px_-20px_#193a302e,0_80px_120px_-60px_#193a3040] phone:rounded-[28px] phone:px-5 phone:pt-6 phone:pb-5" aria-hidden="true">
          <div className="flex items-center justify-between gap-4">
            <div className="flex min-w-0 items-center gap-4 phone:gap-3">
              <span className="grid size-14 flex-none place-items-center rounded-full bg-sage font-serif text-[26px] phone:hidden">A</span>
              <div className="min-w-0">
                <p className="font-serif text-[30px] leading-[1.1] tracking-[-.02em] phone:text-[24px]">{words.care}</p>
                <p className="mt-0.5 text-[15px] text-muted">{words.plan}</p>
              </div>
            </div>
            <span className="flex h-10 flex-none items-center gap-2 overflow-hidden rounded-full bg-paper px-4 text-[15px] text-ink-soft phone:h-9 phone:px-3">
              <Icon name="calendar" className="size-4 flex-none" />
              <span className="relative grid">
                <AnimatePresence mode="popLayout" initial={false}>
                  <motion.span key={moment.date + (shown.phase === "reset" ? "r" : "")} initial={{ y: 14, opacity: 0, filter: "blur(3px)" }} animate={{ y: 0, opacity: 1, filter: "blur(0px)" }} exit={{ y: -14, opacity: 0, filter: "blur(3px)" }} transition={soft} className="whitespace-nowrap">
                    {shown.phase === "reset" ? MOMENTS[0].date : moment.date}
                  </motion.span>
                </AnimatePresence>
              </span>
            </span>
          </div>

          <ol className="relative mt-7 phone:mt-5">
            {/* The thread: drawn in ink as far as the care is done. */}
            <span className="absolute top-[39px] bottom-[39px] left-[13px] w-[2px] rounded-full bg-line phone:top-[40px] phone:bottom-[40px]" />
            <motion.span className="absolute top-[39px] bottom-[39px] left-[13px] w-[2px] origin-top rounded-full bg-ink phone:top-[40px] phone:bottom-[40px]" animate={{ scaleY: lastDone / (rows.length - 1) }} transition={settle} />
            {rows.map((row, i) => {
              const target = row.id === moment.target && shown.phase !== "reset";
              const nextStep = i === rows.findIndex(({ state }) => state !== "done");
              return (
                <li key={row.id} className="relative grid h-[78px] grid-cols-[28px_minmax(0,1fr)_auto] items-center gap-x-5 phone:h-20 phone:grid-cols-[28px_minmax(0,1fr)] phone:gap-x-4">
                  {target && <motion.span layoutId="how-row" className="absolute -inset-x-4 inset-y-1 rounded-[20px] bg-sage/70 phone:-inset-x-2.5" transition={spring} />}
                  <span ref={(el) => { marks.current[row.id] = el; }} className="relative"><Mark state={row.state} pulse={target && shown.phase === "land"} /></span>
                  <span className={`relative ${titleType} truncate phone:text-[20px]`}>{row.label}</span>
                  <span className="relative flex items-center justify-end gap-3 phone:col-start-2 phone:-mt-3 phone:justify-start">
                    <span ref={(el) => { notes.current[row.id] = el; }} className="relative grid">
                      <AnimatePresence mode="popLayout" initial={false}>
                        <motion.span key={row.note + nextStep} initial={{ opacity: 0, y: 12, filter: "blur(4px)" }} animate={{ opacity: 1, y: 0, filter: "blur(0px)" }} exit={{ opacity: 0, y: -12, filter: "blur(4px)" }} transition={soft}
                          className={`whitespace-nowrap text-[17px] leading-[1.3] phone:text-[15px] ${nextStep ? "rounded-full bg-orange/22 px-3 py-1 text-ink" : "text-ink-soft"}`}>
                          {row.note}
                        </motion.span>
                      </AnimatePresence>
                    </span>
                    <span className="flex w-[52px] justify-end -space-x-2 phone:justify-start">
                      <AnimatePresence initial={false}>
                        {(via[row.id] ?? []).map((door, j) => (
                          <motion.span key={`${door}-${j}`} initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} transition={{ ...spring, delay: 0.15 }} className="grid size-[30px] place-items-center rounded-full bg-card text-ink shadow-[0_1px_2px_#193a3026,0_3px_8px_-2px_#193a3026]">
                            <Icon name={doorIcon[door]} className="size-4" />
                          </motion.span>
                        ))}
                      </AnimatePresence>
                    </span>
                  </span>
                </li>
              );
            })}
          </ol>

          <Saved saving={shown.phase === "land"} />
        </div>

        {/* The door this moment came through: from the side on wide screens, from below the heading otherwise. */}
        <div
          className={`pointer-events-none absolute top-[150px] left-1/2 w-[min(340px,calc(100%-8px))] -translate-x-1/2 -translate-y-1/2 min-[1240px]:top-(--row-y) min-[1240px]:w-[290px] min-[1240px]:translate-x-0 ${moment.side === "left" ? "min-[1240px]:left-[calc(50%_-_590px)]" : "min-[1240px]:left-[calc(50%_+_312px)]"}`}
          aria-hidden="true"
        >
          <AnimatePresence>
            {(fragment || reduced) && (
              <div key={`${shown.m}`} ref={fold}>
                <motion.div initial={{ ...enterFrom, opacity: 0, scale: 0.94, filter: "blur(8px)" }} animate={{ x: 0, y: 0, rotate: 0, opacity: 1, scale: 1, filter: "blur(0px)" }} exit={{ opacity: 0, transition: { duration: 0.15 } }}
                  transition={{ ...spring, opacity: { duration: 0.3 }, filter: { duration: 0.35 } }}>
                  <Fragment door={moment.door} phase={reduced ? "answer" : shown.phase} />
                </motion.div>
              </div>
            )}
          </AnimatePresence>
        </div>

        <p className="sr-only">{words.alt}</p>
      </div>
    </MotionConfig>
  );
}

// A step's state: the page's one care mark, drawn big on a card-coloured disc so the thread passes behind it. A change
// sends out a ring.
function Mark({ state, pulse }: { state: CareState; pulse: boolean }) {
  return (
    <span className="relative grid size-7 place-items-center rounded-full bg-card">
      <CareMark state={state} size="size-7" />
      {pulse && <Ping className="inset-0 bg-orange/45" />}
    </span>
  );
}

const fragmentShadow = "shadow-[0_1px_2px_#193a3014,0_16px_36px_-14px_#193a3040,0_44px_80px_-36px_#193a3047]";
const show = (on: boolean, delay = 0) => ({ initial: false, animate: { opacity: on ? 1 : 0, y: on ? 0 : 8 }, transition: { ...soft, delay: on ? delay : 0 } }) as const;

// Each door, as a small object: what the patient (or the record) said, and what happened.
function Fragment({ door, phase }: { door: Door; phase: Phase }) {
  const asked = reached(phase, "ask");
  const answered = reached(phase, "answer");
  const alex = STEPS[4].beats;
  const text = STEPS[3].beats;
  if (door === "call") {
    return (
      <div className={`rounded-[26px] bg-deep p-5 text-on-deep ${fragmentShadow}`}>
        <div className="flex items-center gap-3">
          <span className="grid size-9 place-items-center rounded-full bg-orange text-ink"><Icon name="phone" className="size-[18px]" /></span>
          <span className="text-[15px]">{words.calling}</span>
          <span className="ml-auto"><Voice who="ophi" bars={9} small tone="text-on-deep/80" /></span>
        </div>
        <p className="mt-4 text-[14px] text-on-deep-soft">{words.alex}</p>
        <p className="font-serif text-[22px] leading-[1.25] tracking-[-.01em]">{alex[0].say!.text}</p>
        <Grow on={asked}>
          <p className="pt-3 text-[14px] text-on-deep-soft">{words.ophi}</p>
          <p className="text-[16px] leading-[1.4] text-on-deep">{alex[1].say!.text}</p>
        </Grow>
      </div>
    );
  }
  if (door === "text") {
    return (
      <div className={`rounded-[26px] bg-card p-5 ${fragmentShadow}`}>
        <p className="flex items-center gap-2 text-[14px] text-label"><Icon name="speech" className="size-4" />{words.text}</p>
        <p className="mt-3 max-w-[92%] rounded-[20px] rounded-tl-[6px] bg-sage px-4 py-2.5 text-[15px] leading-[1.4]">{text[2].say!.text}</p>
        <Grow on={asked}>
          <div className="grid justify-items-end pt-2">
            <motion.span className="col-start-1 row-start-1 flex h-10 items-center gap-1 rounded-[20px] rounded-tr-[6px] bg-ink px-4" {...show(!answered)}>
              {[0, 1, 2].map((d) => <motion.span key={d} className="size-1.5 rounded-full bg-paper/70" animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1, repeat: Infinity, delay: d * 0.18 }} />)}
            </motion.span>
            <motion.span className="col-start-1 row-start-1 rounded-[20px] rounded-tr-[6px] bg-ink px-4 py-2.5 text-[15px] text-paper" {...show(answered)}>{text[3].say!.text}</motion.span>
          </div>
        </Grow>
      </div>
    );
  }
  if (door === "page") {
    const pressing = asked && !answered;
    const prepAt = MOMENTS[0].to.find(({ id }) => id === "prep")!.note;
    return (
      <div className={`rounded-[26px] bg-card p-5 ${fragmentShadow}`}>
        <p className="flex items-center gap-2 text-[14px] text-label"><Icon name="lock" className="size-4" />{words.page}</p>
        <p className="mt-3 font-serif text-[21px] leading-[1.25] tracking-[-.01em]">{words.planReady}</p>
        <motion.span className={`mt-4 flex min-h-11 items-center justify-center gap-2 rounded-full px-4 text-[15px] font-medium ${answered ? "bg-ink text-paper" : "bg-orange text-ink"}`} animate={{ scale: pressing ? 0.95 : 1 }} transition={spring}>
          {answered && <Icon name="check" className="size-4" />}
          {answered ? words.booked(prepAt) : words.book(prepAt)}
        </motion.span>
      </div>
    );
  }
  const estimate = MOMENTS[1].to.find(({ id }) => id === "estimate")!;
  return (
    <div className={`rounded-[26px] bg-card p-5 ${fragmentShadow}`}>
      <p className="flex items-center gap-2 text-[14px] text-label"><Icon name="records" className="size-4" />{words.records}</p>
      <p className="mt-3 font-serif text-[21px] leading-[1.25] tracking-[-.01em]">{words.insurer}</p>
      <Grow on={asked}>
        <p className="mt-3 flex items-center gap-2.5 rounded-[16px] bg-sage px-3.5 py-2.5 text-[15px]">
          <span className="grid size-[18px] flex-none place-items-center rounded-full bg-ink text-paper"><Icon name="check" className="size-3" /></span>
          {estimate.note}
        </p>
      </Grow>
    </div>
  );
}

// A line that opens its own room as it arrives, so a fragment grows with its conversation.
function Grow({ on, children }: { on: boolean; children: ReactNode }) {
  return (
    <motion.div className="overflow-hidden" initial={false} animate={on ? { height: "auto", opacity: 1 } : { height: 0, opacity: 0 }} transition={{ height: soft, opacity: { duration: 0.45, delay: on ? 0.12 : 0 } }}>
      {children}
    </motion.div>
  );
}

// The card's link to the clinic's record system: quiet while Ophi reads, a tick each time a change is saved back.
function Saved({ saving }: { saving: boolean }) {
  return (
    <p className="relative mt-5 flex h-12 items-center gap-2.5 overflow-hidden rounded-[18px] bg-paper px-4 text-[15px] text-label phone:mt-4">
      <span className="relative grid size-[18px] flex-none place-items-center">
        <motion.span className="absolute inset-0 grid place-items-center" animate={{ opacity: saving ? 0 : 1, scale: saving ? 0.6 : 1 }} transition={spring}><Icon name="records" className="size-[18px]" /></motion.span>
        <motion.span className="absolute inset-0 grid place-items-center rounded-full bg-ink text-paper" animate={{ opacity: saving ? 1 : 0, scale: saving ? 1 : 0.6 }} transition={spring}><Icon name="check" className="size-3" /></motion.span>
      </span>
      <span className="relative grid">
        <AnimatePresence mode="popLayout" initial={false}>
          <motion.span key={saving ? "s" : "r"} initial={{ y: 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -14, opacity: 0 }} transition={soft} className={saving ? "text-ink" : ""}>
            {saving ? words.saved : words.inStep}
          </motion.span>
        </AnimatePresence>
      </span>
    </p>
  );
}
