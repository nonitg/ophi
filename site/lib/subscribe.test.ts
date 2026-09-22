import { describe, expect, it } from "vitest";
import { EMAIL_ERROR, parseSubscription } from "./subscribe";

function form(fields: Record<string, string>) {
  const f = new FormData();
  for (const [k, v] of Object.entries(fields)) f.set(k, v);
  return f;
}

describe("parseSubscription", () => {
  it("accepts an email with an optional PMS and normalises case", () => {
    const parsed = parseSubscription(form({ email: " Front.Desk@Clinic.CA ", pms: "ClearDent" }));
    expect(parsed).toEqual({ ok: true, email: "front.desk@clinic.ca", pms: "ClearDent", bot: false });
  });

  it("rejects a malformed email with the copy the form shows", () => {
    expect(parseSubscription(form({ email: "front-desk" }))).toEqual({ ok: false, error: EMAIL_ERROR });
  });

  it("flags a filled honeypot as a bot without rejecting it", () => {
    const parsed = parseSubscription(form({ email: "a@b.ca", hp_ref: "http://spam" }));
    expect(parsed).toMatchObject({ ok: true, bot: true });
  });
});
