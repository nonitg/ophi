import type { Metadata } from "next";
import Link from "next/link";
import { JsonLd } from "@/components/json-ld";
import { copy } from "@/lib/copy";

export const metadata: Metadata = {
  title: "Privacy at Ophi",
  description:
    "How Ophi handles dental scheduling calls, what staff approve, where requests are held, and what to review before a clinic pilot.",
  alternates: { canonical: "/privacy" },
};

const UPDATED = "November 20, 2026";
const mail = copy.contactEmail;

const h2 = "mt-12 text-[22px] leading-[1.25] tracking-[-.4px]";
const p = "mt-3 text-[14px] leading-[1.75] text-muted";
const li = "text-[14px] leading-[1.7] text-muted";
const link = "text-ink underline decoration-pill-line underline-offset-4 hover:decoration-ink";

export default function Privacy() {
  return (
    <main className="mx-auto w-full max-w-2xl px-6 py-12 sm:py-16">
      <nav aria-label="Breadcrumb" className="mb-8 text-[12px]">
        <ol className="flex flex-wrap gap-x-2 text-muted">
          <li><Link href="/" className="hover:underline">Ophi</Link></li>
          <li aria-hidden="true">/</li>
          <li aria-current="page">Privacy</li>
        </ol>
      </nav>

      <h1 className="text-[34px] leading-[1.1] tracking-[-1.2px] sm:text-[42px]">Privacy at Ophi</h1>
      <p className={p}>Updated {UPDATED}. For dental clinics, their patients and visitors to ophi.app.</p>

      <section className="mt-8 rounded-[8px] bg-sage p-6" aria-labelledby="calls">
        <h2 id="calls" className="text-[22px] leading-tight">When Ophi answers your clinic’s phone</h2>
        <p className={p}>Ophi helps callers arrange dental visits. It checks the caller’s name and date of birth before sharing appointment details. It looks up available times and sends a request to your staff. A call alone cannot change the schedule. A staff member must approve a request before Ophi writes to your practice management system.</p>
        <p className={p}>While staff review a request, the call server holds patient details in memory. The hosted demo runs in Ohio and uses fictional clinic records. By default, unanswered requests expire after 24 hours. The server removes a request about an hour after approval, rejection or expiry.</p>
        <p className={p}>Call audio and text pass through outside providers and may be processed in the United States. Before using Ophi with patients, review the providers, account settings and access permissions for your clinic with our team.</p>
      </section>

      <h2 className={h2}>What a caller hears</h2>
      <blockquote className="mt-3 border-l-2 border-pill-line pl-4">“Hi, I’m Ophi, the office’s AI assistant. How can I help you today?”</blockquote>
      <p className={p}>Callers can ask for a person at any time. When a staff line is configured, Ophi rings it and leaves a callback request for the team in case nobody answers, including after hours. Without a staff line, Ophi can take a message. Ophi handles scheduling and directs clinical questions to your team.</p>

      <h2 className={h2}>What Ophi can do in your records</h2>
      <p className={p}>Ophi uses identifying details, upcoming appointments, provider schedules and visit types for booking. A new-patient request can also include contact and insurance details. Staff can decline a request without changing the patient’s record.</p>
      <p className={p}>The available changes depend on your software. The demo can move and cancel appointments. The ABELDent connection implements patient creation and booking. Moving and cancelling in ABELDent are not available. Writes are rolled back by default until enabled. The account your clinic connects may have broader permissions than the actions Ophi offers. Ask to see the account’s permissions and a test booking before enabling writes.</p>

      <h2 className={h2}>What remains after a call</h2>
      <p className={p}>A pending booking can include a name, date of birth, requested visit and contact details. A callback can include a name, phone number and the caller’s message, including health details they volunteer. The dashboard shows these items to people with clinic dashboard access. Ophi operators with server access can also reach them.</p>
      <p className={p}>With call logging off, Ophi drops the conversation transcript when the call ends and does not write a call recording. A separate diagnostic setting can save audio, transcripts and detailed logs for development. Confirm it is off for patient calls. The queue’s expiry times apply to the call server’s memory. Approved changes remain in the clinic’s records. If after-hours email is enabled, appointment details can also remain in the sending service and clinic mailbox.</p>

      <h2 className={h2}>Who handles call information</h2>
      <p className={p}>Ophi selects the speech and language services in the call configuration. The table lists the available choices. For a live pilot, ask for the selected provider at each step, its processing region, how long it keeps content and service logs, and whether its account terms permit model training. The demo configuration alone cannot establish those terms.</p>
      <table className="mt-4 w-full text-left text-[14px] leading-relaxed">
        <caption className="sr-only">Call services and information they receive</caption>
        <thead><tr className="border-b border-line"><th scope="col" className="py-2 pr-4">Provider</th><th scope="col">Information handled</th></tr></thead>
        <tbody>
          {[
            ["Telnyx", "Phone numbers, call timing and audio for the call and staff transfer."],
            ["Amazon Web Services", "Hosts the call server. The Ohio demo server processes audio, conversation text and pending staff requests."],
            ["AssemblyAI, Deepgram or Cartesia", "Receives caller audio to turn speech into text."],
            ["Cerebras, Baseten, Groq or Anthropic", "Receives conversation text, clinic instructions and scheduling lookup results to generate a reply."],
            ["ElevenLabs or Cartesia", "Receives the words of Ophi’s reply to turn them into speech."],
            ["Clinic email provider, if enabled", "Receives approved after-hours appointment details, which can include the patient’s name, visit time and reason."],
          ].map(([provider, detail]) => (
            <tr key={provider} className="border-b border-line align-top">
              <th scope="row" className="w-2/5 py-3 pr-4 font-medium">{provider}</th>
              <td className="py-3 text-muted">{detail}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className={p}>We tell the clinic before adding a provider. We do not sell patient information, use it for advertising or combine it with another clinic’s information.</p>

      <h2 className={h2}>Before your first patient call</h2>
      <p className={p}>Your clinic remains the health information custodian in Ontario. Ophi acts on the clinic’s instructions as its agent. Ophi is operated by its founders. We do not yet have a signed clinic pilot agreement. To arrange a walkthrough with a fictional patient or discuss written terms for your clinic, <a className={link} href={`mailto:${mail}?subject=Clinic%20pilot%20privacy%20review`}>contact the Ophi team</a>.</p>
      <p className={p}>Review who signs for Ophi, who handles urgent incidents, who may access patient requests for support, and what record of that access your clinic can inspect. Clinic dashboard connections are encrypted in transit. The current dashboard uses a shared password, so a dashboard action alone does not identify the individual staff member. Agree on access and log retention with the pilot team before connecting your records.</p>

      <h2 className={h2}>Stopping a pilot</h2>
      <p className={p}>Have your phone administrator restore the clinic’s usual call routing and test an incoming call. Have your practice software administrator revoke Ophi’s connection. Disconnecting the records alone does not redirect the phone line. Review outstanding callbacks with staff before shutting down the call server, because a restart clears its in-memory queue. Confirm with Ophi which provider logs, emails and clinic records remain and when each can be deleted.</p>

      <h2 className={h2}>If something goes wrong</h2>
      <p className={p}>Contact the Ophi team about the phone service, even if you first notice the problem in your appointment book. We investigate the call service and involve the affected provider. Your clinic coordinates the response for its patients and can involve its practice software vendor when its system is affected.</p>
      <p className={p}>If we learn of a security incident or suspected unauthorized access affecting patient information, a live call or your clinic connection, we will notify your designated clinic contact at the first reasonable opportunity and within 72 hours of learning of it. We will share what we know, what we have done to contain it and when you can expect an update.</p>
      <p className={p}>To report a concern, <a className={link} href={`mailto:${mail}?subject=Clinic%20privacy%20incident`}>email Ophi about a privacy incident</a> with your clinic name and a callback number. Keep patient details out of email. Patients can contact their clinic about their records.</p>

      <h2 className={h2}>Website visitors</h2>
      <ul className="mt-3 grid list-disc gap-2 pl-5">
        <li className={li}><strong className="font-medium text-ink">Waitlist form:</strong> your email address, and the clinic software you use if you choose to say. We use them to write to you about Ophi’s launch and progress.</li>
        <li className={li}><strong className="font-medium text-ink">Film page:</strong> if you leave a name or phone number, we email them to our team so someone can follow up. They are not added to the mailing list record.</li>
        <li className={li}><strong className="font-medium text-ink">Page visits:</strong> counted with Vercel Analytics, which sets no cookies and does not identify you.</li>
        <li className={li}><strong className="font-medium text-ink">Your connection:</strong> we use your IP address in server memory to limit repeated submissions within a one-minute window. The form does not write it to a database.</li>
      </ul>
      <p className={p}>
        Please do not put patient or health information into any form on this site or into an email to {mail}. We have no use for it there and the site is not built to hold it.
      </p>

      <h2 className={h2}>Who handles website information</h2>
      <ul className="mt-3 grid list-disc gap-2 pl-5">
        <li className={li}><strong className="font-medium text-ink">Resend</strong> stores the mailing list and sends our emails.</li>
        <li className={li}><strong className="font-medium text-ink">Vercel</strong> hosts the site and provides the analytics.</li>
      </ul>
      <p className={p}>
        We never sell or rent your details. Both are US-based companies, so your email address can be processed outside Canada. We share your details with no one else, and we use them for no purpose beyond the ones above.
      </p>

      <h2 className={h2}>Your website and email choices</h2>
      <p className={p}>
        To stop our emails, reply to any of them with “unsubscribe.” To see, correct or delete what we hold about you, or to withdraw your consent, write to <a className={link} href={`mailto:${mail}`}>{mail}</a>. We answer within 30 days. If you are not satisfied, you may complain to the Office of the Privacy Commissioner of Canada.
      </p>

      <h2 className={h2}>Changes and contact</h2>
      <p className={p}>
        When we change this page, we change the date at the top. If a change affects how we treat information you already gave us, we will email you first. Questions about privacy go to <a className={link} href={`mailto:${mail}`}>{mail}</a>.
      </p>

      <JsonLd data={{ "@context": "https://schema.org", "@type": "WebPage", name: "Privacy at Ophi", url: "https://ophi.app/privacy", inLanguage: "en-CA" }} />
    </main>
  );
}
