import type { CSSProperties } from "react";
import { copy } from "@/lib/copy";
import { Icon } from "@/components/icons";

const words = copy.desk;

// The whole front desk: first the doors a patient uses (a call is only one), then the page's thread laid on its side,
// one stop per job, each marked done because Ophi does every one. Phones turn it upright, like a patient's thread. As
// it comes into view the line draws and each stop arrives as the line reaches it (globals.css `.stage`).
export function FrontDesk() {
  return (
    <div data-reveal className="mt-12 phone:mt-10">
      <div className="mb-16 flex flex-wrap items-center gap-x-3 gap-y-2.5 phone:mb-12">
        <span className="mr-1 text-[15px] text-muted phone:w-full">{words.doorsLabel}</span>
        {words.doors.map(({ icon, label }) => (
          <span key={label} className="inline-flex h-10 items-center gap-2 rounded-full bg-sage pr-4 pl-3 text-[15px] text-ink"><Icon name={icon} className="size-[18px] text-sage-deep" />{label}</span>
        ))}
      </div>
      <ol className="relative grid grid-cols-5 gap-6 tablet:grid-cols-1 tablet:gap-0">
        <span className="grow-line absolute top-[13px] right-0 left-[14px] h-[2px] origin-left bg-ink/25 tablet:hidden" aria-hidden="true" />
        {words.stages.map(({ name, work }, i) => (
          <li key={name} className="relative tablet:grid tablet:grid-cols-[28px_minmax(0,1fr)] tablet:gap-x-5 tablet:pb-10 tablet:last:pb-0" style={{ "--i": i } as CSSProperties}>
            {i < words.stages.length - 1 && <span className="grow-down absolute top-[34px] bottom-1 left-[13px] hidden w-[2px] origin-top bg-ink/25 tablet:block" aria-hidden="true" />}
            <span className="stage-dot relative grid size-7 place-items-center rounded-full bg-ink text-paper" aria-hidden="true"><Icon name="check" className="size-4 [stroke-width:2.2]" /></span>
            <div className="stage">
              <h3 className="mt-6 font-serif text-[length:clamp(26px,2.2vw,32px)] leading-[1.1] tracking-[-.02em] tablet:mt-0">{name}</h3>
              <p className="mt-3 max-w-[18em] text-[16px] leading-[1.5] text-ink-soft">{work}</p>
            </div>
          </li>
        ))}
      </ol>
      <p style={{ "--i": words.stages.length } as CSSProperties} className="stage mt-14 flex max-w-[760px] items-start gap-3.5 rounded-[20px] bg-sage px-6 py-5 text-[17px] leading-[1.5] phone:mt-12">
        <Icon name="person" className="mt-0.5 size-[22px] flex-none text-sage-deep" />{words.stays}
      </p>
    </div>
  );
}
