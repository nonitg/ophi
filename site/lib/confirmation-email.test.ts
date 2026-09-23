import { describe, expect, it } from "vitest";
import { copy } from "@/lib/copy";
import { confirmationEmail } from "./confirmation-email";

describe("confirmationEmail", () => {
  it("links the clinic survey, invites a reply, offers a way out, and stays inside the copy law", () => {
    const email = confirmationEmail("desk@clinic.ca");
    expect(email.to).toBe("desk@clinic.ca");
    expect(email.replyTo).toBe("hello@ophi.app");
    for (const body of [email.html, email.text]) {
      expect(body).toContain(copy.survey.href);
      expect(body).toContain("hit reply");
      expect(body).toContain("reply with “unsubscribe”");
      expect(body).not.toMatch(/\b(approved|eligible|covered|colombus)\b/i);
    }
    // No bulk-mail header: it steers Gmail toward Promotions.
    expect(email.headers).toBeUndefined();
  });
});
