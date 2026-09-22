"use client";

import { useActionState, useEffect, useRef, useState } from "react";
import { track } from "@vercel/analytics";
import { subscribe, type SubscribeState } from "@/app/actions";
import { copy } from "@/lib/copy";
import { Icon } from "@/components/icons";
import { PmsSelect } from "@/components/pms-select";

const initial: SubscribeState = { status: "idle" };

export function WaitlistForm() {
  const [state, action, pending] = useActionState(subscribe, initial);
  const [email, setEmail] = useState("");
  const emailInput = useRef<HTMLInputElement>(null);
  const success = useRef<HTMLDivElement>(null);
  const failed = state.status === "error";
  const invalid = failed && state.field === "email";
  // Each submit result moves focus to where the reader must look next.
  useEffect(() => {
    if (state.status === "error") emailInput.current?.focus();
    if (state.status === "ok") { success.current?.focus(); track("waitlist_join"); }
  }, [state]);
  if (state.status === "ok") {
    return <div ref={success} tabIndex={-1} role="status" className="waitlist-success"><span><Icon name="check" /></span><p><strong>{copy.form.success}</strong><br />{copy.form.successDetail}</p></div>;
  }
  return (
    <form action={action} noValidate className="waitlist-form" aria-busy={pending}>
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
  );
}
