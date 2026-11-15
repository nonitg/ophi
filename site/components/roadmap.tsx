import type { CSSProperties } from "react";
import { copy } from "@/lib/copy";
import { Icon } from "@/components/icons";

const words = copy.roadmap;

// Where Ophi is going, drawn as the page's thread laid on its side: the first stage is live, the rest are planned,
// and each one adds work without taking away the last. Phones turn it upright, like a patient's thread. As it comes
// into view the line draws from the live stage and each stage arrives as the line reaches it (globals.css `.stage`).
export function Roadmap() {
  return (
    <div data-reveal className="mt-16 phone:mt-12">
      <ol className="relative grid grid-cols-5 gap-6 tablet:grid-cols-1 tablet:gap-0">
        <span className="grow-line absolute top-[13px] right-0 left-[14px] h-[2px] origin-left bg-line tablet:hidden" aria-hidden="true" />
        {words.stages.map(({ name, work }, i) => (
          <li key={name} className="relative tablet:grid tablet:grid-cols-[28px_minmax(0,1fr)] tablet:gap-x-5 tablet:pb-10 tablet:last:pb-0" style={{ "--i": i } as CSSProperties}>
            {i < words.stages.length - 1 && <span className="grow-down absolute top-[34px] bottom-1 left-[13px] hidden w-[2px] origin-top bg-line tablet:block" aria-hidden="true" />}
            <div className="flex items-center gap-3 tablet:items-start">
              <span className={`stage-dot relative size-7 flex-none rounded-full ${i === 0 ? "now-ring bg-orange shadow-[0_0_0_6px_color-mix(in_srgb,var(--orange)_22%,transparent)]" : "border-2 border-dashed border-ink/35 bg-paper"}`} aria-hidden="true" />
              {i === 0 && <span className="stage rounded-full bg-[#f9d6c5] px-3 py-1 text-[14px] font-medium tablet:hidden">{words.now}</span>}
            </div>
            <div className="stage">
              <h3 className="mt-6 flex flex-wrap items-center gap-3 font-serif text-[length:clamp(26px,2.2vw,32px)] leading-[1.1] tracking-[-.02em] tablet:mt-0">
                {name}
                {i === 0 && <span className="hidden rounded-full bg-[#f9d6c5] px-3 py-1 font-sans text-[14px] font-medium tracking-normal tablet:inline">{words.now}</span>}
              </h3>
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
