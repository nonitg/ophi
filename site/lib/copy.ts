// Pre-launch public copy: purpose and problem, without product or payer-outcome claims.
export const copy = {
  name: "Ophi",
  title: "ophi.",
  description: "We’re building for dental teams who’d rather spend their time on people. Join Ophi for a first look at what’s taking shape.",
  contactEmail: "hello@ophi.app",
  source: {
    label: "Health Canada, via Oral Health Group · June 18, 2026",
    href: "https://www.oralhealthgroup.com/dental-governance-regulations/cdcp-update-less-than-half-of-dental-preauthorization-requests-approved-as-new-trends-emerge-1003996608/",
  },
  // Notes found by playing with the X-ray view.
  xray: {
    backwards: "Film’s in backwards. That pattern is its lead backing.",
    alara: "That’s five exposures. Dentists keep radiation as low as reasonably achievable.",
  },
  form: {
    email: "Your email",
    emailPlaceholder: "Your email address",
    pms: "Which software does your clinic use? (optional)",
    pmsPlaceholder: "At a clinic? Tell us your software (optional)",
    submit: "Join waitlist",
    submitting: "Joining…",
    consent: "By joining, you agree to occasional updates from Ophi. Unsubscribe anytime.",
    success: "You’re on the list.",
    successDetail: "We’ll write when there’s something to share.",
  },
} as const;
