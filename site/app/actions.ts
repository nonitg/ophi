"use server";

import { createHash } from "node:crypto";
import { headers } from "next/headers";
import { after } from "next/server";
import { Resend } from "resend";
import { confirmationEmail } from "@/lib/confirmation-email";
import { parseSubscription } from "@/lib/subscribe";

export type SubscribeState =
  | { status: "idle" }
  | { status: "ok" }
  | { status: "error"; message: string; field?: "email" };

// Per-instance sliding window. Enough to blunt a script; not a substitute for a WAF.
const WINDOW_MS = 60_000;
const LIMIT = 5;
const hits = new Map<string, number[]>();
const SAVE_FAILED: SubscribeState = { status: "error", message: "We couldn't save that just now. Try again in a moment." };

function rateLimited(ip: string): boolean {
  const now = Date.now();
  const recent = (hits.get(ip) ?? []).filter((t) => now - t < WINDOW_MS);
  recent.push(now);
  hits.set(ip, recent);
  return recent.length > LIMIT;
}

async function clientIp(): Promise<string> {
  const h = await headers();
  return (h.get("x-forwarded-for") ?? "").split(",")[0].trim() || "unknown";
}

export async function subscribe(_prev: SubscribeState, form: FormData): Promise<SubscribeState> {
  const parsed = parseSubscription(form);
  if (!parsed.ok) return { status: "error", message: parsed.error, field: "email" };
  // Bots get the same success screen as people, so they learn nothing.
  if (parsed.bot) return { status: "ok" };

  if (rateLimited(await clientIp())) {
    return { status: "error", message: "Too many attempts from this connection. Try again in a minute." };
  }

  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    if (process.env.NODE_ENV !== "production") {
      console.log("[subscribe] no RESEND_API_KEY; would save and send the welcome note to", parsed.email, parsed.pms ?? "");
      return { status: "ok" };
    }
    return { status: "error", message: "Signups are not open yet. Try again later." };
  }

  const resend = new Resend(apiKey);
  const lookup = await resend.contacts.get({ email: parsed.email });
  // Submitting the form again is a fresh opt-in, so someone who unsubscribed is back on the list (owner's decision).
  if (lookup.data?.unsubscribed) {
    const { error } = await resend.contacts.update({ email: parsed.email, unsubscribed: false });
    if (error) {
      console.error("[subscribe] resend rejoin error", error);
      return SAVE_FAILED;
    }
    return welcome(resend, parsed.email);
  }

  const contact = { email: parsed.email, unsubscribed: false };
  let { error } = await resend.contacts.create({
    ...contact,
    properties: parsed.pms ? { pms: parsed.pms } : undefined,
  });
  // The software answer is a nice-to-have; never lose the signup over it (e.g. property not yet defined in Resend).
  if (error && parsed.pms && !/already|exist/i.test(error.message)) {
    console.error("[subscribe] resend rejected pms property, retrying without it", error);
    ({ error } = await resend.contacts.create(contact));
  }

  // An address already on the list is a success from the reader's side.
  if (error && !/already|exist/i.test(error.message)) {
    console.error("[subscribe] resend error", error);
    return SAVE_FAILED;
  }
  // Re-entering a listed address, anyone's, must not make Ophi email it again.
  // Any lookup failure other than "not found" counts as listed, so an unsure answer never sends.
  if (lookup.error?.name !== "not_found") return { status: "ok" };
  return welcome(resend, parsed.email);
}

// Sent after the response, so a slow or failed send never delays or loses the signup.
// The key (a hash, keeping the address out of it) stops racing double submits both sending. It holds for one minute,
// not the 24 h Resend remembers keys, so a later rejoin still gets its note.
function welcome(resend: Resend, email: string): SubscribeState {
  const minute = Math.floor(Date.now() / 60_000);
  const idempotencyKey = `welcome/${createHash("sha256").update(`${email}:${minute}`).digest("hex")}`;
  after(async () => {
    const { error } = await resend.emails.send(confirmationEmail(email), { idempotencyKey });
    if (error) console.error("[subscribe] welcome note failed", error);
  });
  return { status: "ok" };
}
