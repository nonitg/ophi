"use client";

import { useEffect, useId, useRef } from "react";
import { Icon } from "@/components/icons";
import { pill, pillIcon, pillTag } from "@/components/pill";

const title = "mb-6 pr-14 text-[length:clamp(32px,3.5vw,46px)] leading-[1.1] tracking-[-1.6px] phone:pr-0 phone:text-[32px] small:text-[30px]";
const text = "mt-5 text-[16px] leading-[1.7] text-[#52614b] phone:text-[15px] xray:text-[#c3cfc4]";

// `note` adds a page's own sentence to the privacy panel (the film page also takes a name and number).
export function InfoPanel({ note }: { note?: string }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const look = { surface: "paper", size: "footer" } as const;
  // The title's italic isn't preloaded (app/layout.tsx): fetch it once the page is up, so the panel never opens on a
  // stand-in face.
  useEffect(() => {
    const em = dialog.current?.querySelector("em");
    if (em) void document.fonts.load(`italic 400 1em ${getComputedStyle(em).fontFamily}`);
  }, []);
  return (
    <>
      <button className={pill({ ...look, className: "privacy-button" })} type="button" aria-haspopup="dialog" onClick={() => dialog.current?.showModal()}>Your email & privacy<span className={pillTag(look)}><Icon name="plus" className={`${pillIcon} group-hover/pill:rotate-90`} /></span></button>
      {/* Available on demand, with native modal keyboard behavior. */}
      <dialog ref={dialog} className="privacy-panel fixed inset-0 m-auto max-h-[calc(100dvh-48px)] w-[min(600px,calc(100%-40px))] overscroll-contain rounded-[8px] border border-[#c0c9b6] bg-paper p-0 text-ink shadow-[0_30px_120px_#10231930] backdrop:bg-[#16332857] backdrop:backdrop-blur-[9px] motion-safe:open:animate-[panel-in_.25s_ease-out_both] xray:border-line xray:shadow-[0_30px_120px_#000000a6] xray:backdrop:bg-[#050d0ab3]" aria-labelledby={titleId} onClick={(event) => { if (event.target === event.currentTarget) dialog.current?.close(); }}>
        <article className="relative p-10 phone:px-6 phone:pt-7 phone:pb-6 small:p-5">
          {/* Close sits on the heading's first line, so the title starts the panel. On phones it floats, so only that line yields to it. */}
          <button type="button" className="absolute top-[42px] right-[30px] grid size-10 place-items-center rounded-full border border-[#b6c3a8] bg-transparent transition-[background] duration-200 hover:bg-sage phone:static phone:float-right phone:-mt-1 phone:-mr-1.5 phone:ml-2 xray:border-pill-line" aria-label="Close" onClick={() => dialog.current?.close()}><Icon name="close" className="size-[17px]" /></button>
          <h2 id={titleId} className={title}>Your email<br /><em>and your privacy</em></h2>
          <p className={text}>Joining the mailing list means occasional emails about Ophi’s launch and progress.</p>
          <p className={text}>We store your email with Resend, our email provider. Sharing your clinic software is optional; it helps us decide what to build.</p>
          {note && <p className={text}>{note}</p>}
          <p className={text}>We never sell your email or share it with anyone else.</p>
          <p className={text}>We count page visits with Vercel Analytics, which uses no cookies and doesn’t identify you.</p>
        </article>
      </dialog>
    </>
  );
}
