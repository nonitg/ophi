import type { CreateEmailOptions } from "resend";
import { copy } from "@/lib/copy";

// A named person, not a brand: Gmail files personal senders in Primary more often than Promotions.
const FROM = "Nonit at Ophi <nonit@updates.ophi.app>";

const text = {
  subject: "You’re on the Ophi waitlist",
  greeting: "Hi,",
  intro: "Thanks for joining the Ophi waitlist. We’re building for dental teams who’d rather spend their time on people, and we’ll write when there’s something to share.",
  survey: "Dentist, or work at a clinic? Tell us where the paperwork slows your team down. The survey takes 3–4 minutes, and your answers shape what we build first:",
  surveyAction: "Take the survey",
  // A reply is Gmail's strongest sign that a sender is wanted, so the note asks for one.
  reply: "Or just hit reply and tell us what you do. I read every reply.",
  signoff: "Thanks for being here early,",
  name: "Nonit",
  reason: "You’re getting this because you joined the Ophi waitlist at ophi.app. To stop hearing from us, reply with “unsubscribe”.",
  sender: `Sent by Ophi. Write to us anytime at ${copy.contactEmail}.`,
};

// Plain paragraphs with no layout, colour or button, so it reads as a note from a person rather than a newsletter.
const p = (body: string) => `<p style="margin:0 0 16px;">${body}</p>`;
const html = `<!doctype html>
<html lang="en-CA">
<head><meta charset="utf-8"><title>${text.subject}</title></head>
<body>
<div style="max-width:560px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.5;color:#222;">
${p(text.greeting)}
${p(text.intro)}
${p(`${text.survey} <a href="${copy.survey.href}">${text.surveyAction}</a>`)}
${p(text.reply)}
${p(`${text.signoff}<br>${text.name}<br>Ophi`)}
<p style="margin:32px 0 0;font-size:12px;color:#666;">${text.reason}<br>${text.sender}</p>
</div>
</body>
</html>`;

const plain = [
  text.greeting,
  text.intro,
  `${text.survey}\n${copy.survey.href}`,
  text.reply,
  `${text.signoff}\n${text.name}\nOphi`,
  "—",
  text.reason,
  text.sender,
].join("\n\n");

// The note a new signup gets right away. Nothing from the reader goes into it except the address it is sent to.
// CASL's way out is the reply-to-unsubscribe line; a List-Unsubscribe header would mark it as bulk mail.
export function confirmationEmail(to: string): CreateEmailOptions {
  return {
    from: FROM,
    to,
    replyTo: copy.contactEmail,
    subject: text.subject,
    html,
    text: plain,
  };
}
