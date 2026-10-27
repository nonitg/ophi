// Pre-launch public copy: purpose and problem, without product or outcome claims.
export const copy = {
  name: "Ophi",
  // Metadata only — the visible wordmark is hardcoded in page.tsx, so the SERP/tab title carries the keywords
  // without changing the page the reader sees.
  title: "Ophi — AI voice agents for dental clinics",
  description:
    "Ophi builds AI voice agents that answer calls for dental clinics — booking, rescheduling, and making sure no patient goes unanswered. Join the waitlist for a first look.",
  keywords: ["Ophi", "dental voice agent", "AI phone answering", "dental clinics", "after-hours dental calls", "dental appointment booking", "dental clinic software"],
  contactEmail: "hello@ophi.app",
  // The homepage FAQ, surfaced to search engines as FAQPage structured data. Text must match page.tsx exactly.
  faq: [
    { q: "Who is Ophi for?", a: "Dental clinics that want every patient call answered, even after hours." },
    { q: "What are you building?", a: "An AI voice agent that answers calls, books and reschedules appointments, and sends your team an email so nothing falls through." },
    { q: "Does it work with my clinic software?", a: "Ophi plugs into your practice management software to read your schedule and book directly. We’re building integrations for the most common Canadian systems first." },
    { q: "When can I try it?", a: "We’re still building. Join the waitlist to hear when Ophi is ready." },
  ],
  source: {
    label: "Dental Economics · missed calls in dental practices",
    href: "https://www.dentaleconomics.com/",
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
    submit: "Join waitlist",
    submitting: "Joining…",
    consent: "By joining, you agree to occasional updates from Ophi. Unsubscribe anytime.",
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
