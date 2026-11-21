import type { Metadata } from "next";
import Link from "next/link";
import { JsonLd } from "@/components/json-ld";
import { copy } from "@/lib/copy";

export const metadata: Metadata = {
  title: "Ophi: privacy and compliance",
  description:
    "What Ophi collects on this site, how it handles clinic and patient information, and which privacy and security standards it does and does not claim.",
  alternates: { canonical: "/privacy" },
};

const UPDATED = "November 20, 2026";
const mail = copy.contactEmail;

// Each row is a claim a clinic can check; keep it to what the code and contracts actually do.
const standards: { name: string; status: string; detail: string }[] = [
  {
    name: "PHIPA (Ontario)",
    status: "Compliant",
    detail:
      "Your clinic is the health information custodian. Ophi acts as its agent and handles patient information only to do the work the clinic asks for. The records stay in your clinic’s practice management system.",
  },
  {
    name: "PIPEDA (federal)",
    status: "Compliant",
    detail:
      "We collect only what a task needs, tell people what we do with it, keep nothing we don’t need, and answer access, correction and deletion requests.",
  },
  {
    name: "CASL (Canada’s anti-spam law)",
    status: "Compliant",
    detail:
      "We email only people who asked to hear from us, say why they are getting each email, and stop when they ask.",
  },
];

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

      <h1 className="text-[34px] leading-[1.1] tracking-[-1.2px] sm:text-[42px]">Privacy and compliance</h1>
      <p className={p}>Last updated {UPDATED}. This page covers ophi.app and the Ophi service for dental clinics.</p>

      <section className="mt-8 rounded-[8px] bg-sage p-6" aria-labelledby="short">
        <h2 id="short" className="text-[19px] leading-[1.3] tracking-[-.3px]">The short version</h2>
        <ul className="mt-3 grid list-disc gap-2 pl-5">
          <li className={li}>This website collects an email address, and sometimes a clinic-software name, a name and a phone number. It collects nothing about anyone’s health.</li>
          <li className={li}>We never sell or rent what you give us.</li>
          <li className={li}>When Ophi works inside a clinic’s records, the clinic stays in charge of them. Ophi acts only for the clinic.</li>
          <li className={li}>Ophi does not keep patient records. It reads and writes your practice management system directly, and the records stay there.</li>
          <li className={li}>We comply with PHIPA, PIPEDA and CASL.</li>
        </ul>
      </section>

      <h2 className={h2}>What this website collects</h2>
      <ul className="mt-3 grid list-disc gap-2 pl-5">
        <li className={li}><strong className="font-medium text-ink">Waitlist form:</strong> your email address, and the clinic software you use if you choose to say. We use them to write to you about Ophi’s launch and progress.</li>
        <li className={li}><strong className="font-medium text-ink">Film page:</strong> if you leave a name or phone number, we email them to our team so someone can follow up. They are not added to the mailing list record.</li>
        <li className={li}><strong className="font-medium text-ink">Page visits:</strong> counted with Vercel Analytics, which sets no cookies and does not identify you.</li>
        <li className={li}><strong className="font-medium text-ink">Your connection:</strong> the form’s spam limit keeps your IP address in server memory for about a minute. We do not write it to a database.</li>
      </ul>
      <p className={p}>
        Please do not put patient or health information into any form on this site or into an email to {mail}. We have no use for it there and the site is not built to hold it.
      </p>

      <h2 className={h2}>Who handles it for us</h2>
      <ul className="mt-3 grid list-disc gap-2 pl-5">
        <li className={li}><strong className="font-medium text-ink">Resend</strong> stores the mailing list and sends our emails.</li>
        <li className={li}><strong className="font-medium text-ink">Vercel</strong> hosts the site and provides the analytics.</li>
      </ul>
      <p className={p}>
        Both are US-based companies, so your email address can be processed outside Canada. We share your details with no one else, and we use them for no purpose beyond the ones above.
      </p>

      <h2 className={h2}>Your choices</h2>
      <p className={p}>
        To stop our emails, reply to any of them with “unsubscribe.” To see, correct or delete what we hold about you, or to withdraw your consent, write to <a className={link} href={`mailto:${mail}`}>{mail}</a>. We answer within 30 days. If you are not satisfied, you may complain to the Office of the Privacy Commissioner of Canada.
      </p>

      <h2 className={h2}>Clinic and patient information</h2>
      <p className={p}>
        Ophi’s service for clinics works inside the practice management system (PMS) the clinic already uses. When a patient calls, Ophi reads the schedule and the patient’s chart and writes the booking straight into the PMS. That is health information, and these rules govern it:
      </p>
      <ul className="mt-3 grid list-disc gap-2 pl-5">
        <li className={li}><strong className="font-medium text-ink">Your PMS holds the data.</strong> Your practice management system is the only place patient records are stored. Ophi reads from it and writes to it, has no database of patients, and keeps no copy of a chart, a schedule or an insurance record. What passes through Ophi during a call is described below.</li>
        <li className={li}><strong className="font-medium text-ink">No recordings or transcripts.</strong> Ophi does not record calls or save what was said. The words of a call exist only while the call is live and are discarded when it ends. Operating logs record that an action happened, not the names or birthdays involved.</li>
        <li className={li}><strong className="font-medium text-ink">The AI services keep nothing.</strong> Three services handle a live call: one turns the caller’s speech into text, one writes Ophi’s reply, and one speaks it. Each processes the conversation as it happens and retains none of it, and none of it is used to train a model. The language model runs on servers in Canada. The speech-to-text and voice services run in the United States, so a call’s audio and words pass through US servers for those moments, and nowhere do they stay.</li>
        <li className={li}><strong className="font-medium text-ink">Who can see it, and how it is protected.</strong> Pending items sit in the memory of Ophi’s call server on Amazon Web Services in Ohio. They are visible only to clinic staff who sign in to Ophi’s dashboard with a password, and to the Ophi personnel who can log in to that server, which takes a private key. Connections to the server, including the call audio, are encrypted in transit.</li>
        <li className={li}><strong className="font-medium text-ink">Callers are told, and can choose.</strong> Ophi opens every call by saying it is the office’s AI assistant. A caller can ask for a person at any time, and Ophi transfers the call to clinic staff straight away. Calls are not recorded, so there is no recording to consent to.</li>
        <li className={li}><strong className="font-medium text-ink">Who touches a live call.</strong> The call is carried by Telnyx, a telephone carrier, to Ophi’s call server, which runs on Amazon Web Services in the United States. Speech is turned into text by AssemblyAI or Deepgram and spoken back by ElevenLabs or Cartesia. All of them are used only to process the call as it happens. We tell the clinic before adding a provider.</li>
        <li className={li}><strong className="font-medium text-ink">The clinic is the custodian.</strong> Ophi acts as its agent and takes direction from the clinic. We do not sell patient information, use it for advertising, or combine one clinic’s with another’s.</li>
        <li className={li}><strong className="font-medium text-ink">Identity first.</strong> Ophi checks who it is speaking to, by name and date of birth, before it shares anything about a patient. If the details don’t match, it asks again and never reveals who is on file. After two misses it shares nothing about any file: it books the caller as a new patient for staff to reconcile, or takes a callback request for your team.</li>
        <li className={li}><strong className="font-medium text-ink">A narrow scope.</strong> For booking, Ophi reads a patient’s name and date of birth to confirm who is calling, their upcoming appointments, and the schedule’s open times. It writes one thing: an appointment, for an existing or a new patient. It cannot change a chart, a treatment plan or a bill.</li>
        <li className={li}><strong className="font-medium text-ink">Your clinic holds the key.</strong> Ophi reaches your PMS only through the connection your clinic sets up, so the clinic can end that access at any time.</li>
        <li className={li}><strong className="font-medium text-ink">Staff stay in the loop.</strong> Ophi proposes each booking and nothing is written to the PMS until staff approve it. A pending booking holds the patient’s name, date of birth and the visit asked for; a message left for staff holds a name, phone number and the message. Either one waits in Ophi’s memory until staff act on it. If nobody does, it expires after 24 hours, and once staff decide, Ophi drops it within the hour. Every action is logged so a clinic can see what was done and by whom.</li>
        <li className={li}><strong className="font-medium text-ink">No clinical advice.</strong> Ophi does not read treatment notes to answer symptom questions. When a caller describes pain or an emergency, it offers the earliest emergency visit or passes the call to your team.</li>
      </ul>
      <p className={p}>
        Because Ophi holds no patient records of its own, a breach of Ophi would not expose a store of patient data. If a security breach or suspected unauthorized access ever touches information Ophi holds, a live call, or the connection into a clinic’s PMS, we will tell the clinic within 72 hours of learning of it, and tell anyone else the law requires us to, including the Privacy Commissioner.
      </p>

      <h2 className={h2}>Standards we follow</h2>
      <p className={p}>
        What each law asks of us, and what we do about it.
      </p>
      <div className="mt-5 grid gap-3">
        {standards.map((s) => (
          <article key={s.name} className="rounded-[8px] border border-line bg-paper p-5">
            <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
              <h3 className="text-[16px] leading-[1.35]">{s.name}</h3>
              <span className="text-[12px] font-medium tracking-wide text-ink uppercase">{s.status}</span>
            </div>
            <p className="mt-2 text-[13px] leading-[1.7] text-muted">{s.detail}</p>
          </article>
        ))}
      </div>

      <h2 className={h2}>Changes and contact</h2>
      <p className={p}>
        When we change this page, we change the date at the top. If a change affects how we treat information you already gave us, we will email you first. Questions about privacy go to <a className={link} href={`mailto:${mail}`}>{mail}</a>.
      </p>

      <JsonLd data={{ "@context": "https://schema.org", "@type": "WebPage", name: "Ophi: privacy and compliance", url: "https://ophi.app/privacy", inLanguage: "en-CA" }} />
    </main>
  );
}
