import type { CreateEmailOptions } from "resend";
import { copy } from "@/lib/copy";

const FROM = "Ophi <hello@updates.ophi.app>";

// The page's paper, ink and orange, so the note reads as the same sheet the reader just signed.
const c = { paper: "#f4f2e9", ink: "#193a30", soft: "#425e51", muted: "#5c6557", orange: "#ef865b", sage: "#e4e7d9", line: "#d4d9c9" };
const serif = "Newsreader, Georgia, 'Times New Roman', serif";
const sans = "'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif";

const text = {
  subject: "You’re on the Ophi waitlist",
  preview: "Thanks for joining. One small favour if you work at a clinic.",
  heading: "You’re on the list.",
  intro: "Thanks for joining. We’re building for dental teams who’d rather spend their time on people, and we’ll write when there’s something to share.",
  surveyHeading: "Dentist, or work at a clinic?",
  surveyBody: "Tell us where the paperwork slows your team down. The survey takes 3–4 minutes, and your answers shape what we build first. We’d really appreciate it.",
  surveyAction: "Take the survey",
  signoff: "Thanks for being here early,",
  reason: "You’re getting this because you joined the Ophi waitlist at ophi.app. To stop hearing from us, reply with “unsubscribe”.",
  sender: `Sent by Ophi. Write to us anytime at ${copy.contactEmail}.`,
};

// Table layout and inline styles: the only structure every mail client renders the same way.
const html = `<!doctype html>
<html lang="en-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>${text.subject}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500&family=Newsreader:opsz,wght@6..72,400&display=swap" rel="stylesheet">
<style>
  @media (max-width: 520px) {
    .sheet { padding: 32px 20px 28px !important; }
    .heading { font-size: 30px !important; }
    .survey { padding: 24px 22px !important; }
  }
</style>
</head>
<body style="margin:0;padding:0;background:${c.paper};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">${text.preview}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:${c.paper};">
<tr><td align="center">
<table role="presentation" class="sheet" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;padding:48px 32px 36px;">
  <tr><td style="font-family:${serif};font-size:34px;line-height:1;letter-spacing:-1.5px;color:${c.ink};">ophi<span style="color:${c.orange};">.</span></td></tr>
  <tr><td class="heading" style="padding-top:44px;font-family:${serif};font-size:34px;line-height:1.1;letter-spacing:-0.8px;color:${c.ink};">${text.heading}</td></tr>
  <tr><td style="padding-top:16px;font-family:${sans};font-size:15px;line-height:1.65;color:${c.soft};">${text.intro}</td></tr>
  <tr><td style="padding-top:32px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:${c.sage};border-radius:24px;">
      <tr><td class="survey" style="padding:28px 30px 30px;">
        <div style="font-family:${serif};font-size:22px;line-height:1.2;letter-spacing:-0.4px;color:${c.ink};">${text.surveyHeading}</div>
        <div style="padding-top:10px;font-family:${sans};font-size:14px;line-height:1.65;color:${c.muted};">${text.surveyBody}</div>
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:22px;"><tr>
          <td style="background:${c.orange};border-radius:100px;">
            <a href="${copy.survey.href}" style="display:inline-block;padding:14px 24px;font-family:${sans};font-size:14px;font-weight:500;line-height:1;color:${c.ink};text-decoration:none;border-radius:100px;">${text.surveyAction}</a>
          </td>
        </tr></table>
      </td></tr>
    </table>
  </td></tr>
  <tr><td style="padding-top:32px;font-family:${sans};font-size:15px;line-height:1.65;color:${c.soft};">${text.signoff}<br><span style="font-family:${serif};font-size:20px;color:${c.ink};">Ophi</span></td></tr>
  <tr><td style="padding-top:36px;"><div style="border-top:1px solid ${c.line};font-size:0;line-height:0;">&nbsp;</div></td></tr>
  <tr><td style="padding-top:18px;font-family:${sans};font-size:12px;line-height:1.6;color:${c.muted};">${text.reason}<br>${text.sender}</td></tr>
</table>
</td></tr>
</table>
</body>
</html>`;

const plain = [
  text.heading,
  text.intro,
  `${text.surveyHeading} ${text.surveyBody}`,
  `${text.surveyAction}: ${copy.survey.href}`,
  `${text.signoff}\nOphi`,
  "—",
  text.reason,
  text.sender,
].join("\n\n");

// The note a new signup gets right away. Nothing from the reader goes into it except the address it is sent to.
export function confirmationEmail(to: string): CreateEmailOptions {
  return {
    from: FROM,
    to,
    replyTo: copy.contactEmail,
    subject: text.subject,
    html,
    text: plain,
    // CASL: every send carries a way out; replies land in the owner's inbox.
    headers: { "List-Unsubscribe": `<mailto:${copy.contactEmail}?subject=unsubscribe>` },
  };
}
