"use client";

import { useId, useRef } from "react";
import { copy } from "@/lib/copy";
import { Icon } from "@/components/icons";
import { pill, pillIcon, pillTag } from "@/components/pill";

const title = "mb-6 pr-14 text-[length:clamp(32px,3.5vw,46px)] leading-[1.1] tracking-[-1.6px] phone:pr-0 phone:text-[32px] small:text-[30px]";
const text = "mt-5 text-[14px] leading-[1.8] text-[#52614b] phone:text-[13px] xray:text-[#c3cfc4]";

export function InfoPanel({ kind }: { kind: "why" | "privacy" }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const isWhy = kind === "why";
  // "Why Ophi?" sits in the signup band; privacy sits in the footer.
  const look = isWhy ? { surface: "band-desktop", size: "default" } as const : { surface: "paper", size: "footer" } as const;
  return (
    <>
      <button className={pill({ ...look, className: isWhy ? "why-button" : "privacy-button" })} type="button" aria-haspopup="dialog" onClick={() => dialog.current?.showModal()}>{isWhy ? "Why Ophi?" : "Your email & privacy"}<span className={pillTag(look)}><Icon name={isWhy ? "arrow" : "plus"} className={`${pillIcon} ${isWhy ? "group-hover/pill:translate-x-px group-hover/pill:-translate-y-px" : "group-hover/pill:rotate-90"}`} /></span></button>
      {/* The evidence is available on demand, with native modal keyboard behavior. */}
      <dialog ref={dialog} className={`${isWhy ? "why-panel" : "privacy-panel"} fixed inset-0 m-auto max-h-[calc(100dvh-48px)] w-[min(600px,calc(100%-40px))] overscroll-contain rounded-[8px] border border-[#c0c9b6] bg-paper p-0 text-ink shadow-[0_30px_120px_#10231930] backdrop:bg-[#16332857] backdrop:backdrop-blur-[9px] motion-safe:open:animate-[panel-in_.25s_ease-out_both] xray:border-line xray:shadow-[0_30px_120px_#000000a6] xray:backdrop:bg-[#050d0ab3]`} aria-labelledby={titleId} onClick={(event) => { if (event.target === event.currentTarget) dialog.current?.close(); }}>
        <article className="relative p-10 phone:px-6 phone:pt-7 phone:pb-6 small:p-5">
          {/* Close sits on the heading's first line, so the title starts the panel. On phones it floats, so only that line yields to it. */}
          <button type="button" className="absolute top-[42px] right-[30px] grid size-10 place-items-center rounded-full border border-[#b6c3a8] bg-transparent [transition:background_.2s,rotate_.35s_var(--ease-out)] hover:rotate-90 hover:bg-sage phone:static phone:float-right phone:-mt-1 phone:-mr-1.5 phone:ml-2 xray:border-pill-line" aria-label="Close" onClick={() => dialog.current?.close()}><Icon name="close" className="size-[17px]" /></button>
          {isWhy ? <>
            <h2 id={titleId} className={title}>Care takes people.<br /><em>Paperwork takes time.</em></h2>
            <p className={text}>For some treatments, clinics need approval before the Canadian Dental Care Plan will pay. Someone has to gather the records, explain the treatment, and put the details together.</p>
            <div className="mt-7 border-y border-line py-[23px]"><span className="font-serif text-[56px] leading-none tracking-[-2px] phone:text-[49px]">≈480,000</span><p className="mt-2.5 text-[13px] leading-[1.7]">complete requests for treatment preauthorization<br />in just three months.</p><span className="mt-2.5 block text-[11px] text-muted">March 1 – May 31, 2026</span></div>
            <p className={text}>Ophi is starting with the work behind those requests. We’re early, and we’ll share more when it’s ready.</p>
            <a className="mt-7 inline-flex min-h-8 items-center rounded-full bg-sage px-3.5 py-[5px] text-[11px] leading-[1.5] transition-[background] duration-200 hover:bg-tag-hover" href={copy.source.href} target="_blank" rel="noopener noreferrer">{copy.source.label}<span className="sr-only"> (opens in a new tab)</span></a>
          </> : <>
            <h2 id={titleId} className={title}>Committed to<br /><em>100% transparency</em></h2>
            <p className={text}>Joining the mailing list means occasional emails about Ophi’s launch and progress.</p>
            <p className={text}>We store your email with Resend, our email provider. Sharing your clinic software is optional; it helps us decide what to build.</p>
            <p className={text}>Your email and data never leaves our servers.</p>
            <p className={text}>We count page visits with Vercel Analytics, which uses no cookies and doesn’t identify you.</p>
          </>}
        </article>
      </dialog>
    </>
  );
}
