"use client";

import { useActionState, useEffect, useLayoutEffect, useRef, useState } from "react";
import { track } from "@vercel/analytics";
import { subscribe, type SubscribeState } from "@/app/actions";
import { copy } from "@/lib/copy";
import { Icon } from "@/components/icons";
import { PmsSelect } from "@/components/pms-select";

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
    <div ref={wrap} className="waitlist" data-done={done || undefined}>
      <form action={action} onSubmit={measure} noValidate className="waitlist-form" aria-busy={pending} inert={done}>
        <div className="email-row">
          <label className="sr-only" htmlFor="email">{copy.form.email}</label>
          <input ref={emailInput} id="email" name="email" type="email" autoComplete="email" inputMode="email" placeholder={copy.form.emailPlaceholder} value={email} onChange={(event) => setEmail(event.target.value)} required aria-invalid={invalid || undefined} aria-describedby={failed ? "email-error consent" : "consent"} />
          <button type="submit" disabled={pending} className="join-button">{pending ? copy.form.submitting : copy.form.submit}<Icon name="arrow" /></button>
        </div>
        {failed && <p id="email-error" role="alert" className="waitlist-error">{state.message}</p>}
        <PmsSelect />
        {/* The honeypot name deliberately avoids browser autofill vocabularies. */}
        <div className="honeypot" aria-hidden="true"><label htmlFor="hp_ref">Reference</label><input id="hp_ref" name="hp_ref" type="text" tabIndex={-1} autoComplete="off" /></div>
        <p id="consent" className="waitlist-consent">{copy.form.consent}</p>
      </form>
      {done && (
        <div ref={success} tabIndex={-1} role="status" className="waitlist-success">
          <p className="success-line"><strong>{copy.form.success}</strong><span className="success-tag"><Icon name="check" /></span></p>
          <p className="success-detail">{copy.form.successDetail} <span>{email.trim()}</span>.</p>
          {/* The moment of highest intent: clinic staff who just joined can tell us how their paperwork goes. */}
          <a className="pill survey-link" href={copy.survey.href} target="_blank" rel="noopener">{copy.survey.label}<span className="pill-tag"><Icon name="arrow" /></span></a>
        </div>
      )}
    </div>
  );
}
