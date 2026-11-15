"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, MotionConfig, motion } from "motion/react";
import { copy } from "@/lib/copy";
import { EVENTS, teamAt, type Row } from "@/lib/team";
import { Icon } from "@/components/icons";
import { spring, soft, Fade, Ping } from "@/components/motion";
import { MiniThread } from "@/components/thread";
import { card } from "@/components/type";
import { useInView } from "@/components/use-in-view";

const words = copy.team;
// A new thing happens at the clinic this often while the reader watches.
const EVENT_MS = 3800;
// Each check after a yes stays in view this long, long enough to read.
const STEP_MS = 800;
// Shared by the column labels and every row, so they line up.
const columns = "grid grid-cols-[minmax(0,1.1fr)_150px_minmax(0,1.1fr)_minmax(0,1.3fr)] gap-x-6 tablet:grid-cols-[minmax(0,1fr)_150px_minmax(0,1.1fr)] phone:grid-cols-[minmax(0,1fr)_auto]";


// Every line a row or the status can show while the reader watches. Each holds the room of its longest version, so
// the card never changes height as things happen.
const HELD = teamAt(0, false).rows.find(({ ask }) => ask)!.id;
const LINES = new Map<string, string[]>();
for (let e = 0; e <= EVENTS.length; e++) {
  for (const approved of [false, true]) {
    for (const row of teamAt(e, approved).rows) {
      for (const [field, text] of [["next", row.next], ["move", row.move]]) {
        const all = LINES.get(`${row.id}:${field}`) ?? [];
        if (!all.includes(text)) LINES.set(`${row.id}:${field}`, [...all, text]);
      }
    }
  }
}
const MESSAGES = [words.idle, words.done, ...EVENTS.map(({ now }) => now)];

type Approval = "no" | "running" | "done";

