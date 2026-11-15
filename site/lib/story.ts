// One patient's crown, told as the page's centrepiece (components/crown-story.tsx): each step is a moment in the
// treatment, and each beat inside it is one thing happening on a door, in Ophi's memory or in the clinic's records.
// Alex, Birchwood Family Dental and everything after the first call are fictional. The first call's words are a real
// recording (public/calls/book-cleaning.mp3): never edit them.

export type CareState = "waiting" | "booked" | "planned" | "done";
export type Door = "call" | "text" | "page";
export type Line = { who: "alex" | "ophi"; text: string };
export type CareChange = { id: CareId; state: CareState; note: string };
export type RecordRow = { kind: string; text: string };

// Alex's care timeline, in the order treatment runs.
// `short` is the label where space is tight (the timeline on a phone).
export const CARE = [
  { id: "cleaning", label: "Cleaning and checkup", short: "Cleaning" },
  { id: "prep", label: "Crown prep", short: "Crown prep" },
  { id: "estimate", label: "Insurance estimate", short: "Estimate" },
  { id: "lab", label: "Crown made at the lab", short: "Lab" },
  { id: "fitting", label: "Crown fitting", short: "Fitting" },
  { id: "balance", label: "Balance", short: "Balance" },
  { id: "recall", label: "Six-month cleaning", short: "June cleaning" },
] as const;
export type CareId = (typeof CARE)[number]["id"];

type Beat = {
  // Milliseconds after the previous beat (or after the step begins).
  wait: number;
  say?: Line;
  care?: CareChange[];
  record?: RecordRow;
  // The patient presses the page's one button.
  tap?: true;
};

export type Step = {
  when: string;
  // The time on the patient's phone.
  clock: string;
  door: Door;
  title: string;
  // The rule Ophi kept in this moment, stated as done.
  proof: string;
  // The one button on the personal page during this step.
  action?: string;
  beats: Beat[];
};

export const STEPS: Step[] = [
  {
    when: "Thursday, 7:42 pm",
    clock: "7:42",
    door: "call",
    title: "The clinic is closed. Alex calls anyway.",
    proof: "Name and birthday matched one patient file first",
    beats: [
      { wait: 400, say: { who: "alex", text: "Hi, um, I'd like to book a cleaning, please." } },
      {
        wait: 1500,
        say: { who: "ophi", text: "Thanks, Alex, I've got your file. I have Tuesday, November 10th at 4 PM, or Wednesday, November 11th at 3 PM. Which works better?" },
        care: [{ id: "cleaning", state: "planned", note: "Due this fall" }],
        record: { kind: "LOOKUP", text: "Martin, Alex · Nov 2, 1972 · one file" },
      },
      { wait: 2400, say: { who: "alex", text: "Oh, the first one works for me." } },
      {
        wait: 1400,
        say: { who: "ophi", text: "It's requested for Tuesday, November 10th at 4 PM, and you'll get a text once the clinic confirms." },
        care: [{ id: "cleaning", state: "waiting", note: "Tue Nov 10, 4:00 pm · needs your front desk’s yes" }],
        record: { kind: "REQUEST", text: "Cleaning · Tue Nov 10 4:00 PM · M. Chen" },
      },
    ],
  },
  {
    when: "Friday, 8:03 am",
    clock: "8:03",
    door: "text",
    title: "Your front desk says yes. Alex gets a text.",
    proof: "Sent only after the booking was checked in the record",
    beats: [
      { wait: 600, record: { kind: "APPROVED", text: "By the front desk, 8:03 AM" } },
      {
        wait: 1100,
        care: [{ id: "cleaning", state: "booked", note: "Tue Nov 10, 4:00 pm" }],
        record: { kind: "APPT", text: "Tue Nov 10 4:00 PM · Cleaning · saved" },
      },
      { wait: 1100, say: { who: "ophi", text: "Birchwood Family Dental: You’re booked for a cleaning and checkup on Tuesday, November 10th, at 4 PM. Questions? Call 416-555-0100." } },
    ],
  },
  {
    when: "Tuesday, November 10",
    clock: "4:51",
    door: "page",
    title: "At the checkup, Dr. Shah finds a cracked molar. The plan lands on Alex’s page.",
    proof: "No app, no password. One tap to book",
    action: "Book crown prep: Thu Nov 19, 9:30 am",
    beats: [
      {
        wait: 600,
        record: { kind: "TX PLAN", text: "Crown, lower left molar · 3 steps" },
        care: [
          { id: "cleaning", state: "done", note: "Nov 10" },
          { id: "prep", state: "planned", note: "Not booked yet" },
          { id: "estimate", state: "waiting", note: "Waiting on the insurer" },
          { id: "lab", state: "planned", note: "After prep" },
          { id: "fitting", state: "planned", note: "When the crown is back" },
        ],
      },
      { wait: 2600, tap: true },
      {
        wait: 700,
        care: [{ id: "prep", state: "booked", note: "Thu Nov 19, 9:30 am" }],
        record: { kind: "APPT", text: "Thu Nov 19 9:30 AM · Crown prep" },
      },
    ],
  },
  {
    when: "Tuesday, December 1",
    clock: "10:42",
    door: "text",
    title: "The lab delivers the crown. Nobody picks up a phone.",
    proof: "Sent when the record changed. Typed by no one",
    beats: [
      {
        wait: 400,
        care: [
          { id: "prep", state: "done", note: "Nov 19" },
          { id: "estimate", state: "done", note: "Your part: about $312" },
          { id: "lab", state: "waiting", note: "Waiting on the lab" },
        ],
      },
      { wait: 1500, record: { kind: "LAB", text: "Crown case received" }, care: [{ id: "lab", state: "done", note: "Arrived Dec 1" }] },
      { wait: 1100, say: { who: "ophi", text: "Your crown has arrived. Ready to book your fitting? Thursday Dec 3 at 9:30 am, or Friday Dec 4 at 1:00 pm." } },
      { wait: 1900, say: { who: "alex", text: "Thursday" } },
      {
        wait: 1200,
        say: { who: "ophi", text: "Booked: crown fitting, Thursday, December 3rd at 9:30 AM." },
        care: [{ id: "fitting", state: "booked", note: "Thu Dec 3, 9:30 am" }],
        record: { kind: "APPT", text: "Thu Dec 3 9:30 AM · Crown fitting" },
      },
    ],
  },
  {
    when: "Wednesday, 12:15 pm",
    clock: "12:15",
    door: "call",
    title: "Alex calls to move it. Ophi already knows what “it” is.",
    proof: "One memory behind every door",
    beats: [
      { wait: 500, say: { who: "alex", text: "Hi, can I move it to Friday?" } },
      { wait: 1700, say: { who: "ophi", text: "Your crown fitting, Thursday at 9:30? Friday the 4th at 1 PM is open." } },
      { wait: 2300, say: { who: "alex", text: "Perfect." } },
      {
        wait: 1200,
        say: { who: "ophi", text: "Done. It’s Friday, December 4th at 1 PM." },
        care: [{ id: "fitting", state: "booked", note: "Fri Dec 4, 1:00 pm" }],
        record: { kind: "MOVED", text: "Crown fitting · to Fri Dec 4 1:00 PM" },
      },
    ],
  },
  {
    when: "Friday, December 4",
    clock: "2:05",
    door: "page",
    title: "Crown fitted. Paid from the same page.",
    proof: "Treatment finished, and the next step already planned",
    action: "Pay $312",
    beats: [
      {
        wait: 600,
        record: { kind: "DONE", text: "Crown fitting · Dr. Shah" },
        care: [
          { id: "fitting", state: "done", note: "Dec 4" },
          { id: "balance", state: "waiting", note: "$312 due" },
          { id: "recall", state: "planned", note: "Due in June" },
        ],
      },
      { wait: 2600, tap: true },
      { wait: 700, care: [{ id: "balance", state: "done", note: "Paid Dec 4" }], record: { kind: "PAYMENT", text: "$312.00 received" } },
    ],
  },
];

