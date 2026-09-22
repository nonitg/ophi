"use client";

import { useId, useRef } from "react";
import { copy } from "@/lib/copy";
import { Icon } from "@/components/icons";

export function InfoPanel({ kind }: { kind: "why" | "privacy" }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const isWhy = kind === "why";
  return (
    <>
      <button className={`pill ${isWhy ? "why-button" : "privacy-button"}`} type="button" aria-haspopup="dialog" onClick={() => dialog.current?.showModal()}>{isWhy ? "Why Ophi?" : "Your email & privacy"}<span className="pill-tag"><Icon name={isWhy ? "arrow" : "plus"} /></span></button>
      <dialog ref={dialog} className={`info-panel ${isWhy ? "why-panel" : "privacy-panel"}`} aria-labelledby={titleId} onClick={(event) => { if (event.target === event.currentTarget) dialog.current?.close(); }}>
        <article className="panel-content">
          <button type="button" className="close-button" aria-label="Close" onClick={() => dialog.current?.close()}><Icon name="close" /></button>
          {isWhy ? <>
            <h2 id={titleId}>Care takes people.<br /><em>Paperwork takes time.</em></h2>
            <p>For some treatments, clinics need approval before the Canadian Dental Care Plan will pay. Someone has to gather the records, explain the treatment, and put the details together.</p>
            <div className="source-note"><span className="source-number">≈480,000</span><p>complete requests for treatment preauthorization<br />in just three months.</p><span className="source-period">March 1 – May 31, 2026</span></div>
            <p>Ophi is starting with the work behind those requests. We’re early, and we’ll share more when it’s ready.</p>
            <a className="source-link" href={copy.source.href} target="_blank" rel="noopener noreferrer">{copy.source.label}<span className="sr-only"> (opens in a new tab)</span></a>
          </> : <>
            <h2 id={titleId}>Committed to<br /><em>100% transparency</em></h2>
            <p>Joining the mailing list means occasional emails about Ophi’s launch and progress.</p>
            <p>We store your email with Resend, our email provider. Sharing your clinic software is optional; it helps us decide what to build.</p>
            <p>Your email and data never leaves our servers.</p>
            <p>We count page visits with Vercel Analytics, which uses no cookies and doesn’t identify you.</p>
          </>}
        </article>
      </dialog>
    </>
  );
}
