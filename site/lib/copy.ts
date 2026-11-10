// Public copy. Every claim here is something the phone agent does today (ophi-phone: agent/prompt.py, agent/tools.py,
// office.py); no customers, prices, launch dates or outcome promises. Never say a treatment is covered, approved or eligible.
export const copy = {
  name: "Ophi",
  // Metadata only — the visible wordmark is hardcoded in page.tsx, so the SERP/tab title carries the keywords
  // without changing the page the reader sees.
  title: "Ophi — AI voice agents for dental clinics",
  description:
    "Ophi is an AI voice agent that answers calls for dental clinics, day or night. It takes bookings, changes and cancellations for your team to approve, slows down when asked, and hands over the moment a caller wants a person. Listen to recorded calls.",
  keywords: ["Ophi", "dental voice agent", "AI phone answering", "dental clinics", "after-hours dental calls", "dental appointment booking", "dental clinic software"],
  contactEmail: "hello@ophi.app",
  nav: [
    { href: "#listen", label: "Listen" },
    { href: "#judgment", label: "Judgment" },
    { href: "#front-desk", label: "Your front desk" },
    { href: "#questions", label: "Questions" },
  ],
  cta: "Get early access",
  standfirst: "Ophi is an AI voice agent for dental clinics. It answers every call, day or night, takes the booking, and knows when to hand over to your team.",
  status: "Starting with a small group of pilot clinics in Canada.",
  listen: {
    action: "Hear a call",
    // {date} is the day the calls were placed (lib/calls.ts recordedOn).
    note: "Recorded on Ophi’s phone line, {date}. The callers are test voices reading a script and the patients are fictional; Ophi’s side is unscripted. Nothing is cut, except that the two transfers end at the hand-off, where a real call rings through to your team.",
    summary: "Left for your team",
    teamNote: "Its note to your team:",
    // Titles and one-liners are ours; every word in the transcripts is the recording's (lib/calls.ts).
    calls: {
      "book-cleaning": { title: "Booking a cleaning", blurb: "Checks identity, offers real openings.", caller: "Alex" },
      "slow-down": { title: "“Could you slow down?”", blurb: "Asked once, Ophi slows and says it again.", caller: "Margaret" },
      "ask-for-person": { title: "“Can I talk to someone?”", blurb: "No menu. Straight to your team.", caller: "Caller" },
      emergency: { title: "Swelling, and hard to swallow", blurb: "Not a booking. Ophi says so at once.", caller: "Caller" },
      "new-patient": { title: "A brand-new patient", blurb: "Name, birthday and insurance, taken once.", caller: "Nadia" },
      question: { title: "“Do you take the CDCP?”", blurb: "Your clinic’s own answer. No promises.", caller: "Caller" },
      frustrated: { title: "“That’s not what I said.”", blurb: "Ophi doesn’t argue. It brings in your team.", caller: "Caller" },
    },
  },
  // What the agent does when a call leaves the script. `hear` points at the recorded moment that proves it:
  // the first thing Ophi says after that tool runs, or the start of the call.
  judgment: [
    { title: "Slows down when asked.", body: "Say “could you slow down?” once, or just ask it to repeat itself. Ophi speaks slower and waits longer before it replies.", hear: { slug: "slow-down", tool: "set_pace" } },
    { title: "Hands over the moment you ask.", body: "Ask for a person and you get one. No menu and no “let me try first”. Your team gets a note saying why. If nobody can pick up, the caller is told they’ll be called back, and the note is already waiting.", hear: { slug: "ask-for-person", tool: "transfer_to_staff" } },
    { title: "Notices when a call is going badly.", body: "If it mishears twice, or the caller keeps repeating themselves or sounds fed up, Ophi stops trying and brings in your team.", hear: { slug: "frustrated", tool: "transfer_to_staff" } },
    { title: "Knows an emergency when it hears one.", body: "Swelling that affects breathing or swallowing is not a booking. Ophi says to call 911 or go to emergency, right away. A broken tooth gets your earliest emergency visit.", hear: { slug: "emergency" } },
    { title: "Lets people finish.", body: "Birthdays and phone numbers come with pauses. Ophi waits them out, and stops talking the moment a caller cuts in.", hear: null },
  ],
  frontDesk: {
    lede: "Nothing changes in your schedule on Ophi’s say-so. Every request from a call waits for your team.",
    steps: [
      { title: "On the call", body: "Ophi offers real openings and tells the caller the time is requested. It never says booked until it is." },
      { title: "At your desk", body: "The request is waiting with who called, what they want and the exact change. One click approves it." },
      { title: "In your software", body: "Ophi writes the appointment into your practice software, then looks it up again to check it saved correctly." },
      { title: "To the patient", body: "Only then does the confirmation text go out." },
    ],
    card: {
      label: "Waiting at the front desk",
      from: "From the first call above",
      approve: "Approve booking",
      working: "Approving…",
      done: ["Written to the schedule", "Checked that it saved correctly", "Confirmation text sent"],
      reset: "Show it again",
      note: "A demonstration with the request from the recorded call. Nothing is sent.",
      // Fictional demo clinic (ophi-phone playbooks/demo-clinic.yaml); wording follows office.py's confirmation text.
      clinic: "Birchwood Family Dental",
      phone: "416-555-0100",
    },
    software: {
      title: "Inside the software you already run.",
      body: "Ophi reads your real schedule from your practice software and, once your team approves, writes the appointment into it. ABELDent comes first, starting with our pilot clinics, and other Canadian systems follow. Tell us what your clinic runs when you sign up; it decides what we build next.",
    },
  },
  limits: [
    { title: "Give clinical advice.", body: "It offers a visit, or a call back from your dental team." },
    { title: "Promise coverage.", body: "It never says a treatment is covered, approved or eligible. Your team confirms at the visit." },
    { title: "Discuss a patient with a stranger.", body: "Name and date of birth are checked against the file first. If they don’t match, it gives nothing away." },
    { title: "Guess.", body: "Every time, price and policy it says comes from your schedule or your clinic’s own rules. If it doesn’t know, it takes a message." },
  ],
  signup: {
    intro: "In an analysis of 11.5 million calls to dental practices, 31 in 100 callers hung up before reaching anyone. Ophi answers every one.",
    title: "Get early access.",
    note: "We’re bringing clinics on a few at a time. Leave your email and we’ll write when there’s room for yours.",
  },
  // The homepage FAQ, surfaced to search engines as FAQPage structured data. Text must match page.tsx exactly.
  faq: [
    { q: "Who is Ophi for?", a: "Dental clinics that want every patient call answered, including the ones that come in after hours or while the front desk is busy." },
    { q: "What can Ophi do on a call?", a: "Take bookings, changes and cancellations, register new patients, answer questions from your clinic’s own rules, take messages, and transfer to your team. Each change waits for your team’s yes." },
    { q: "Does it change my schedule on its own?", a: "No. Every change waits for one click from your team. Once approved, Ophi writes it into your practice software, checks it saved correctly, and then confirms with the patient." },
    { q: "Does it work with my clinic software?", a: "Ophi reads your schedule from your practice management software and writes approved appointments into it. ABELDent comes first, starting with our pilot clinics, and we’re building for the most common Canadian systems next." },
    { q: "When can I try it?", a: "We’re starting with a small group of pilot clinics. Leave your email and we’ll write when there’s room for yours." },
  ],
  // The "Why Ophi?" figure: a call-analytics vendor's own customers, so the basis is stated with it.
  // Checked against the report page 2026-11-10 (figure, call count, locations).
  why: {
    figure: "31 in 100",
    claim: "patient calls ended with the caller hanging up before reaching anyone.",
    basis: "11.5 million calls to 8,280 dental practices in 2025",
  },
  source: {
    label: "Patient Prism · The Dental Patient Access Report, 2026",
    href: "https://www.patientprism.com/report/dental-patient-access-report/",
  },
  // Notes found by playing with the X-ray view.
  xray: {
    backwards: "Film’s in backwards. That’s its lead backing.",
    alara: "Five exposures. Dentists keep doses as low as reasonably achievable.",
  },
  form: {
    email: "Your email",
    emailPlaceholder: "Your email address",
    pms: "Which software does your clinic use? (optional)",
    pmsPlaceholder: "At a clinic? Tell us your software (optional)",
    pmsPlaceholderShort: "Your clinic’s software (optional)",
    submit: "Request access",
    submitting: "Sending…",
    consent: "By asking for access, you agree to occasional updates from Ophi. Unsubscribe anytime.",
    success: "You’re on the list.",
    // True for first and repeat signups alike, so the page never reveals who is already on the list.
    successDetail: "We’ll write to you at",
  },
  // Clinic workflow survey, offered after signup and in the welcome note.
  survey: {
    href: "https://www.jotform.com/262616967929072",
    label: "At a clinic? Tell us about your phone workflow",
  },
} as const;
