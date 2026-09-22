import { describe, expect, it } from "vitest";
import { copy } from "@/lib/copy";
import { confirmationEmail } from "./confirmation-email";

describe("confirmationEmail", () => {
  it("links the clinic survey, offers a way out, and stays inside the copy law", () => {
    const email = confirmationEmail("desk@clinic.ca");
    expect(email.to).toBe("desk@clinic.ca");
    for (const body of [email.html, email.text]) {
      expect(body).toContain(copy.survey.href);
      expect(body).toContain("reply with “unsubscribe”");
      expect(body).not.toMatch(/\b(approved|eligible|covered|colombus)\b/i);
    }
    expect(email.headers?.["List-Unsubscribe"]).toBe("<mailto:hello@ophi.app?subject=unsubscribe>");
  });
});
