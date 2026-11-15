// Public copy. The page describes where Ophi is going (ophi-phone VISION.md), not only what ships today:
// no customers, prices, launch dates or outcome promises. Never say a treatment is covered, approved or eligible.
// Every idea is said once; each section's picture carries the rest.
export const copy = {
  name: "Ophi",
  // Metadata only: the visible wordmark is hardcoded in page.tsx, so the SERP/tab title carries the keywords
  // without changing the page the reader sees.
  title: "Ophi — One assistant for every dental patient",
  description:
    "Ophi is one assistant for every patient of a dental clinic. Patients call, text or tap, and Ophi knows where their care stands and what happens next, straight from the clinic’s own record system.",
  keywords: ["Ophi", "dental patient assistant", "dental AI", "dental clinics", "patient communication", "treatment follow-up", "dental clinic software", "AI phone answering"],
  contactEmail: "hello@ophi.app",
  nav: [
    { href: "#how", label: "How it works" },
    { href: "#story", label: "One patient" },
    { href: "#clinic", label: "For clinics" },
    { href: "#roadmap", label: "Roadmap" },
  ],
  cta: "Get early access",
  madeIn: "Built in Canada",

  hero: {
    title: "One assistant for every patient.",
    lede: "Ophi is an AI assistant for dental clinics. Patients call, text or tap, and it always knows where their care stands and what happens next.",
    seeHow: "See how it works",
    // The stage: three patients, three doors, each answered from their own care (lib/hero.ts, components/hero-stage.tsx).
    channel: { call: "Phone call", text: "Text message", page: "Patient page" },
    calling: "Calling…",
    onCall: "On a call with Ophi",
    compose: "Message",
    ophi: "Ophi",
    page: (name: string) => `${name}’s page`,
    noLogin: "No app, no login",
    record: (name: string) => `${name}’s care, from your records`,
  },

  // Why: the record holds the whole plan, the patient holds one date (components/gap.tsx).
  gap: {
    title: "Care takes many steps. Today, your patient sees one.",
    lede: "The whole plan lives in your record system. To learn the rest, patients phone the front desk, and many never get through.",
    patient: "What Alex knows today",
    // The one step Alex knows about: the appointment the front desk told them.
    known: "prep",
    ask: "To learn the rest, Alex has to call.",
    fixLabel: "With Ophi",
    // Each count of what the gap costs, and what Ophi does about it.
    stats: [
      {
        figure: "31 in 100", text: "calls to dental practices hang up before reaching anyone.", source: "Patient Prism, 2026", href: "https://www.patientprism.com/report/dental-patient-access-report/", of: 100, hit: 31,
        fix: "Every call answered, day or night, in your clinic’s words.",
      },
      {
        figure: "1 in 5", text: "adults have ever opened a patient portal.", source: "CareQuest Institute, 1,022 US adults", href: null, of: 5, hit: 1,
        fix: "Every patient gets their page in a text. No app, no login.",
      },
    ],
  },

  // How: one patient's care, changed through every door, always in one place (components/how-thread.tsx).
  // Says what Ophi is; never names or blames anyone else.
  how: {
    title: "Call, text or tap. It all lands in one place.",
    lede: "However a patient reaches you, Ophi adds it to one picture of their care, kept in step with the record system you already run.",
    care: "Alex’s care",
    plan: "Crown, lower left molar",
    doors: { call: "Call", text: "Text", page: "Their page", records: "Records" },
    alex: "Alex",
    ophi: "Ophi",
    calling: "Alex is calling",
    text: "Text message",
    page: "Alex’s page · no app, no login",
    planReady: "Dr. Shah’s plan for your crown is ready.",
    book: (when: string) => `Book ${when}`,
    booked: (when: string) => `Booked ${when}`,
    records: "From your records",
    insurer: "The insurer replied.",
    inStep: "In step with your record system",
    saved: "Saved to your record system",
    alt: "Alex’s crown as one care timeline. Alex books the crown prep on their own page, the insurer’s reply comes in from the clinic’s records, the fitting is booked by text and then moved in a phone call, and every change lands in the same timeline.",
  },

  story: {
    title: "Follow one crown, start to finish.",
    real: "Hear the real call",
    realNote: "Real recording of Ophi with a test caller",
    stop: "Stop",
    pause: "Pause the story",
    play: "Play the story",
    replay: "Watch again",
    note: "An illustration with a fictional patient and clinic. The first call is a real recording.",
    page: "Alex’s care",
    states: { done: "Done", booked: "Booked", planned: "Planned", waiting: "Waiting on" },
  },

  team: {
    title: "Your team sees every patient. You decide what needs a yes.",
    lede: "Updates go out when your records change, with no one typing. Every action leaves a trail your team can check.",
    clinic: "Birchwood Family Dental",
    when: "Wednesday, 12:20 pm",
    approve: "Approve",
    approving: "Approving…",
    // In the order the product runs them: the patient is told last, once the change is checked.
    approved: ["Checked the time is still free", "Written to your schedule", "Checked it saved correctly", "Jordan texted"],
    rule: "Your rule: surgery changes wait for a yes",
    tallies: [
      { id: "calls", label: "calls answered" },
      { id: "updates", label: "updates sent" },
      { id: "booked", label: "next steps booked" },
    ],
    columns: ["Patient", "Care", "Next", "What Ophi did"],
    idle: "One request needs your yes.",
    done: "You approved. Jordan got a text.",
    note: "An illustration of one clinic’s day. Fictional patients.",
  },

  // Each stage adds work Ophi can take on; the stages before it stay (components/roadmap.tsx).
  roadmap: {
    title: "Starts with the phone. Grows into the whole front desk.",
    now: "Starting here",
    stages: [
      { name: "Answer", work: "Every call picked up: booking, changes, new patients, questions." },
      { name: "Inform", work: "Confirmations, reminders and each patient’s own page." },
      { name: "Guide", work: "Multi-visit plans, lab orders and recalls, carried to the end." },
      { name: "Complete", work: "Forms, estimates, insurance and payment, closed out." },
      { name: "Run", work: "The routine front desk, at every location." },
    ],
    stays: "What stays with your team: welcoming patients, judgment calls, and the approvals you choose to keep.",
  },

  signup: {
    title: "Be one of the first clinics.",
    note: "We’re bringing clinics on a few at a time. Leave your email and we’ll write when there’s room for yours.",
  },

  faqTitle: "Questions",
  // The homepage FAQ, surfaced to search engines as FAQPage structured data. Text must match page.tsx exactly.
  faq: [
    { q: "Who is Ophi for?", a: "Dental clinics that want every patient to know where their care stands, without adding work for the front desk." },
    { q: "Does it work with my clinic software?", a: "Ophi sits on the record system your clinic already runs. ABELDent is connected first, and we build the connection for each clinic we bring on." },
    { q: "Where does patient data live?", a: "In Canada. Ophi is built for Canadian health privacy law, such as PHIPA in Ontario. It checks who it’s talking to before sharing anything, and writes to your records only what your rules allow." },
    { q: "Will Ophi give clinical advice?", a: "No. Ophi only says what your records say. Questions about care go to your team." },
    { q: "When can I try it?", a: "We’re starting with a small group of pilot clinics on ABELDent. Other record systems follow as clinics join." },
  ],
  contact: "Anything else? Write to us.",

  // Notes found by playing with the X-ray view (components/tooth-scene.tsx, not on the page right now).
  xray: {
    backwards: "Film’s in backwards. That’s its lead backing.",
    alara: "Five exposures. Dentists keep doses as low as reasonably achievable.",
  },
  form: {
    email: "Your email",
    emailPlaceholder: "Your work email",
    pms: "Which software does your clinic use? (optional)",
    pmsPlaceholder: "At a clinic? Tell us your software (optional)",
    pmsPlaceholderShort: "Clinic software (optional)",
    submit: "Get early access",
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
