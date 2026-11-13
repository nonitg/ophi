import { beforeEach, describe, expect, it, vi } from "vitest";

const create = vi.fn();
const get = vi.fn();
const send = vi.fn();

vi.mock("resend", () => ({
  Resend: class {
    contacts = { create, get };
    emails = { send };
  },
}));

// Run post-response work inline so the test can see the sends.
vi.mock("next/server", () => ({ after: (task: () => Promise<void>) => void task() }));
vi.mock("next/headers", () => ({ headers: async () => new Headers({ "x-forwarded-for": "203.0.113.200" }) }));

import { leaveDetails } from "./actions";

function form(fields: Record<string, string>) {
  const f = new FormData();
  for (const [k, v] of Object.entries(fields)) f.set(k, v);
  return f;
}

describe("leaveDetails", () => {
  beforeEach(() => {
    create.mockReset().mockResolvedValue({ data: { id: "c_1" }, error: null });
    get.mockReset().mockResolvedValue({ data: null, error: { name: "not_found", message: "Contact not found" } });
    send.mockReset().mockResolvedValue({ data: { id: "e_1" }, error: null });
    process.env.RESEND_API_KEY = "re_test_key";
  });

  it("joins the waitlist and tells the team the name and number", async () => {
    const state = await leaveDetails({ status: "idle" }, form({ email: "owner@clinic.ca", name: "Dana Lee", phone: "604 555 0100" }));
    expect(state).toEqual({ status: "ok" });
    expect(create).toHaveBeenCalledWith({ email: "owner@clinic.ca", unsubscribed: false, properties: undefined });
    await vi.waitFor(() => expect(send).toHaveBeenCalledWith(expect.objectContaining({ to: "hello@ophi.app", text: "Email: owner@clinic.ca\nName: Dana Lee\nPhone: 604 555 0100" })));
  });

  it("sends the team nothing for an email alone", async () => {
    await leaveDetails({ status: "idle" }, form({ email: "owner@clinic.ca" }));
    await vi.waitFor(() => expect(send).toHaveBeenCalledTimes(1)); // the welcome note only
  });
});
