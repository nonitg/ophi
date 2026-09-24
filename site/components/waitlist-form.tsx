"use client";

import { useActionState, useEffect, useLayoutEffect, useRef, useState } from "react";
import { track } from "@vercel/analytics";
import { subscribe, type SubscribeState } from "@/app/actions";
import { copy } from "@/lib/copy";
import { Icon } from "@/components/icons";
import { PmsSelect } from "@/components/pms-select";
import { pill, pillIcon, pillTag } from "@/components/pill";

const initial: SubscribeState = { status: "idle" };

export function WaitlistForm() {
  const [state, action, pending] = useActionState(subscribe, initial);
  const [email, setEmail] = useState("");
  const wrap = useRef<HTMLDivElement>(null);
  const formHeight = useRef(0);
  const emailInput = useRef<HTMLInputElement>(null);
  const success = useRef<HTMLDivElement>(null);
  const done = state.status === "ok";
  const failed = state.status === "error";
  const invalid = failed && state.field === "email";
  // Each submit result moves focus to where the reader must look next.
  useEffect(() => {
    if (state.status === "error") emailInput.current?.focus();
    if (state.status === "ok") { success.current?.focus({ preventScroll: true }); track("waitlist_join"); }
  }, [state]);
  // The band eases to its new height instead of jolting the page below it.
  useLayoutEffect(() => {
    const el = wrap.current;
    if (!done || !el || !formHeight.current || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    el.animate([{ height: `${formHeight.current}px` }, { height: `${el.offsetHeight}px` }], { duration: 500, easing: "cubic-bezier(.16, 1, .3, 1)" });
  }, [done]);

  // The success state grows out of the form's footprint: the join button closes into the done tag.
  function measure() {
    const el = wrap.current;
    if (!el) return;
    formHeight.current = el.offsetHeight;
    el.style.setProperty("--join-w", `${el.querySelector<HTMLElement>(".join-button")?.offsetWidth ?? 46}px`);
  }

  return (
    <div ref={wrap} className="waitlist relative">
      {/* Once joined, the form stays underneath, faded and inert, so the result takes over the same pill. */}
      <form action={action} onSubmit={measure} noValidate className={`waitlist-form ${done ? "absolute inset-x-0 top-0 z-1 invisible opacity-0 [transition:opacity_.2s_ease-out,visibility_0s_.2s]" : "relative"}`} aria-busy={pending} inert={done}>
        <div className="email-row flex items-center rounded-full border border-[#a3b29b] bg-paper p-[5px] transition-[border-color,background] duration-200 focus-within:border-sage-deep focus-within:bg-[#eef0e6] has-[input[aria-invalid=true]]:border-error xray:border-[#e6ece359] xray:focus-within:border-sage-deep xray:focus-within:bg-paper xray:has-[input[aria-invalid=true]]:border-error">
          <label className="sr-only" htmlFor="email">{copy.form.email}</label>
          {/* Typed email stays 16px on phones so iOS doesn't zoom; the placeholder keeps 14px so it shows whole. */}
          <input ref={emailInput} id="email" name="email" type="email" autoComplete="email" inputMode="email" placeholder={copy.form.emailPlaceholder} value={email} onChange={(event) => setEmail(event.target.value)} required aria-invalid={invalid || undefined} aria-describedby={failed ? "email-error consent" : "consent"}
            className="h-[46px] w-full min-w-0 rounded-[30px] border-0 bg-transparent px-[15px] py-0 text-[14px] text-ink outline-none placeholder:text-[#65715c] placeholder:opacity-100 phone:pr-2 phone:pl-3 phone:text-[16px] phone:placeholder:text-[14px] xray:placeholder:text-muted" />
          {/* Busy, not unavailable: the pill stays solid while its arrow carries the wait. */}
          <button type="submit" disabled={pending} className="group/join join-button inline-flex h-[46px] flex-none items-center justify-between gap-[21px] rounded-full border-0 bg-orange pr-4.5 pl-5 text-[12px] font-medium transition-[background] duration-200 hover:bg-[#f59973] disabled:opacity-100 tablet:gap-3 tablet:px-4 phone:gap-3 phone:px-3.5 phone:text-[11px] small:gap-[7px] small:px-[11px] xray:text-paper xray:shadow-[0_0_28px_-6px_#dff3e6b3] xray:hover:bg-white">
            {pending ? copy.form.submitting : copy.form.submit}
            {/* Joining: the arrow leaves and comes back while the request is out. */}
            <Icon name="arrow" className={`size-[22px] transition-transform duration-350 ease-out group-hover/join:translate-x-0.5 group-hover/join:-translate-y-0.5 tiny:hidden ${pending ? "motion-safe:animate-[send_.9s_var(--ease-out)_infinite]" : ""}`} />
          </button>
        </div>
        {failed && <p id="email-error" role="alert" className="waitlist-error my-2.5 text-[12px] leading-[1.5] text-error">{state.message}</p>}
        <PmsSelect />
        {/* The honeypot name deliberately avoids browser autofill vocabularies. */}
        <div className="sr-only" aria-hidden="true"><label htmlFor="hp_ref">Reference</label><input id="hp_ref" name="hp_ref" type="text" tabIndex={-1} autoComplete="off" /></div>
        <p id="consent" className="mt-2 max-w-[370px] text-[11px] leading-[1.6] text-muted phone:text-pretty">{copy.form.consent}</p>
      </form>
      {done && (
        <div ref={success} tabIndex={-1} role="status" className="waitlist-success focus:outline-none">
          {/* Joined: the button closes into the done tag, the check draws, the field seals into a plain paper pill. */}
          <p className="success-line flex h-[58px] items-center justify-between gap-3 rounded-full border border-transparent bg-paper py-[5px] pr-[5px] pl-5 motion-safe:animate-[seal_.6s_ease-out_both]">
            <strong className="text-[14px] font-medium motion-safe:animate-[write-in_.6s_.18s_var(--ease-out)_both]">{copy.form.success}</strong>
            {/* The done tag, as on "Copied": ink with a paper check. Underneath, the join button closes to a circle before the ink fills it. */}
            <span className="relative isolate grid size-[46px] flex-none place-items-center text-paper before:absolute before:inset-0 before:left-auto before:-z-1 before:w-(--join-w,46px) before:rounded-full before:bg-orange before:[clip-path:inset(1px_1px_1px_calc(100%-45px)_round_100px)] after:absolute after:inset-0 after:-z-1 after:rounded-full after:bg-ink motion-safe:before:animate-[join-close_.5s_.12s_var(--ease-out)_both] motion-safe:after:animate-[ink-fill_.35s_.4s_var(--ease-out)_both]">
              <Icon name="check" className="size-5 motion-safe:[&_path]:[stroke-dasharray:16] motion-safe:[&_path]:animate-[check-draw_.4s_.55s_var(--ease-out)_both]" />
            </span>
          </p>
          <p className="mt-3 text-[13px] leading-[1.6] text-muted motion-safe:animate-[arrive_.5s_.34s_var(--ease-out)_both]">{copy.form.successDetail} <span className="text-ink wrap-anywhere">{email.trim()}</span>.</p>
          {/* The moment of highest intent: clinic staff who just joined can tell us how their paperwork goes. */}
          <a className={pill({ surface: "band", className: "survey-link mt-4 motion-safe:animate-[arrive_.5s_.44s_var(--ease-out)_both]" })} href={copy.survey.href} target="_blank" rel="noopener">{copy.survey.label}<span className={pillTag({ surface: "band" })}><Icon name="arrow" className={pillIcon} /></span></a>
        </div>
      )}
    </div>
  );
}
