import type { CreateEmailOptions } from "resend";
import { copy } from "@/lib/copy";
import type { Pms } from "@/lib/pms";
import { parseSubscription } from "@/lib/subscribe";

// Someone on the film page who left more than an email: a person the team can call or write to by name.
export type Lead = { email: string; pms?: Pms; name?: string; phone?: string };

// One line, bounded: these go into an email to the team as typed.
const clean = (value: FormDataEntryValue | null, max: number) => String(value ?? "").replace(/\s+/g, " ").trim().slice(0, max) || undefined;

// Null for bots, bad emails and plain signups, which need no follow-up beyond the waitlist.
export function parseLead(form: FormData): Lead | null {
  const signup = parseSubscription(form);
  const name = clean(form.get("name"), 120);
  const phone = clean(form.get("phone"), 40);
  if (!signup.ok || signup.bot || !(name || phone)) return null;
  return { email: signup.email, pms: signup.pms, name, phone };
}

// The note that reaches the team's inbox, so a name and number never depend on how the contact list is set up.
export function leadNote(lead: Lead): CreateEmailOptions {
  const rows = [["Email", lead.email], ["Name", lead.name], ["Phone", lead.phone], ["Clinic software", lead.pms]];
  return {
    from: "Ophi film page <site@updates.ophi.app>",
    to: copy.contactEmail,
    replyTo: lead.email,
    subject: `Film page: ${lead.name ?? lead.email} left their details`,
    text: rows.filter(([, value]) => value).map(([label, value]) => `${label}: ${value}`).join("\n"),
  };
}
