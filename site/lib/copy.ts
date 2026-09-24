// Pre-launch public copy: purpose and problem, without product or payer-outcome claims.
export const copy = {
  name: "Ophi",
  // Metadata only — the visible wordmark is hardcoded in page.tsx, so the SERP/tab title carries the keywords
  // without changing the page the reader sees.
  title: "Ophi — Dental preauthorization for clinics",
  description:
    "Ophi builds tools that help dental clinics prepare treatment preauthorization requests, so less time goes to paperwork. Join the waitlist for a first look.",
  keywords: ["Ophi", "dental preauthorization", "preauthorization", "dental clinics", "treatment preauthorization", "CDCP", "dental clinic software"],
  contactEmail: "hello@ophi.app",
  // The homepage FAQ, surfaced to search engines as FAQPage structured data. Text must match page.tsx exactly.
  faq: [
    { q: "Who is Ophi for?", a: "Dental clinics handling treatment paperwork and preauthorization requests." },
    { q: "What are you building?", a: "Tools that help dental teams prepare preauthorization requests, so less time goes to paperwork." },
    { q: "When can I try it?", a: "We’re still building. Join the waitlist to hear when Ophi is ready." },
  ],
  source: {
    label: "Health Canada, via Oral Health Group · June 18, 2026",
    href: "https://www.oralhealthgroup.com/dental-governance-regulations/cdcp-update-less-than-half-of-dental-preauthorization-requests-approved-as-new-trends-emerge-1003996608/",
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
    label: "At a clinic? Take our survey",
  },
} as const;
