"use server";

import { after } from "next/server";
import { Resend } from "resend";
import { subscribe, type SubscribeState } from "@/app/actions";
import { leadNote, parseLead } from "@/lib/lead";

// The film page's form: the homepage's waitlist signup, unchanged, then a note to the team when the reader
// also left a name or a number.
export async function leaveDetails(prev: SubscribeState, form: FormData): Promise<SubscribeState> {
  const state = await subscribe(prev, form);
  const lead = parseLead(form);
  if (state.status !== "ok" || !lead) return state;

  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    console.log("[film page] no RESEND_API_KEY; would tell the team about", lead.email);
    return state;
  }
  // After the response, like the welcome note: a slow or failed send never costs the signup.
  after(async () => {
    const { error } = await new Resend(apiKey).emails.send(leadNote(lead));
    if (error) console.error("[film page] note to the team failed", error);
  });
  return state;
}
