// Hidden SEO guide pages under /guides. They are intentionally never linked from the visible site; crawlers reach
// them through sitemap.xml (see app/sitemap.ts). Content is factual and pre-launch honest: no invented statistics,
// dates, or pricing, and the only figure reused is the CDCP figure cited on the homepage (copy.source).

export type GuideSection = { heading: string; paragraphs: string[] };

export type Guide = {
  slug: string;
  title: string;
  // Meta description (~160 chars) plus the lead-in on the page.
  description: string;
  lede: string;
  keywords: string[];
  sections: GuideSection[];
  faq?: { q: string; a: string }[];
  related: string[];
};

export const guides: Guide[] = [
  {
    slug: "dental-preauthorization",
    title: "What is dental preauthorization?",
    description:
      "Dental preauthorization is a plan’s approval of a treatment before the clinic proceeds. Learn what it involves and why clinics prepare preauthorization requests.",
    lede: "Dental preauthorization is how a dental plan agrees to pay for a treatment before the work begins. This guide covers what it is, when a dental clinic needs one, and where it fits in the day-to-day.",
    keywords: ["dental preauthorization", "preauthorization", "treatment preauthorization", "preauthorization request"],
    sections: [
      {
        heading: "Dental preauthorization, briefly",
        paragraphs: [
          "Dental preauthorization is the review a dental plan does before it agrees to pay for a treatment. A clinic sends the plan the details of what it wants to do and why; the plan decides whether — and how much — it will cover before the work begins.",
          "It isn’t a bill or a guarantee of coverage. It’s an approval in advance: the clinic knows where it stands before committing to treatment, and the patient knows what the plan will contribute.",
        ],
      },
      {
        heading: "When does a dental clinic need preauthorization?",
        paragraphs: [
          "Plans usually ask for preauthorization on larger or less routine treatments — anything where the plan wants the clinical picture (records, x-rays, a written explanation) before it commits. Under Canada’s federal dental coverage through the CDCP, treatment preauthorization is required for some treatments before the plan pays.",
          "Every plan sets its own thresholds, so a dental clinic keeps its payer rules close at hand when deciding which treatments need a preauthorization request.",
        ],
      },
      {
        heading: "What goes into a preauthorization request",
        paragraphs: [
          "A complete request is assembled evidence: the treatment plan, supporting radiographs and notes, and a short clinical explanation of why the treatment is needed. Missing material is the most common reason a request stalls.",
          "Putting those pieces together is mostly paperwork time — exactly the part of the job Ophi is building tools to shrink.",
        ],
      },
      {
        heading: "Where preauthorization fits in a dental clinic’s day",
        paragraphs: [
          "Preauthorization lands on the clinic’s administrative team, between chair time and everything else that keeps the practice running. Each request means gathering records, drafting the explanation, submitting to the right place, and following up on the decision.",
          "For dental clinics, the difference between fast, complete requests and slow back-and-forth is preparation — and preparation is paperwork.",
        ],
      },
    ],
    faq: [
      { q: "Is preauthorization required for every dental treatment?", a: "No. Plans ask for it on treatments that meet their thresholds — typically larger or less routine work. The practice’s payer rules decide when one is needed." },
      { q: "Who prepares the preauthorization request?", a: "Usually the clinic’s administrative team, often working from the dentist’s notes and images, since the request is a clinical explanation of the planned treatment." },
      { q: "Does preauthorization mean the treatment is covered?", a: "Preauthorization approves the treatment in advance, but coverage still depends on the patient’s benefits and the plan’s terms." },
    ],
    related: ["dental-preauthorization-for-clinics", "cdcp-treatment-preauthorization", "ophi-for-dental-clinics"],
  },
  {
    slug: "dental-preauthorization-for-clinics",
    title: "Dental preauthorization for clinics: how the process works",
    description:
      "How dental clinics prepare and submit treatment preauthorization requests — the records, the clinical narrative, and the follow-up that gets them approved.",
    lede: "For a dental clinic, preauthorization is a familiar rhythm: identify the treatments that need approval, pull the records, write the request, submit, and follow up. Here’s how the process actually runs.",
    keywords: ["dental preauthorization for clinics", "dental clinics", "treatment preauthorization", "preauthorization request"],
    sections: [
      {
        heading: "The clinic’s side of preauthorization",
        paragraphs: [
          "Preauthorization exists so the plan can review a treatment before it happens. The clinic’s job is to hand the plan a clear picture: what treatment is planned, why it’s needed, and what the records show.",
          "For most clinics that means the same loop every time — identify the treatments that need approval, pull the records, write the request, submit it, and track the decision until it lands.",
        ],
      },
      {
        heading: "The treatment narrative",
        paragraphs: [
          "The narrative is the written why: the diagnosis, the planned treatment, and the clinical reasoning. It’s the part that reads like the practice — and the part that slows clinics down when it’s improvised from scratch each time.",
        ],
      },
      {
        heading: "Supporting records",
        paragraphs: [
          "X-rays, chart notes, and other records back the narrative. A complete file is easier to approve; an incomplete one gets returned for more information, and that’s where hold-ups usually happen.",
        ],
      },
      {
        heading: "Submitting and tracking",
        paragraphs: [
          "Submit to the right plan, note the reference, and track the outcome. Decisions come back as approvals, partial approvals, or requests for more information — each with its own follow-up.",
          "Tracking is where paperwork quietly multiplies. A clinic with a clear view of outstanding requests and their statuses saves itself the “where is this one?” calls.",
        ],
      },
      {
        heading: "Spending paperwork time on people instead",
        paragraphs: [
          "Every request that is prepared well the first time is a block of staff time returned to the clinic’s real work. Ophi is building tools that help dental teams prepare preauthorization requests with less of that time spent on paperwork.",
        ],
      },
    ],
    related: ["dental-preauthorization", "cdcp-treatment-preauthorization", "dental-preauthorization-wait-times"],
  },
  {
    slug: "cdcp-treatment-preauthorization",
    title: "CDCP treatment preauthorization: a guide for dental clinics",
    description:
      "How treatment preauthorization works under the Canadian Dental Care Plan (CDCP), how much of it clinics are handling, and what a complete request looks like.",
    lede: "The Canadian Dental Care Plan asks clinics to request preauthorization for some treatments before it will pay. This guide covers how that works and how much of it dental clinics are handling.",
    keywords: ["CDCP preauthorization", "treatment preauthorization", "Canadian Dental Care Plan", "dental preauthorization"],
    sections: [
      {
        heading: "What is the Canadian Dental Care Plan (CDCP)?",
        paragraphs: [
          "The Canadian Dental Care Plan (CDCP) is a federal dental benefits plan, administered by Health Canada, that helps eligible residents pay for dental care. For some treatments, the plan asks clinics to submit a treatment preauthorization request before it will pay.",
        ],
      },
      {
        heading: "When the CDCP requires preauthorization",
        paragraphs: [
          "Preauthorization under the CDCP follows the same shape as plan preauthorization anywhere: the clinic submits a request with the planned treatment and its supporting records, and the plan approves it in advance or asks for more.",
        ],
      },
      {
        heading: "What clinics are handling in practice",
        paragraphs: [
          "The volume is real. In the CDCP update of June 18, 2026, via Oral Health Group, less than half of dental preauthorization requests were approved — and clinics had submitted roughly 480,000 complete requests for treatment preauthorization in just three months (March 1 – May 31, 2026).",
          "That figure is cited and sourced on Ophi’s homepage. It matters to clinics because each of those requests was paperwork someone had to assemble.",
        ],
      },
      {
        heading: "Preparing a complete CDCP preauthorization request",
        paragraphs: [
          "A complete request gives the plan everything it needs once: the treatment plan, the clinical explanation, and the records behind it. Requests that are complete the first time move through review without the back-and-forth that stretches wait times.",
          "Ophi is starting with the work behind these requests — the preparation that turns a treatment into a submittable file. It’s early, and we’ll share more when it’s ready.",
        ],
      },
    ],
    faq: [
      { q: "Is CDCP preauthorization the same as a dental preauthorization?", a: "It’s the same idea — advance approval of a treatment — applied to the federal Canadian Dental Care Plan." },
      { q: "Where can I read the CDCP preauthorization figures Ophi cites?", a: "The Health Canada update, via Oral Health Group (June 18, 2026), is linked from Ophi’s homepage." },
    ],
    related: ["dental-preauthorization", "dental-preauthorization-for-clinics", "dental-preauthorization-wait-times"],
  },
  {
    slug: "dental-preauthorization-wait-times",
    title: "How long does dental preauthorization take?",
    description:
      "Why dental preauthorization decisions take time, what clinics control in that timeline, and how a complete request keeps wait times short.",
    lede: "No one can quote a universal dental preauthorization wait time — it depends on the plan, the treatment, and the completeness of the file. Here’s what actually moves the needle.",
    keywords: ["dental preauthorization wait times", "preauthorization", "dental clinics"],
    sections: [
      {
        heading: "Why preauthorization decisions take time",
        paragraphs: [
          "A dental preauthorization is a review: someone reads the treatment plan, checks the records against the request, and applies the plan’s rules before approving. That review takes time, and how long depends on the plan, the treatment, and how complete the file is.",
        ],
      },
      {
        heading: "What clinics control",
        paragraphs: [
          "Missing records are a leading reason requests stall. A request that arrives complete — treatment plan, narrative, images — moves through review without a round trip for more information.",
          "Preparation is the clinic’s lever on wait times. The same treatment can take days longer when the first submission is incomplete.",
        ],
      },
      {
        heading: "Keeping requests from getting stuck",
        paragraphs: [
          "Standardize what goes into a request: the same checklist, the same file order, the same clarity of narrative. Track outstanding requests so follow-ups happen before a payer has to ask.",
          "Ophi is building tools that cut the preparation side of that loop — the assembly and paperwork — so dental teams spend less time waiting on preauthorization queues.",
        ],
      },
    ],
    faq: [
      { q: "What makes a preauthorization request complete?", a: "The planned treatment, a clinical explanation, and the supporting records — x-rays and notes — submitted together the first time." },
      { q: "Who decides how long preauthorization takes?", a: "Each plan runs its own review. Clinics influence the fastest part to fix: submitting a complete request so no follow-up is needed." },
    ],
    related: ["dental-preauthorization-for-clinics", "cdcp-treatment-preauthorization", "dental-preauthorization"],
  },
  {
    slug: "preauthorization-vs-predetermination",
    title: "Preauthorization vs. predetermination: what dental clinics should know",
    description:
      "The difference between predetermination — an estimate of coverage — and preauthorization — advance approval — and when dental clinics use each.",
    lede: "Predetermination and preauthorization sound alike and often get swapped. They answer different questions, and sending the wrong one costs a clinic a round trip. Here’s how to tell them apart.",
    keywords: ["preauthorization vs predetermination", "predetermination", "dental preauthorization", "dental clinics"],
    sections: [
      {
        heading: "Two different questions",
        paragraphs: [
          "Predetermination and preauthorization sound alike but answer different questions: predetermination asks what a plan would pay; preauthorization asks whether the treatment may proceed before the plan pays.",
        ],
      },
      {
        heading: "Predetermination: the estimate",
        paragraphs: [
          "A predetermination gives the patient an idea of coverage in advance — what the plan would contribute and what the patient may owe. The clinic submits the treatment plan and gets a coverage estimate back before treatment starts.",
          "Some plans use specific words for this step, and some regulate when a clinic may charge a fee for preparing one, so local and payer rules still apply.",
        ],
      },
      {
        heading: "Preauthorization: the approval in advance",
        paragraphs: [
          "Preauthorization is the go-ahead for the treatment itself. The clinic sends the clinical picture — plan, narrative, records — and the plan approves it before work begins. Under the CDCP and other plans, treatment preauthorization is required for some treatments before the plan pays.",
        ],
      },
      {
        heading: "Why the distinction matters to clinics",
        paragraphs: [
          "Sending the wrong one costs time: an estimate where a decision was needed, or a request where the plan wanted a review first. Knowing which question the plan is asking keeps requests — and paperwork — moving.",
        ],
      },
    ],
    faq: [
      { q: "Is a predetermination required before preauthorization?", a: "Not always. Different plans handle the two differently; the clinic’s payer rules decide which step applies to a given treatment." },
      { q: "Do patients see the difference?", a: "They experience it as the plan’s coverage decision. For the clinic the practical difference is which file to prepare and which process to run." },
    ],
    related: ["dental-preauthorization", "dental-preauthorization-for-clinics", "cdcp-treatment-preauthorization"],
  },
  {
    slug: "ophi-for-dental-clinics",
    title: "Ophi for dental clinics: preauthorization with less paperwork",
    description:
      "Ophi builds tools that help dental teams prepare preauthorization requests — so clinics spend their time on people, not paperwork.",
    lede: "Ophi is building tools for dental teams who’d rather spend their time on people. This guide explains the problem Ophi starts with — the paperwork behind preauthorization requests.",
    keywords: ["Ophi", "Ophi dental", "dental preauthorization software", "dental clinics"],
    sections: [
      {
        heading: "The paperwork behind every preauthorization request",
        paragraphs: [
          "Before a plan pays for some treatments, a clinic has to submit a preauthorization request: the treatment plan, the supporting records, and a clinical explanation. Someone has to gather all of it — usually the clinic’s team, between everything else the practice runs on.",
          "The volume is considerable. In three months alone (March 1 – May 31, 2026), clinics submitted roughly 480,000 complete treatment preauthorization requests under the CDCP, per the Health Canada update cited on Ophi’s homepage.",
        ],
      },
      {
        heading: "What Ophi is building",
        paragraphs: [
          "Ophi is building tools that help dental teams prepare preauthorization requests, so less time goes to paperwork and more can go to patient care. We’re starting with the work behind those requests — the preparation itself.",
        ],
      },
      {
        heading: "Who Ophi is for",
        paragraphs: [
          "Dental clinics handling treatment paperwork and preauthorization requests. If your team assembles files, explains treatments, and tracks payer decisions, you’re who we’re building for.",
        ],
      },
      {
        heading: "Join the waitlist",
        paragraphs: [
          "We’re still building. Join the waitlist to hear when Ophi is ready, and tell us which clinic software you use — it helps us decide what to build next.",
        ],
      },
    ],
    related: ["dental-preauthorization-for-clinics", "dental-clinic-administration", "cdcp-treatment-preauthorization"],
  },
  {
    slug: "dental-clinic-administration",
    title: "Dental clinic administration: taming preauthorization paperwork",
    description:
      "Where preauthorization paperwork comes from in a dental clinic and how teams keep administration from eating chair time.",
    lede: "Dental clinics run on clinical care and the administration around it — including preauthorization requests. Here’s where that paperwork comes from and how teams keep it from eating chair time.",
    keywords: ["dental clinic administration", "dental clinics", "dental preauthorization", "dental office"],
    sections: [
      {
        heading: "The paperwork side of running a dental clinic",
        paragraphs: [
          "A dental clinic runs on clinical care and the administration around it: schedules, insurance, claims, and the records behind each. Preauthorization requests are the part of that paperwork that needs preparation before the plan will pay.",
        ],
      },
      {
        heading: "Where preauthorization requests come from",
        paragraphs: [
          "When a treatment meets a plan’s thresholds, the clinic prepares a request with the treatment plan, the clinical narrative, and supporting images and notes. Under the federal CDCP, clinics prepared on the order of 480,000 complete treatment preauthorization requests in three months — per the Health Canada update Ophi cites — which is why they’re a fixture of clinic administration.",
        ],
      },
      {
        heading: "Saving time on treatment preauthorization",
        paragraphs: [
          "The clinics that keep preauthorization under control treat it as a routine: a checklist of what every complete request needs, clear ownership, and a shared view of outstanding requests and their statuses.",
          "Standardizing the paperwork shrinks the administrative burden — and that’s the gap Ophi is building for. Tools that help dental teams prepare preauthorization requests, so fewer hours go to files and follow-ups.",
        ],
      },
    ],
    faq: [
      { q: "What is the most time-consuming part of preauthorization for clinics?", a: "Assembling the file — records, narrative, and submission — and the round trips when a request comes back incomplete." },
      { q: "Can clinics reduce preauthorization paperwork?", a: "Yes: with a consistent checklist, clear ownership, and tracking. Preparation done once beats rework repeated." },
    ],
    related: ["dental-preauthorization-for-clinics", "ophi-for-dental-clinics", "preauthorization-vs-predetermination"],
  },
];

export function findGuide(slug: string): Guide | undefined {
  return guides.find((g) => g.slug === slug);
}