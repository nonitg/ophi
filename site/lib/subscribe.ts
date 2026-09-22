import { z } from "zod";

// Canadian clinic PMS list first, then exits for readers who are not clinic staff.
// The answer steers which integration ships first, so the labels match how clinics name them.
export const PMS_OPTIONS = [
  "ABELDent",
  "ClearDent",
  "Dentrix",
  "Tracker",
  "Open Dental",
  "Paradigm",
  "Power Practice",
  "Curve",
  "Dentitek",
  "Progident",
  "Other",
  "I don't work in a clinic",
] as const;

export type Pms = (typeof PMS_OPTIONS)[number];

const schema = z.object({
  email: z.email().max(254),
  pms: z.enum(PMS_OPTIONS).optional(),
});

export type ParsedSubscription =
  | { ok: true; email: string; pms?: Pms; bot: boolean }
  | { ok: false; error: string };

export const EMAIL_ERROR = "Enter a full email address, like you@example.com.";

export const HONEYPOT_FIELD = "hp_ref";

// The honeypot field is invisible to people; anything in it marks the submission as a bot.
export function parseSubscription(form: FormData): ParsedSubscription {
  const bot = String(form.get(HONEYPOT_FIELD) ?? "").trim() !== "";
  const email = String(form.get("email") ?? "").trim().toLowerCase();
  const pmsRaw = String(form.get("pms") ?? "").trim();
  const result = schema.safeParse({ email, pms: pmsRaw || undefined });
  if (!result.success) return { ok: false, error: EMAIL_ERROR };
  return { ok: true, email: result.data.email, pms: result.data.pms, bot };
}
