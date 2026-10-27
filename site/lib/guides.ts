// Hidden SEO guide pages under /guides. They are intentionally never linked from the visible site; crawlers reach
// them through sitemap.xml (see app/sitemap.ts). Content is factual and pre-launch honest: no invented statistics,
// dates, or pricing, and every figure used is an industry-cited estimate clearly labelled as such.

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
    slug: "dental-voice-agent",
    title: "What is a dental voice agent?",
    description:
      "A dental voice agent is an AI that answers your clinic's phone — booking appointments, handling reschedules, and making sure no patient call goes unanswered.",
    lede: "A dental voice agent is AI that picks up the phone for your clinic. It talks to patients, books and reschedules appointments, and sends your team an email when something needs attention. This guide covers what it is and how it works.",
    keywords: ["dental voice agent", "AI phone answering dental", "dental clinic voice AI", "automated dental receptionist"],
    sections: [
      {
        heading: "A voice agent, briefly",
        paragraphs: [
          "A dental voice agent is an AI-powered system that answers phone calls on behalf of a dental clinic. It listens to what the patient needs, checks the clinic's schedule through the practice management software, and books or reschedules appointments in real time.",
          "It isn't a phone tree or an answering machine. It's a conversation — the patient speaks naturally, the agent understands, and the appointment lands on the schedule without a human needing to pick up.",
        ],
      },
      {
        heading: "How it works with your clinic",
        paragraphs: [
          "The voice agent connects to your practice management software, so it sees real availability and books directly into your schedule. When a patient calls and your team is busy or the office is closed, the agent picks up, handles the request, and sends an email to your team with the details.",
          "For calls that need a human — an emergency, an insurance question, something outside booking — the agent routes them appropriately or takes a message so your team can follow up.",
        ],
      },
      {
        heading: "Why clinics are looking at voice agents now",
        paragraphs: [
          "Front desk staff juggle walk-ins, check-ins, and a ringing phone at the same time. Industry data suggests dental clinics miss anywhere from 20–35% of incoming calls, and a patient who can't get through often calls the next clinic on their list.",
          "A voice agent doesn't replace the front desk — it catches the calls they can't get to. The team stays focused on the patients in front of them while every caller still gets an answer.",
        ],
      },
    ],
    faq: [
      { q: "Does a dental voice agent replace the front desk?", a: "No. It handles overflow and after-hours calls so the front desk team can focus on patients in the office." },
      { q: "Can the agent handle more than just booking?", a: "It can book, reschedule, and take messages. Calls that need a human are flagged for your team to follow up." },
      { q: "Does the patient know they're talking to AI?", a: "The agent identifies itself clearly. Patients interact with it the same way they'd speak to any receptionist." },
    ],
    related: ["missed-calls-dental-clinics", "after-hours-dental-calls", "ophi-for-dental-clinics"],
  },
  {
    slug: "missed-calls-dental-clinics",
    title: "How missed calls cost dental clinics patients",
    description:
      "Dental clinics miss 20–35% of incoming calls. Each unanswered call risks losing a patient worth thousands in lifetime value. Here's what it actually costs.",
    lede: "When a dental clinic misses a call, the patient doesn't leave a voicemail — they call someone else. This guide looks at what missed calls actually cost a practice and why answering every call matters more than most clinics think.",
    keywords: ["missed calls dental clinic", "dental clinic phone calls", "patient loss dental", "dental practice revenue"],
    sections: [
      {
        heading: "How many calls dental clinics miss",
        paragraphs: [
          "Industry estimates put the missed call rate for dental practices between 20% and 35%. The calls pile up during the busiest times — when the front desk is checking in patients, handling insurance, or assisting chairside — and after hours, when nobody is there at all.",
          "Most patients won't leave a voicemail. Studies on consumer phone behaviour consistently show that the majority of callers who reach voicemail hang up without leaving a message.",
        ],
      },
      {
        heading: "The cost of one missed call",
        paragraphs: [
          "A single dental patient is worth an estimated $12,000 to $15,000 or more over their lifetime — routine cleanings, exams, and occasional procedures add up over years of visits. One unanswered call from a new patient isn't a missed appointment; it's the entire relationship that never starts.",
          "Even for existing patients, a missed call that delays rebooking can mean a longer gap between visits, more cancellations, and eventually a patient who drifts away.",
        ],
      },
      {
        heading: "When calls get missed",
        paragraphs: [
          "Lunch hours, Monday mornings, and the period right after opening are peak missed-call times for most clinics. After-hours calls are missed entirely unless the clinic has coverage — and many don't.",
          "The pattern is predictable: call volume spikes when staff are busiest, and the calls that don't get answered are the ones that arrived at the worst moment.",
        ],
      },
      {
        heading: "What clinics can do about it",
        paragraphs: [
          "Hiring more staff is one option, but it's expensive and hard to scale for after-hours coverage. Call-back systems help, but they depend on patients picking up later. An AI voice agent answers every call in real time, books the appointment, and sends your team a summary — no hold time, no voicemail, no lost patient.",
        ],
      },
    ],
    faq: [
      { q: "What percentage of dental clinic calls go unanswered?", a: "Industry estimates range from 20% to 35%, depending on clinic size, staffing, and whether the office offers after-hours phone coverage." },
      { q: "How much is a missed call worth?", a: "If the caller is a new patient, a single missed call can represent $12,000–$15,000+ in lifetime value — cleanings, exams, and treatments over years." },
      { q: "Do patients leave voicemails?", a: "Most don't. Consumer studies consistently show that the majority of callers who reach voicemail will hang up rather than leave a message." },
    ],
    related: ["dental-voice-agent", "after-hours-dental-calls", "dental-patient-communication"],
  },
  {
    slug: "after-hours-dental-calls",
    title: "After-hours call handling for dental clinics",
    description:
      "Patients call dental clinics outside business hours more than most practices realize. Here's how after-hours calls affect patient retention and what to do about it.",
    lede: "Your clinic closes at 5, but your patients don't stop needing to book appointments at 5. After-hours calls are a real share of your call volume, and most clinics have no way to handle them. This guide covers the problem and the options.",
    keywords: ["after-hours dental calls", "dental clinic phone coverage", "dental office closed calls", "dental appointment after hours"],
    sections: [
      {
        heading: "When patients actually call",
        paragraphs: [
          "A significant portion of calls to dental clinics happen outside office hours — evenings, weekends, and lunch breaks when patients are free to make personal calls. These are often patients trying to book or reschedule, not emergencies.",
          "For a clinic that closes at 5 PM, calls between 5 PM and 9 AM the next day go straight to voicemail. Most of those callers won't leave a message.",
        ],
      },
      {
        heading: "What happens when no one answers",
        paragraphs: [
          "A patient who calls after hours and gets voicemail has three choices: leave a message, call back tomorrow, or call another clinic. The convenience option — calling another clinic — is the one practices can least afford.",
          "The patient isn't upset. They're not dissatisfied with your care. They just needed a time slot and someone else answered the phone.",
        ],
      },
      {
        heading: "Options for after-hours coverage",
        paragraphs: [
          "Answering services staffed by humans are available but costly, and the operators typically take a message rather than booking directly. The clinic still has to call the patient back and complete the booking during business hours.",
          "An AI voice agent handles the call in full: it checks real availability in your practice management software, books the appointment, and emails your team. The patient hangs up with a confirmed time. No call-back needed, no message to chase.",
        ],
      },
      {
        heading: "The compounding value of after-hours coverage",
        paragraphs: [
          "Every after-hours call that converts to a booked appointment is a patient you kept. Over months and years, the difference between answering those calls and losing them compounds — more chairs filled, fewer gaps in the schedule, and a patient base that grows instead of quietly leaking.",
        ],
      },
    ],
    faq: [
      { q: "How many calls come in after hours?", a: "It varies by clinic, but practices commonly report that a meaningful share of their total call volume — especially booking and rescheduling — arrives outside office hours." },
      { q: "Can an AI voice agent handle emergencies?", a: "An agent can identify emergency calls and direct the patient to the appropriate emergency line or on-call provider, rather than trying to handle them itself." },
    ],
    related: ["missed-calls-dental-clinics", "dental-voice-agent", "ai-appointment-booking-dental"],
  },
  {
    slug: "ai-appointment-booking-dental",
    title: "AI appointment booking for dental clinics",
    description:
      "How AI appointment booking works for dental clinics — from reading the schedule to confirming the visit, without the front desk picking up the phone.",
    lede: "AI appointment booking means a patient calls your clinic, speaks to an AI agent, and hangs up with a confirmed appointment — no hold time, no call-back, no manual entry. Here's how it works and what it means for a dental practice.",
    keywords: ["AI appointment booking dental", "dental scheduling AI", "automated dental booking", "dental clinic AI"],
    sections: [
      {
        heading: "How AI books a dental appointment",
        paragraphs: [
          "The patient calls and tells the AI voice agent what they need — a cleaning, a check-up, a reschedule. The agent checks the clinic's live schedule through the practice management software, finds a time that works, and books it on the spot.",
          "The patient gets a confirmed appointment. The clinic gets an email with the details. No one had to transfer, hold, or call back.",
        ],
      },
      {
        heading: "Reading the real schedule",
        paragraphs: [
          "The key to AI booking is the integration with your practice management software. The agent isn't guessing at availability — it reads the same schedule your front desk sees, respects provider preferences and appointment types, and writes the booking back into the system.",
          "That means no double-bookings, no phantom slots, and no manual reconciliation afterward.",
        ],
      },
      {
        heading: "Rescheduling and changes",
        paragraphs: [
          "Rescheduling is where clinics lose the most time on the phone — the patient needs a new time, the team checks availability, and the back-and-forth begins. An AI agent handles this in a single call: it finds the existing booking, checks what's open, and moves it.",
          "The fewer calls it takes to reschedule, the fewer patients give up and cancel entirely.",
        ],
      },
      {
        heading: "What the front desk gets back",
        paragraphs: [
          "Every call the AI handles is a call the front desk doesn't have to. The team gets an email summary of what was booked or changed, and they can review at their pace instead of being interrupted mid-task.",
          "The front desk doesn't disappear — they focus on the patients standing in front of them, while the phone takes care of itself.",
        ],
      },
    ],
    faq: [
      { q: "Does AI booking work with any clinic software?", a: "It depends on the integration. Ophi is building for the most common Canadian practice management systems first." },
      { q: "Can the AI handle complex scheduling?", a: "It handles standard bookings and reschedules. For cases that need clinical judgment — like treatment sequencing — it flags the call for your team." },
      { q: "What if the patient wants to speak to a person?", a: "The agent can take a message or route the call, so the patient always has a path to a human when they need one." },
    ],
    related: ["dental-voice-agent", "dental-clinic-phone-systems", "ophi-for-dental-clinics"],
  },
  {
    slug: "dental-clinic-phone-systems",
    title: "Phone systems for dental clinics: from hold music to AI",
    description:
      "How dental clinic phone systems have evolved — from basic landlines to VoIP to AI voice agents — and what modern clinics should look for.",
    lede: "The phone is still how most patients reach a dental clinic. But the systems behind it have changed — and clinics that haven't kept up are losing calls they don't know about. Here's the landscape.",
    keywords: ["dental clinic phone system", "dental office phone", "VoIP dental clinic", "dental phone answering"],
    sections: [
      {
        heading: "The phone is still the front door",
        paragraphs: [
          "Online booking is growing, but the phone remains the primary way patients contact dental clinics — especially older patients, new patients who have questions, and anyone who needs to reschedule or ask about insurance. A clinic's phone system is its most important patient-facing tool after the chair itself.",
        ],
      },
      {
        heading: "Where traditional systems fall short",
        paragraphs: [
          "A standard phone system — landline or VoIP — rings at the front desk. If the team is busy, it goes to voicemail. If it's after hours, it goes to voicemail. If two patients call at once, one goes to voicemail. The system works when someone is available to answer; when they're not, the call is effectively lost.",
          "Call-back features and hold queues help, but they still depend on a human completing the loop. The patient is waiting, and every minute of wait time increases the chance they hang up.",
        ],
      },
      {
        heading: "Answering services vs. AI voice agents",
        paragraphs: [
          "Human answering services give after-hours coverage, but operators typically take a message — they can't see your schedule or book an appointment. The clinic still has to call the patient back during business hours, and that's another task on the front desk's list.",
          "An AI voice agent closes the loop in one call. It reads your live schedule, books the appointment, and sends your team a summary. The patient gets an answer; the clinic gets a booking. No call-back, no message relay.",
        ],
      },
      {
        heading: "What to look for in a modern system",
        paragraphs: [
          "Integration with your practice management software is the baseline — if the system can't read and write to your schedule, it's just a fancier voicemail. Beyond that: real-time availability, the ability to handle reschedules, email notifications for your team, and a natural conversation that patients don't dread.",
        ],
      },
    ],
    faq: [
      { q: "Should a dental clinic replace its phone system with AI?", a: "Not necessarily. An AI voice agent works alongside your existing system — it handles overflow and after-hours calls without replacing what you already have." },
      { q: "Is AI phone answering expensive?", a: "Generally less than hiring additional front desk staff or a full-time answering service, with better coverage across all hours." },
    ],
    related: ["dental-voice-agent", "after-hours-dental-calls", "ai-appointment-booking-dental"],
  },
  {
    slug: "ophi-for-dental-clinics",
    title: "Ophi for dental clinics: every call answered",
    description:
      "Ophi builds an AI voice agent for dental clinics — answering calls, booking appointments, and making sure no patient goes unanswered, day or night.",
    lede: "Ophi is building an AI voice agent for dental clinics. It answers patient calls, books and reschedules appointments through your clinic software, and emails your team so nothing falls through. Here's what we're building and why.",
    keywords: ["Ophi", "Ophi dental", "dental voice agent", "dental clinic AI", "AI dental receptionist"],
    sections: [
      {
        heading: "The problem: calls your team can't get to",
        paragraphs: [
          "Dental clinics miss a significant share of incoming calls — during busy hours when the front desk is occupied, and after hours when the office is closed. Each missed call is a patient who might book somewhere else, and a lifetime of visits that goes with them.",
          "Hiring more staff helps during the day but doesn't solve after-hours coverage. Voicemail doesn't book appointments. Answering services take messages but can't access your schedule.",
        ],
      },
      {
        heading: "What Ophi does",
        paragraphs: [
          "Ophi is an AI voice agent that answers calls for your clinic. It has a natural conversation with the patient, checks your live schedule through your practice management software, and books or reschedules the appointment on the spot. Then it emails your team with the details.",
          "It works during office hours when your team is tied up, and after hours when nobody's there. Every call gets answered. Every booking lands on the schedule.",
        ],
      },
      {
        heading: "Built for Canadian dental clinics",
        paragraphs: [
          "We're building integrations for the practice management systems Canadian clinics actually use — ABELDent, ClearDent, Dentrix, Tracker, and more. Your schedule, your software, your workflow.",
        ],
      },
      {
        heading: "Join the waitlist",
        paragraphs: [
          "We're still building. Join the waitlist to hear when Ophi is ready, and tell us which clinic software you use — it helps us decide which integrations to build first.",
        ],
      },
    ],
    related: ["dental-voice-agent", "missed-calls-dental-clinics", "dental-patient-communication"],
  },
  {
    slug: "dental-patient-communication",
    title: "Patient communication for dental clinics: phone, email, and AI",
    description:
      "How dental clinics communicate with patients — from phone calls to email notifications — and where AI voice agents fit into a modern practice.",
    lede: "Patient communication is the connective tissue of a dental practice. Most of it still happens by phone, and clinics that can't keep up with call volume lose patients quietly. Here's how the pieces fit together.",
    keywords: ["dental patient communication", "dental clinic phone", "patient retention dental", "dental practice management"],
    sections: [
      {
        heading: "The phone is still the backbone",
        paragraphs: [
          "Despite the growth of online portals and text reminders, the phone call remains the primary channel for dental patient communication — especially for booking, rescheduling, and anything that involves a question. Patients pick up the phone when they need something handled now.",
          "That makes the phone both the clinic's biggest asset and its biggest vulnerability. When calls get answered, patients stay. When they don't, patients drift.",
        ],
      },
      {
        heading: "Email as the notification layer",
        paragraphs: [
          "Email works best as a follow-up and notification channel — appointment confirmations, reminders, and summaries of what was discussed or booked. It doesn't replace the phone for real-time requests, but it gives both the patient and the clinic a written record.",
          "When an AI voice agent books an appointment, the email to the clinic team closes the loop: the booking is confirmed, the details are documented, and no one has to remember what was said on a call.",
        ],
      },
      {
        heading: "Where AI fits in",
        paragraphs: [
          "An AI voice agent isn't a new channel — it's a better answer on the channel patients already prefer. The patient calls, gets a real conversation, and leaves with a booked appointment. The clinic gets an email. The front desk stays focused on in-person care.",
          "The result is a practice that communicates reliably across all hours, without adding headcount or asking patients to change how they reach out.",
        ],
      },
      {
        heading: "Retention starts with answering the phone",
        paragraphs: [
          "Patient retention in dental is driven by convenience and consistency. A patient who can always reach the clinic — who never hits voicemail, never waits on hold, never has to call back — is a patient who stays. The lifetime value of that consistency, compounded across hundreds of patients, is the difference between a practice that grows and one that churns.",
        ],
      },
    ],
    faq: [
      { q: "Is phone still the most important channel for dental clinics?", a: "For booking and rescheduling, yes. Text and online portals are growing but the phone is still how most patients make and change appointments." },
      { q: "How does AI voice answering affect patient satisfaction?", a: "Patients who get an immediate answer and a confirmed appointment tend to be more satisfied than those who reach voicemail or wait on hold." },
    ],
    related: ["missed-calls-dental-clinics", "dental-voice-agent", "ophi-for-dental-clinics"],
  },
];

export function findGuide(slug: string): Guide | undefined {
  return guides.find((g) => g.slug === slug);
}