// The opening call, word for word, with when each turn is spoken (seconds into the recording).
export const REAL_CALL = {
  src: "/calls/book-cleaning.mp3",
  duration: 42.9,
  turns: [
    { who: "ophi", start: 0.3, text: "Hi, I'm Ophi. Welcome to our dental office. How can I help you today?" },
    { who: "alex", start: 5.32, text: "Hi, um, I'd like to book a cleaning, please." },
    { who: "ophi", start: 8.75, text: "Sure. Have you been to our office before?" },
    { who: "alex", start: 12.11, text: "Yeah, I have. It's Alex Martin, November second, nineteen seventy-two." },
    { who: "ophi", start: 16.92, text: "Thanks, Alex, I've got your file. I have Tuesday, November 10th at 4 PM, or Wednesday, November 11th at 3 PM. Which works better?" },
    { who: "alex", start: 26.91, text: "Oh, the first one works for me." },
    { who: "ophi", start: 29.6, text: "It's requested for Tuesday, November 10th at 4 PM, and you'll get a text once the clinic confirms. Is there anything else I can help with?" },
    { who: "alex", start: 38.1, text: "No, that's it. Thanks so much. Bye." },
    { who: "ophi", start: 40.73, text: "Goodbye, Alex. Take care." },
  ] satisfies (Line & { start: number })[],
};

export type CareItem = { id: CareId; label: string; short: string; state: CareState; note: string; changed: boolean };
export type Frame = {
  // The timeline as Ophi remembers it: only what has come up so far.
  care: CareItem[];
  // Everything written to the clinic's records so far; `fresh` marks rows from the current step.
  record: (RecordRow & { fresh: boolean })[];
  // What has been said on the current step's door.
  lines: Line[];
  // The page's button: untouched, being pressed, or pressed with the change already in.
  tap: "no" | "pressing" | "done";
};

// The story's state after `beat` beats of `step` (-1: the step has begun and nothing has happened yet).
// Earlier steps count in full, so the three views always agree however the reader arrived.
export function frameAt(step: number, beat: number): Frame {
  const care = new Map<CareId, CareChange>();
  const changed = new Set<CareId>();
  const frame: Frame = { care: [], record: [], lines: [], tap: "no" };
  STEPS.slice(0, step + 1).forEach((s, i) => {
    const current = i === step;
    s.beats.slice(0, current ? beat + 1 : undefined).forEach((b, j) => {
      b.care?.forEach((c) => care.set(c.id, c));
      if (b.record) frame.record.push({ ...b.record, fresh: current });
      if (!current) return;
      if (b.say) frame.lines.push(b.say);
      if (b.tap) frame.tap = j === beat ? "pressing" : "done";
      if (j === beat) b.care?.forEach((c) => changed.add(c.id));
    });
  });
  frame.care = CARE.flatMap(({ id, label, short }) => {
    const now = care.get(id);
    return now ? [{ id, label, short, state: now.state, note: now.note, changed: changed.has(id) }] : [];
  });
  return frame;
}

export const lastBeat = (step: number) => STEPS[step].beats.length - 1;
