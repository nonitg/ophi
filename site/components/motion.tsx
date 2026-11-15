"use client";

import { useSyncExternalStore, type CSSProperties, type ReactNode } from "react";
import { AnimatePresence, motion, type Transition } from "motion/react";

// The site's one motion language, shared by every animated section so they all move alike: things spring into
// place, text changes in place instead of swapping, and the old leaves quickly before the new arrives.
export const spring: Transition = { type: "spring", stiffness: 240, damping: 24 };
export const settle: Transition = { type: "spring", stiffness: 240, damping: 30, mass: 0.9 };
export const pop: Transition = { type: "spring", stiffness: 420, damping: 28 };
export const soft: Transition = { duration: 0.55, ease: [0.16, 1, 0.3, 1] };
export const glide: Transition = { duration: 0.7, ease: [0.16, 1, 0.3, 1] };
export const leave: Transition = { duration: 0.2, ease: [0.16, 1, 0.3, 1] };
export const ping: Transition = { duration: 1, ease: [0.16, 1, 0.3, 1] };

const subscribeNever = () => () => {};
const prefersReduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
// Read after hydration, so the server's render and the first client render match.
export const usePrefersReduced = () => useSyncExternalStore(subscribeNever, prefersReduced, () => false);

// A short label changing in place: the old one lifts away, then the new one rises in.
export function Swap({ id, className, children }: { id: string; className?: string; children: ReactNode }) {
  return (
    <span className="relative inline-grid">
      <AnimatePresence mode="wait" initial={false}>
        <motion.span key={id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6, transition: leave }} transition={glide} className={className}>{children}</motion.span>
      </AnimatePresence>
    </span>
  );
}

// Text replaced in place by a soft, blurred crossfade. `room` holds the space of every version it can show, so the
// layout around it never moves.
export function Fade({ id, room = [], className = "", children }: { id: string | number; room?: readonly string[]; className?: string; children: ReactNode }) {
  return (
    <span className={`relative grid ${className}`}>
      {room.map((text) => <span key={text} className="invisible col-start-1 row-start-1" aria-hidden="true">{text}</span>)}
      <AnimatePresence mode="popLayout" initial={false}>
        <motion.span key={id} className="col-start-1 row-start-1" initial={{ opacity: 0, y: 12, filter: "blur(4px)" }} animate={{ opacity: 1, y: 0, filter: "blur(0px)" }} exit={{ opacity: 0, y: -12, filter: "blur(4px)" }} transition={soft}>
          {children}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}

// A voice on a call, as moving bars: Ophi in ink, the caller in sage, still when nobody is speaking. `small` is the
// compact one; `tone` sets the colour on surfaces where ink and sage don't show.
export function Voice({ who, bars = 19, small = false, tone }: { who: string | null; bars?: number; small?: boolean; tone?: string }) {
  const colour = tone ?? (who && who !== "ophi" ? "text-sage-deep" : "text-ink");
  return (
    <div className={`flex flex-none items-center justify-center transition-[color] duration-500 ${small ? "h-6 gap-[3px]" : "h-10 gap-[5px]"} ${colour}`} aria-hidden="true">
      {Array.from({ length: bars }, (_, i) => (
        <span key={i} className={`h-full rounded-full bg-current transition-[scale] duration-500 motion-reduce:transition-none ${small ? "w-[3px]" : "w-[4px]"} ${who ? "motion-safe:animate-[voice_.9s_ease-in-out_infinite]" : ""}`} style={{ scale: `1 ${who ? (22 + ((i * 37) % 64)) / 100 : 0.08}`, animationDelay: `${-((i * 53) % 90) / 100}s`, animationDuration: `${0.7 + ((i * 29) % 50) / 100}s` } as CSSProperties} />
      ))}
    </div>
  );
}

// A text message, springing up from its own corner: Ophi's on the left in sage, the patient's on the right in ink.
export function Bubble({ who, children }: { who: string; children: ReactNode }) {
  const ophi = who === "ophi";
  return (
    <motion.p layout="position" className={`max-w-[86%] flex-none rounded-[20px] px-4 py-2.5 text-[15px] leading-[1.4] ${ophi ? "self-start rounded-bl-[6px] bg-sage" : "self-end rounded-br-[6px] bg-ink text-paper"}`}
      style={{ transformOrigin: ophi ? "0% 100%" : "100% 100%" }}
      initial={{ opacity: 0, y: 14, scale: 0.92 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, scale: 0.92, transition: leave }}
      transition={{ ...pop, opacity: { duration: 0.25 } }}>
      {children}
    </motion.p>
  );
}

// Something just happened here: a disc leaves it and fades. The same disc, starting small, is a patient's tap on a
// button. Place and colour it with `className`; change its key to send another.
export function Ping({ className, from = 1 }: { className: string; from?: number }) {
  return <motion.span className={`pointer-events-none absolute rounded-full ${className}`} initial={{ scale: from, opacity: 0.8 }} animate={{ scale: 2.6, opacity: 0 }} exit={{ opacity: 0 }} transition={ping} aria-hidden="true" />;
}
