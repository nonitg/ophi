"use server";

import { headers } from "next/headers";
import { Resend } from "resend";
import { parseSubscription } from "@/lib/subscribe";

export type SubscribeState =
  | { status: "idle" }
  | { status: "ok" }
  | { status: "error"; message: string; field?: "email" };

// Per-instance sliding window. Enough to blunt a script; not a substitute for a WAF.
const WINDOW_MS = 60_000;
const LIMIT = 5;
const hits = new Map<string, number[]>();

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
      console.log("[subscribe] no RESEND_API_KEY; would save", parsed.email, parsed.pms ?? "");
      return { status: "ok" };
    }
    return { status: "error", message: "Signups are not open yet. Try again later." };
  }

  const resend = new Resend(apiKey);
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
    return { status: "error", message: "We couldn't save that just now. Try again in a moment." };
  }
  return { status: "ok" };
}
