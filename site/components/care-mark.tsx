"use client";

import { motion } from "motion/react";
import type { CareState } from "@/lib/story";
import { soft, spring } from "@/components/motion";

// The four states of a step in someone's care, told apart by shape first and colour second: a filled tick (done),
// a ring with a centre (booked), a dashed ring (planned) and an orange ring that breathes (waiting on something).
// A change of state springs from one look into the next instead of swapping. Colours follow --mark / --mark-on,
// so a dark surface only has to set those two.
export function CareMark({ state, size = "size-[18px]", className = "" }: { state: CareState; size?: string; className?: string }) {
  const on = (s: CareState, opacity = 1) => ({ opacity: state === s ? opacity : 0, scale: state === s ? 1 : 0.55 });
  return (
    <span className={`relative grid flex-none place-items-center ${size} ${className}`} data-state={state} aria-hidden="true">
      <motion.span className="absolute inset-0 rounded-full border-[1.5px] border-dashed border-(--mark)" initial={false} animate={on("planned", 0.55)} transition={spring} />
      <motion.span className={`absolute inset-0 rounded-full border-2 border-orange after:absolute after:-inset-[2px] after:rounded-full after:border-2 after:border-orange after:opacity-0 ${state === "waiting" ? "motion-safe:after:animate-[waiting_2.2s_ease-out_infinite]" : ""}`} initial={false} animate={on("waiting")} transition={spring} />
      <motion.span className="absolute inset-0 grid place-items-center rounded-full border-2 border-(--mark)" initial={false} animate={on("booked")} transition={spring}>
        <span className="size-[38%] rounded-full bg-(--mark)" />
      </motion.span>
      <motion.span className="absolute inset-0 grid place-items-center rounded-full bg-(--mark) text-(--mark-on)" initial={false} animate={on("done")} transition={spring}>
        <svg viewBox="0 0 20 20" className="size-[68%]" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
          <motion.path d="m5 10.5 3.2 3.2L15 6.5" initial={false} animate={{ pathLength: state === "done" ? 1 : 0 }} transition={{ ...soft, delay: 0.1 }} />
        </svg>
      </motion.span>
    </span>
  );
}
