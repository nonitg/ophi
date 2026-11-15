import { STEPS, frameAt, lastBeat, type CareId, type CareState, type Door } from "@/lib/story";

// The hero's picture of the product: three patients of the fictional Birchwood Family Dental, each reaching Ophi
// through a different door, each answered from their own care and written back to the clinic's records.
// Alex's lines are the story's (lib/story.ts); Margaret and Chloé are the clinic view's patients (lib/team.ts).

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
    id: "margaret",
    name: "Margaret O’Neil",
    door: "text",
    when: "Monday, 2:10 pm",
    did: "Answered. She’ll get a text when it arrives",
    beats: [
      { wait: 300, say: { who: "patient", text: "Hi, is my denture back from the lab yet?" } },
      {
        wait: 700,
        rows: [
          { label: "Reline at the lab", note: "Due back Wed, Dec 2", state: "waiting" },
          { label: "Denture fitting", note: "When it’s back", state: "planned" },
        ],
      },
      { wait: 900, say: { who: "ophi", text: "Not yet. The lab has it due back Wednesday, and I’ll text you the moment it arrives." } },
      { wait: 2000, say: { who: "patient", text: "Perfect, thank you!" } },
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
