import { beforeEach, describe, expect, it, vi } from "vitest";

const create = vi.fn();
const get = vi.fn();
const update = vi.fn();
const send = vi.fn();

vi.mock("resend", () => ({
  Resend: class {
    contacts = { create, get, update };
    emails = { send };
  },
}));

// Run post-response work inline so the test can see the send.
vi.mock("next/server", () => ({ after: (task: () => Promise<void>) => void task() }));

vi.mock("next/headers", () => ({
  headers: async () => new Headers({ "x-forwarded-for": "203.0.113.7" }),
}));

import { subscribe } from "./actions";

function form(fields: Record<string, string>) {
  const f = new FormData();
  for (const [k, v] of Object.entries(fields)) f.set(k, v);
  return f;
}

describe("subscribe", () => {
  beforeEach(() => {
    create.mockReset();
    update.mockReset().mockResolvedValue({ data: { id: "c_5" }, error: null });
    get.mockReset().mockResolvedValue({ data: null, error: { name: "not_found", message: "Contact not found" } });
    send.mockReset().mockResolvedValue({ data: { id: "e_1" }, error: null });
    process.env.RESEND_API_KEY = "re_test_key";
  });

  it("stores a valid signup as a Resend contact with the PMS answer", async () => {
    create.mockResolvedValue({ data: { id: "c_1" }, error: null });
    const state = await subscribe({ status: "idle" }, form({ email: "Desk@Clinic.ca", pms: "ClearDent" }));
    expect(state).toEqual({ status: "ok" });
    expect(create).toHaveBeenCalledWith({
      email: "desk@clinic.ca",
      unsubscribed: false,
      properties: { pms: "ClearDent" },
    });
  });

  it("keeps the signup when Resend rejects the PMS property", async () => {
    create
      .mockResolvedValueOnce({ data: null, error: { message: "Property pms not found" } })
      .mockResolvedValueOnce({ data: { id: "c_2" }, error: null });
    const state = await subscribe({ status: "idle" }, form({ email: "desk@clinic.ca", pms: "Tracker" }));
    expect(state).toEqual({ status: "ok" });
    expect(create).toHaveBeenLastCalledWith({ email: "desk@clinic.ca", unsubscribed: false });
  });

  it("sends the welcome note to a new signup, keyed so a double submit sends once", async () => {
    create.mockResolvedValue({ data: { id: "c_3" }, error: null });
    await subscribe({ status: "idle" }, form({ email: "desk@clinic.ca" }));
    expect(send).toHaveBeenCalledTimes(1);
    const [email, options] = send.mock.calls[0];
    expect(email).toMatchObject({ to: "desk@clinic.ca", replyTo: "hello@ophi.app" });
    expect(options.idempotencyKey).toMatch(/^welcome\/[0-9a-f]{64}$/);
  });

  it("does not send the welcome note again to an address already on the list", async () => {
    get.mockResolvedValue({ data: { id: "c_4", email: "desk@clinic.ca" }, error: null });
    create.mockResolvedValue({ data: null, error: { message: "Contact already exists" } });
    const state = await subscribe({ status: "idle" }, form({ email: "desk@clinic.ca" }));
    expect(state).toEqual({ status: "ok" });
    expect(send).not.toHaveBeenCalled();
  });

  it("puts someone who unsubscribed back on the list and welcomes them", async () => {
    get.mockResolvedValue({ data: { id: "c_5", email: "desk@clinic.ca", unsubscribed: true }, error: null });
    const state = await subscribe({ status: "idle" }, form({ email: "desk@clinic.ca" }));
    expect(state).toEqual({ status: "ok" });
    expect(update).toHaveBeenCalledWith({ email: "desk@clinic.ca", unsubscribed: false });
    expect(create).not.toHaveBeenCalled();
    expect(send).toHaveBeenCalledTimes(1);
  });

  it("gives a bot the success screen without calling Resend", async () => {
    const state = await subscribe({ status: "idle" }, form({ email: "bot@x.ca", hp_ref: "filled" }));
    expect(state).toEqual({ status: "ok" });
    expect(create).not.toHaveBeenCalled();
    expect(send).not.toHaveBeenCalled();
  });
});
