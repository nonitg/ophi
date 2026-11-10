"use client";

import { Fragment, useEffect, useRef, useState } from "react";
import type { Proposal } from "@/lib/calls";
import { copy } from "@/lib/copy";
import { Icon } from "@/components/icons";
import { pill, pillIcon, pillTag } from "@/components/pill";

const words = copy.frontDesk.card;
const STEP_MS = 750;
// How the front desk names each field of a request; a caller field only matters when someone called for the patient.
const FIELDS = { patient: "Patient", caller: "Caller", from: "From", to: "To", when: "When", provider: "With", phone: "Phone", insurance: "Insurance", reason: "Reason" } as const;

// The staff side of a call as a working miniature: the request waits, one press approves it, and the patient is only
// told once the change is written and read back (ophi-phone office.py). `text` is the confirmation the patient gets.
export function ApprovalCard({ proposal, text }: { proposal: Proposal; text: string }) {
  // 0: waiting for a yes. 1 to 3: that step is under way. Past that: done.
  const [stage, setStage] = useState(0);
  useEffect(() => {
    if (stage === 0 || stage > words.done.length) return;
    const timer = setTimeout(() => setStage(stage + 1), STEP_MS);
    return () => clearTimeout(timer);
  }, [stage]);
  const done = stage > words.done.length;
  const outcome = useRef<HTMLDivElement>(null);
  // What the press sets off is drawn below the card; on a small screen it may be out of sight.
  function approve() {
    setStage(1);
    outcome.current?.scrollIntoView({ block: "nearest" });
  }
  const rows = (Object.keys(FIELDS) as (keyof typeof FIELDS)[]).flatMap((key) => {
    const value = proposal.details[key];
    return value && !(key === "caller" && value === "self") ? [[FIELDS[key], value]] : [];
  });

  return (
    <div className="approval min-w-0 tablet:max-w-[560px]">
      <p className="mb-3 flex flex-wrap items-baseline justify-between gap-x-4 px-1 text-[12px] leading-[1.5] text-muted"><span className="text-ink">{words.label}</span><span>{words.from}</span></p>
      {/* A second sheet shows behind the first: a queue, not a single card. */}
      <div className="relative rounded-[28px] border border-pill-line bg-paper p-7 before:absolute before:inset-x-3 before:-bottom-2 before:-z-1 before:h-10 before:rounded-b-[26px] before:border before:border-t-0 before:border-line phone:rounded-[22px] phone:p-5">
        <h3 className="font-serif text-[26px] leading-[1.2] tracking-[-.5px] phone:text-[22px]">{proposal.title}</h3>
        <dl className="mt-5 grid grid-cols-[76px_minmax(0,1fr)] gap-y-2 text-[14px] leading-[1.5]">
          {rows.map(([label, value]) => <Fragment key={label}><dt className="text-muted">{label}</dt><dd>{value}</dd></Fragment>)}
        </dl>
        <div className="mt-6 flex min-h-[46px] items-center">
          {done
            ? <button type="button" className={pill()} onClick={() => setStage(0)}>{words.reset}<span className={pillTag()}><Icon name="up" className={`${pillIcon} -rotate-90 group-hover/pill:-translate-x-0.5`} /></span></button>
            : <button type="button" disabled={stage > 0} onClick={approve} className="approve-button group/approve inline-flex h-[46px] items-center gap-4 rounded-full bg-ink pr-4 pl-5 text-[13px] font-medium text-paper transition-[background] duration-200 hover:bg-ink-soft disabled:opacity-100">
                {stage > 0 ? words.working : words.approve}<Icon name="check" className="size-[20px] transition-transform duration-350 ease-out group-hover/approve:scale-110" />
              </button>}
        </div>
      </div>
      {/* What one yes sets off, in order. Shown faint beforehand, so the press holds no surprise. */}
      <ol className="relative mt-7 grid gap-3 pl-7 before:absolute before:top-[-18px] before:bottom-[-14px] before:left-[38.5px] before:w-px before:bg-line phone:pl-4 phone:before:left-[26.5px]" aria-live="polite">
        {words.done.map((label, i) => {
          const ticked = stage > i + 1;
          return (
            <li key={label} className={`flex items-center gap-3 text-[14px] leading-[1.5] transition-[color] duration-300 ${ticked ? "text-ink" : "text-muted"}`}>
              <span className={`relative grid size-[22px] flex-none place-items-center rounded-full border bg-paper text-paper ${ticked ? "border-ink" : stage === i + 1 ? "border-ink-soft" : "border-pill-line"}`}>
                {ticked && <><span className="absolute inset-0 rounded-full bg-ink motion-safe:animate-[ink-fill_.3s_var(--ease-out)_both]" /><Icon name="check" className="relative size-3.5 motion-safe:[&_path]:[stroke-dasharray:16] motion-safe:[&_path]:animate-[check-draw_.35s_.12s_var(--ease-out)_both]" /></>}
                {stage === i + 1 && <span className="size-1.5 rounded-full bg-ink-soft motion-safe:animate-pulse" />}
              </span>
              {label}
            </li>
          );
        })}
      </ol>
      <div ref={outcome} className="relative mt-5 ml-7 max-w-[420px] scroll-mb-6 phone:ml-4">
        <p key={done ? "sent" : "waiting"} className={`flex min-h-[94px] items-center rounded-[22px_22px_22px_6px] border px-4.5 py-3.5 text-[14px] leading-[1.55] ${done ? "border-transparent bg-sage text-ink motion-safe:animate-[arrive_.5s_var(--ease-out)_both]" : "border-dashed border-pill-line bg-paper text-muted"}`}>
          {done ? text : "No text yet. The patient is only told once it’s true."}
        </p>
      </div>
      <p className="mt-4 pl-7 text-[12px] leading-[1.6] text-muted phone:pl-4">{words.note}</p>
    </div>
  );
}
