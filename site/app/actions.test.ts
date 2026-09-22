import { beforeEach, describe, expect, it, vi } from "vitest";

const create = vi.fn();

vi.mock("resend", () => ({
  Resend: class {
    contacts = { create };
  },
}));

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

  it("gives a bot the success screen without calling Resend", async () => {
    const state = await subscribe({ status: "idle" }, form({ email: "bot@x.ca", hp_ref: "filled" }));
    expect(state).toEqual({ status: "ok" });
    expect(create).not.toHaveBeenCalled();
  });
});