// The clinic's side as a working miniature: a few patients on one Wednesday, things happening to them while the
// reader watches, and the one change this clinic's rules hold for a yes. Approve runs the checks in order.
export function TeamView() {
  const root = useRef<HTMLDivElement>(null);
  const status = useRef<HTMLParagraphElement>(null);
  const seen = useInView(root, 0.3);
  const [events, setEvents] = useState(0);
  const [approval, setApproval] = useState<Approval>("no");
  const [checks, setChecks] = useState(0);
  // How many events had happened when the yes went through: until the next one, the status line reports the yes.
  const [approvedAt, setApprovedAt] = useState(-1);

  useEffect(() => {
    if (!seen || events >= EVENTS.length || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const timer = setTimeout(() => setEvents(events + 1), EVENT_MS);
    return () => clearTimeout(timer);
  }, [seen, events]);

  useEffect(() => {
    if (approval !== "running") return;
    const timer = setTimeout(() => {
      if (checks < words.approved.length) { setChecks(checks + 1); return; }
      setApproval("done");
      setApprovedAt(events);
      // The button is gone now; focus moves to the line that says what happened.
      status.current?.focus({ preventScroll: true });
    }, STEP_MS);
    return () => clearTimeout(timer);
  }, [approval, checks, events]);

  function approve() {
    setApproval("running");
    setChecks(1);
  }

  const team = teamAt(events, approval === "done");
  const message = approvedAt === events ? words.done : team.now ?? words.idle;
  return (
    <MotionConfig reducedMotion="user">
      <div ref={root} data-reveal className="mt-16 phone:mt-12">
        <div className={`${card} overflow-hidden`}>
          <div className="flex flex-wrap items-end justify-between gap-x-10 gap-y-5 px-8 pt-7 pb-5 phone:px-5 phone:pt-6">
            <div>
              <p className="font-serif text-[26px] leading-[1.15] tracking-[-.02em]">{words.clinic}</p>
              <p className="mt-1 text-[15px] text-muted">{words.when}</p>
            </div>
            <dl className="flex gap-8 phone:w-full phone:justify-between phone:gap-4">
              {words.tallies.map(({ id, label }) => {
                const value = team.tally[id as keyof typeof team.tally];
                return (
                  <div key={id} className="flex flex-col-reverse">
                    <dt className="text-[14px] leading-[1.3] text-muted">{label}</dt>
                    <dd className="font-serif text-[34px] leading-none tracking-[-.02em] tabular-nums"><Fade id={value}>{value}</Fade></dd>
                  </div>
                );
              })}
            </dl>
          </div>
          <div className="px-3 pb-3 phone:px-2">
            <div className={`${columns} px-5 py-2 text-[14px] text-muted phone:hidden`} aria-hidden="true">
              {words.columns.map((name, i) => <span key={name} className={i === 3 ? "tablet:hidden" : ""}>{name}</span>)}
            </div>
            <ul aria-label="Patients at the clinic today">
              {team.rows.map((row) => (
                <PatientRow key={row.id} row={row} fresh={row.id === team.latest} approval={approval} checks={checks} onApprove={approve} />
              ))}
            </ul>
          </div>
          {/* What just happened, in words. Announced only once the reader has pressed Approve. */}
          <p ref={status} tabIndex={-1} className="flex min-h-[60px] items-center gap-3 bg-sage px-8 py-3 phone:items-start phone:py-4 text-[16px] leading-[1.45] outline-none phone:px-5 phone:text-[15px]" aria-live={approval === "no" ? "off" : "polite"}>
            <span className="relative size-2.5 flex-none rounded-full bg-sage-deep phone:mt-[7px]" aria-hidden="true">
              <Ping key={message} className="inset-0 bg-sage-deep" />
            </span>
            <Fade id={message} room={MESSAGES} className="min-w-0 flex-1">{message}</Fade>
          </p>
        </div>
        <p className="mt-4 text-[14px] text-muted">{words.note}</p>
      </div>
    </MotionConfig>
  );
}

function PatientRow({ row, fresh, approval, checks, onApprove }: { row: Row; fresh: boolean; approval: Approval; checks: number; onApprove: () => void }) {
  const held = row.id === HELD;
  const done = row.marks.filter((m) => m === "done").length;
  const ask = <Ask approval={approval} checks={checks} move={row.move} onApprove={onApprove} />;
  return (
    <li className="relative rounded-[18px] px-5 py-4 phone:px-3 phone:py-3.5">
      {/* The held request sits on sage until the yes; the latest thing to happen is lit, and the light glides from row to row. */}
      {held && <motion.span className="absolute inset-0 rounded-[18px] bg-sage/70" initial={false} animate={{ opacity: approval === "done" ? 0 : 1 }} transition={{ duration: 0.9, ease: soft.ease }} aria-hidden="true" />}
      {fresh && <motion.span layoutId="team-latest" className="absolute inset-0 bg-sage/45" style={{ borderRadius: 18 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={spring} aria-hidden="true" />}
      <div className={`relative ${columns} items-center phone:gap-y-1`}>
        <div>
          <p className="text-[17px] leading-[1.3]">{row.name}</p>
          <p className="text-[15px] text-muted">{row.care}</p>
        </div>
        <div>
          <span className="sr-only">{`${done} of ${row.marks.length} steps done`}</span>
          <MiniThread states={row.marks} />
        </div>
        <div className="phone:col-span-2">
          <p className="text-[16px] leading-[1.4]"><Fade id={row.next} room={LINES.get(`${row.id}:next`)}>{row.next}</Fade></p>
          {/* Without room for "What Ophi did", it sits under what's next, ticked like everything Ophi does here. */}
          {!held && (
            <p className="mt-1 hidden items-start gap-2 text-[15px] leading-[1.4] text-ink-soft tablet:flex">
              <Tick className="mt-[3px] size-4" /><Fade id={row.move} room={LINES.get(`${row.id}:move`)} className="min-w-0 flex-1">{row.move}</Fade>
            </p>
          )}
        </div>
        <div className="text-[15px] leading-[1.4] text-ink-soft tablet:hidden">{held ? ask : <Fade id={row.move} room={LINES.get(`${row.id}:move`)}>{row.move}</Fade>}</div>
      </div>
      {/* Tablets and phones drop the last column, so the request sits under the row. */}
      {held && <div className="relative mt-3 hidden tablet:block">{ask}</div>}
    </li>
  );
}

// The held request, in one space that never changes size: why it waits and the yes; then each check, one after
// another, while the button fills; then what happened.
function Ask({ approval, checks, move, onApprove }: { approval: Approval; checks: number; move: string; onApprove: () => void }) {
  const running = approval === "running";
  const line = running ? words.approved[checks - 1] : words.rule;
  const button = "flex min-h-11 min-w-[148px] items-center justify-center gap-2 rounded-full bg-ink px-5 text-[15px] font-medium text-paper";
  return (
    <div className="relative grid items-center text-[14px]">
      {/* Holds the room of the request at its widest, whatever is showing. */}
      <div className="invisible col-start-1 row-start-1 flex flex-wrap items-center justify-between gap-3" aria-hidden="true">
        <span className="flex gap-2"><span className="size-4" />{words.rule}</span>
        <span className={button}>{words.approving}<span className="w-[34px]" /></span>
      </div>
      <AnimatePresence mode="popLayout" initial={false}>
        {approval !== "done" ? (
          <motion.div key="ask" className="col-start-1 row-start-1 flex flex-wrap items-center justify-between gap-3" exit={{ opacity: 0, y: -10, filter: "blur(4px)" }} transition={soft}>
            <Fade id={line} className="text-label">
              <span className="flex items-center gap-2">
                {running && <Tick className="size-4" />}
                {line}
              </span>
            </Fade>
            <button type="button" onClick={onApprove} disabled={running} className={`${button} [transition:background_.15s,scale_.16s_var(--ease-out)] hover:bg-ink-soft active:scale-[.97] disabled:cursor-default disabled:opacity-100`}>
              <Fade id={approval}>{running ? words.approving : words.approve}</Fade>
              {running ? (
                // One dot per check, filling as each one passes.
                <span className="flex w-[34px] justify-end gap-1" aria-hidden="true">
                  {words.approved.map((_, i) => <motion.span key={i} className="size-1.5 rounded-full bg-paper" initial={false} animate={{ opacity: i < checks ? 1 : 0.3, scale: i < checks ? 1 : 0.7 }} transition={spring} />)}
                </span>
              ) : <Icon name="check" className="size-4" />}
            </button>
          </motion.div>
        ) : (
          <motion.p key="done" className="col-start-1 row-start-1 flex items-center gap-2.5 text-[15px] text-ink-soft" initial={{ opacity: 0, y: 12, filter: "blur(4px)" }} animate={{ opacity: 1, y: 0, filter: "blur(0px)" }} transition={{ ...soft, delay: 0.1 }}>
            <Tick className="size-[18px]" />
            {move}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}

// What Ophi did, marked the same way wherever it shows.
function Tick({ className }: { className: string }) {
  return <span className={`grid flex-none place-items-center rounded-full bg-deep text-on-deep ${className}`} aria-hidden="true"><Icon name="check" className="size-[66%]" /></span>;
}
