import { z } from "zod";
import { PMS_OPTIONS, type Pms } from "@/lib/pms";

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
