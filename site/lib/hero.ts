import { STEPS, frameAt, lastBeat, type CareId, type CareState, type Door } from "@/lib/story";

// The hero's picture of the product: four patients of the fictional Birchwood Family Dental, each with a different
// front-desk job (a reschedule, a question about their treatment, a recall, insurance), answered from their own care
// and written back to the clinic's records. Alex's lines are the story's (lib/story.ts); Chloé and Owen are the clinic
// view's patients (lib/team.ts); Priya appears only here.

export type Who = "patient" | "ophi";
export type Said = { who: Who; text: string };
export type HeroRow = { label: string; note: string; state: CareState; changed?: boolean };

type Beat = {
  // Milliseconds after the previous beat.
  wait: number;
  say?: Said;
  // The patient's care as Ophi reads it from the records now; replaces what showed before.
  rows?: HeroRow[];
  // The patient presses the page's button.
  tap?: true;
  // What Ophi did in the clinic's records shows.
  did?: true;
};

export type Moment = {
  id: string;
  name: string;
  door: Door;
  when: string;
  // What Ophi did in the clinic's records, said to the clinic.
  did: string;
  // The page door's one message, the time it offers, its one button, and the button once pressed.
  page?: { text: string; slot: string; action: string; done: string };
  beats: Beat[];
};

// The moment in the story where Alex calls to move "it": Ophi already knows what "it" is.
const MOVE = 4;
const said = (beat: number): Said => {
  const line = STEPS[MOVE].beats[beat].say!;
  return { who: line.who === "alex" ? "patient" : "ophi", text: line.text };
};
// The parts of Alex's crown that answer the question: the lab case and the fitting.
const alexRows = (beat: number, ids: CareId[] = ["lab", "fitting"]): HeroRow[] =>
  frameAt(MOVE, beat).care.filter(({ id }) => ids.includes(id)).map(({ label, note, state, changed }) => ({ label, note, state, changed }));

export const MOMENTS: Moment[] = [
  {
    id: "alex",
    name: "Alex Martin",
    door: "call",
    when: STEPS[MOVE].when,
    did: "Moved in your schedule and checked it saved",
    beats: [
      { wait: 300, say: said(0) },
      { wait: 700, rows: alexRows(-1) },
      { wait: 900, say: said(1) },
      { wait: 2100, say: said(2) },
      { wait: 1000, say: said(3), rows: alexRows(lastBeat(MOVE)) },
      { wait: 900, did: true },
    ],
  },
  {
    // A question only the chart can answer: what was done, when, and what the dentist noted. Never a diagnosis.
    id: "priya",
    name: "Priya Nair",
    door: "text",
    when: "Thursday, 9:12 am",
    did: "Answered from Dr. Shah’s notes. Checking in with her Monday",
    beats: [
      { wait: 300, say: { who: "patient", text: "My tooth is still sore from Tuesday’s filling. Is that normal?" } },
      {
        wait: 700,
        rows: [
          { label: "Filling, lower right molar", note: "Tue Nov 24 · Dr. Shah", state: "done" },
          { label: "Check-in", note: "Not set", state: "planned" },
        ],
      },
      { wait: 900, say: { who: "ophi", text: "Dr. Shah noted it can stay sensitive for up to two weeks. If it gets worse, I can book you in today." } },
      { wait: 2100, say: { who: "patient", text: "Okay, thank you!" } },
      { wait: 1000, rows: [
        { label: "Filling, lower right molar", note: "Tue Nov 24 · Dr. Shah", state: "done" },
        { label: "Check-in", note: "Text Mon Nov 30", state: "booked", changed: true },
      ] },
      { wait: 900, did: true },
    ],
  },
  {
    id: "chloe",
    name: "Chloé Tremblay",
    door: "page",
    when: "Wednesday, 12:33 pm",
    did: "Booked in your schedule and checked it saved",
    page: { text: "Hi Chloé, your six-month cleaning is due. Here’s the next open time with Dr. Shah.", slot: "Wed Dec 9, 11:00 am", action: "Book this time", done: "Booked" },
    beats: [
      { wait: 300, rows: [{ label: "Six-month cleaning", note: "Due since October", state: "planned" }] },
      { wait: 1900, tap: true },
      { wait: 600, rows: [{ label: "Six-month cleaning", note: "Wed Dec 9, 11:00 am", state: "booked", changed: true }] },
      { wait: 900, did: true },
    ],
  },
  {
    // The insurance side of the desk: Owen's estimate is the one the clinic view shows Ophi asked for.
    id: "owen",
    name: "Owen Brooks",
    door: "call",
    when: "Wednesday, 10:05 am",
    did: "Followed up with his insurer and noted it on his file",
    beats: [
      { wait: 300, say: { who: "patient", text: "Hi, has my insurance come back on the root canal?" } },
      {
        wait: 700,
        rows: [
          { label: "Insurance estimate", note: "Sent Monday, no reply yet", state: "waiting" },
          { label: "Root canal", note: "Once the estimate is back", state: "planned" },
        ],
      },
      { wait: 900, say: { who: "ophi", text: "Not yet. We sent it Monday, so I’m asking your insurer for an update now." } },
      { wait: 2100, say: { who: "ophi", text: "I’ll text you your share as soon as it’s in, with times for the root canal." } },
      { wait: 1000, rows: [
        { label: "Insurance estimate", note: "Followed up today", state: "waiting", changed: true },
        { label: "Root canal", note: "Once the estimate is back", state: "planned" },
      ] },
      { wait: 900, did: true },
    ],
  },
];

export type Shown = { lines: Said[]; rows: HeroRow[]; tap: "no" | "pressing" | "done"; did: boolean };

// What a moment shows after `beat` beats (-1: nothing yet).
export function shownAt(moment: Moment, beat: number): Shown {
  const shown: Shown = { lines: [], rows: [], tap: "no", did: false };
  moment.beats.slice(0, beat + 1).forEach((b, i) => {
    if (b.say) shown.lines.push(b.say);
    if (b.rows) shown.rows = b.rows;
    if (b.tap) shown.tap = i === beat ? "pressing" : "done";
    if (b.did) shown.did = true;
  });
  return shown;
}

export const lastHeroBeat = (moment: Moment) => moment.beats.length - 1;
