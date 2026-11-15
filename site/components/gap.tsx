import type { CSSProperties } from "react";
import { copy } from "@/lib/copy";
import { CARE, frameAt, lastBeat } from "@/lib/story";
import { Icon } from "@/components/icons";
import { Thread } from "@/components/thread";
import { caption, card } from "@/components/type";

const words = copy.gap;
// Alex's crown the day it was planned (the story's third moment): one date in Alex's head today.
const plan = frameAt(2, lastBeat(2)).care;
const today = plan.map(({ id, label, note, state }) => ({ label, note, state, hidden: id !== words.known }));
const known = CARE.find(({ id }) => id === words.known);

// The gap How just closed: Alex's plan today, all but one step out of focus. Then what the gap costs, in two counts,
// each with what Ophi does about it underneath.
export function Gap() {
  return (
    <>
      <figure data-reveal className={`${card} mx-auto mt-16 flex w-full max-w-[680px] flex-col p-8 tablet:p-6 phone:mt-12`} aria-label={`${words.patient}: only ${known?.label}`}>
        <figcaption className="flex items-center gap-2.5 text-[15px] text-muted"><Icon name="person" className="size-[18px]" />{words.patient}</figcaption>
        <Thread steps={today} className="mt-6" />
        <p className="mt-6 flex items-center gap-2.5 text-[16px] text-ink"><Icon name="phone" className="size-[18px] flex-none" />{words.ask}</p>
      </figure>

      <div className="mt-24 grid grid-cols-2 gap-x-16 gap-y-20 tablet:gap-x-10 phone:mt-16 phone:grid-cols-1">
        {words.stats.map((stat, i) => (
          <div key={stat.figure} className="flex flex-col">
            <div data-reveal style={{ "--i": i } as CSSProperties}>
              {/* Both counts sit on the same baseline, whatever their drawing's height. */}
              <div className="flex h-[88px] items-end phone:h-auto">{stat.of === 100 ? <Hundred hit={stat.hit} /> : <People hit={stat.hit} of={stat.of} />}</div>
              <p className="mt-8 font-serif text-[length:clamp(44px,4.6vw,64px)] leading-none tracking-[-.03em]">{stat.figure}</p>
              <p className="mt-3 max-w-[22em] text-[18px] leading-[1.5] text-ink-soft">{stat.text}</p>
              <p className={`${caption} mt-3`}>
                Source: {stat.href ? <a className="underline decoration-line underline-offset-4 hover:decoration-ink" href={stat.href} target="_blank" rel="noopener">{stat.source}</a> : stat.source}
              </p>
            </div>
            {/* The fix, a beat after the problem. */}
            <div data-reveal className={`${card} mt-8 p-6 phone:p-5`} style={{ "--i": i + 3 } as CSSProperties}>
              <p className="flex items-center gap-2.5 text-[15px] text-ink"><Ticked />{words.fixLabel}</p>
              <p className="mt-3 font-serif text-[length:clamp(23px,1.9vw,28px)] leading-[1.25] tracking-[-.02em] text-pretty">{stat.fix}</p>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

// Ophi's tick: what Ophi changes is marked the same way everywhere in this section.
const Ticked = () => <span className="grid size-[18px] flex-none place-items-center rounded-full bg-deep text-on-deep" aria-hidden="true"><Icon name="check" className="size-3" /></span>;

// A hundred calls, the ones that hung up filled in.
function Hundred({ hit }: { hit: number }) {
  return (
    <div className="grid w-fit grid-cols-[repeat(20,10px)] gap-[7px] tablet:grid-cols-[repeat(20,8px)] tablet:gap-[6px]" aria-hidden="true">
      {Array.from({ length: 100 }, (_, i) => (
        <span key={i} className={`aspect-square rounded-full ${i < hit ? "hit bg-ink" : "bg-ink/12"}`} style={{ "--d": i } as CSSProperties} />
      ))}
    </div>
  );
}

// Five adults, the one who has opened a portal filled in.
function People({ hit, of }: { hit: number; of: number }) {
  return (
    <div className="flex items-end gap-2.5" aria-hidden="true">
      {Array.from({ length: of }, (_, i) => (
        <span key={i} className={`grid size-[52px] place-items-center rounded-full phone:size-11 ${i < hit ? "hit bg-ink text-paper" : "bg-ink/8 text-ink/40"}`} style={{ "--d": i * 8 } as CSSProperties}>
          <Icon name="person" className="size-6" />
        </span>
      ))}
    </div>
  );
}
