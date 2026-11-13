import { describe, expect, it } from "vitest";
import { leadNote, parseLead } from "./lead";

function form(fields: Record<string, string>) {
  const f = new FormData();
  for (const [k, v] of Object.entries(fields)) f.set(k, v);
  return f;
}

describe("parseLead", () => {
  it("keeps the name and number someone left with their email", () => {
    const lead = parseLead(form({ email: "Owner@Clinic.ca", name: "  Dana\n Lee ", phone: "604 555 0100", pms: "Tracker" }));
    expect(lead).toEqual({ email: "owner@clinic.ca", name: "Dana Lee", phone: "604 555 0100", pms: "Tracker" });
  });

  it("is null for a plain signup and for a bot", () => {
    expect(parseLead(form({ email: "owner@clinic.ca" }))).toBeNull();
    expect(parseLead(form({ email: "owner@clinic.ca", name: "Dana", hp_ref: "spam" }))).toBeNull();
  });
});

describe("leadNote", () => {
  it("goes to the team, lists only what was given, and replies to the lead", () => {
    const note = leadNote({ email: "owner@clinic.ca", phone: "604 555 0100" });
    expect(note).toMatchObject({ to: "hello@ophi.app", replyTo: "owner@clinic.ca", text: "Email: owner@clinic.ca\nPhone: 604 555 0100" });
  });
});
