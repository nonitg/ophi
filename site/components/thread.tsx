import { Fragment, type CSSProperties } from "react";
import type { CareItem, CareState } from "@/lib/story";
import { copy } from "@/lib/copy";
import { CareMark } from "@/components/care-mark";
import { Fade } from "@/components/motion";

// The page's one motif: a patient's care as a thread of steps, each marked done, booked, planned or waiting.
// Every picture on the page draws it the same way. A `hidden` step is one the patient can't see: it prints, then
// blurs out of focus as its card comes into view (globals.css `.fog`).
export type ThreadStep = { label: string; note: string; state: CareState; next?: boolean; hidden?: boolean; changed?: boolean };

const sizes = {
  md: { row: "pb-[18px]", label: "text-[17px] phone:text-[16px]", note: "text-[15px]", line: "top-[24px]" },
  sm: { row: "pb-3", label: "text-[15px]", note: "text-[14px]", line: "top-[22px]" },
};

// A care timeline as a thread, the first open step marked as the next one.
export const toThread = (care: CareItem[]): ThreadStep[] => {
  const next = care.findIndex(({ state }) => state !== "done");
  return care.map(({ label, note, state, changed }, i) => ({ label, note, state, changed, next: i === next }));
};

export function Thread({ steps, size = "md", className = "" }: { steps: readonly ThreadStep[]; size?: keyof typeof sizes; className?: string }) {
  const s = sizes[size];
  return (
    <ol className={`grid ${className}`}>
      {steps.map(({ label, note, state, next, hidden, changed }, i) => (
        <li key={label} className={`relative grid grid-cols-[18px_minmax(0,1fr)] items-start gap-x-3.5 last:pb-0 ${s.row}`} style={{ "--i": i } as CSSProperties}>
          {/* The thread between this step and the next. */}
          {i < steps.length - 1 && <span className={`absolute bottom-0 left-[8px] w-[2px] rounded-full bg-line ${s.line}`} aria-hidden="true" />}
          <CareMark state={hidden ? "planned" : state} className="mt-[3px]" />
          <div className={`flex min-w-0 flex-wrap items-baseline justify-between gap-x-4 gap-y-0.5 ${hidden ? "fog" : ""}`} aria-hidden={hidden || undefined}>
            <span className={`${s.label} leading-[1.35] text-ink ${changed ? "motion-safe:animate-[flash-text_1.2s_ease-out]" : ""}`}><span className="sr-only">{copy.story.states[state]}: </span>{label}</span>
            {/* A changed note crossfades in place; becoming the next step, it eases into its orange pill. */}
            <span className={`${s.note} rounded-full leading-[1.35] transition-[background-color,color,padding] duration-500 ${next ? "bg-orange/25 px-2.5 py-0.5 font-medium text-ink" : "text-muted"}`}><Fade id={note}>{note}</Fade></span>
          </div>
          {hidden && <span className="sr-only">Not known to the patient</span>}
        </li>
      ))}
    </ol>
  );
}

// A thread in miniature, laid on its side: one mark per step, joined by short lines.
export function MiniThread({ states, join = "w-2.5 bg-line", className = "" }: { states: readonly CareState[]; join?: string; className?: string }) {
  return (
    <span className={`flex w-fit items-center ${className}`} aria-hidden="true">
      {states.map((state, i) => (
        <Fragment key={i}>
          {i > 0 && <span className={`h-[2px] ${join}`} />}
          <CareMark state={state} />
        </Fragment>
      ))}
    </span>
  );
}
