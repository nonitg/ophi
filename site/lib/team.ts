import type { CareState } from "@/lib/story";

// The clinic's side of Ophi as a working miniature (components/team-view.tsx): a few patients of the fictional
// Birchwood Family Dental on one Wednesday, the things that happen to them while the reader watches, and the one
// change this clinic's rules hold for a yes. Illustration only: no real patients.

export type Trail = { at: string; text: string };
export type Row = {
  id: string;
  name: string;
  care: string;
  // The steps of this patient's treatment, in order.
  marks: CareState[];
  next: string;
  // The last thing Ophi did for them.
  move: string;
  trail: Trail[];
  // Held for the team's yes.
  ask?: true;
};
export type Tally = { calls: number; updates: number; booked: number };
type Patch = Pick<Row, "marks" | "next" | "move">;

const START: Row[] = [
  {
    id: "jordan", name: "Jordan Lee", care: "Wisdom teeth", marks: ["done", "waiting"], next: "Asks to move surgery to Dec 14", move: "Needs your yes", ask: true,
    trail: [
      { at: "11:40 am", text: "Jordan called to move his surgery" },
      { at: "11:40 am", text: "Mon Dec 14, 9:00 am is free with Dr. Shah" },
      { at: "11:41 am", text: "Your rule: surgery changes wait for a yes" },
    ],
  },
  {
    id: "alex", name: "Alex Martin", care: "Crown", marks: ["done", "done", "done", "done", "booked"], next: "Fitting, Fri 1:00 pm", move: "Moved the fitting when Alex called",
    trail: [
      { at: "12:15 pm", text: "Alex called to move the crown fitting" },
      { at: "12:15 pm", text: "Fri Dec 4, 1:00 pm was free" },
      { at: "12:16 pm", text: "Moved in your schedule, then read back" },
      { at: "12:16 pm", text: "Texted Alex the new time" },
    ],
  },
  {
    id: "margaret", name: "Margaret O’Neil", care: "Denture reline", marks: ["done", "waiting", "planned"], next: "Waiting on the lab", move: "Told her it’s due back today",
    trail: [
      { at: "Mon 2:10 pm", text: "Margaret texted to ask where her denture was" },
      { at: "Mon 2:10 pm", text: "Your records showed the lab case due Wednesday" },
      { at: "Mon 2:10 pm", text: "Told her, and that she’d hear when it arrives" },
    ],
  },
  {
    id: "chloe", name: "Chloé Tremblay", care: "Cleaning", marks: ["planned"], next: "Due since October", move: "Reminder goes out today",
    trail: [{ at: "Oct 28", text: "Six months since her last cleaning" }],
  },
  {
    id: "owen", name: "Owen Brooks", care: "Root canal", marks: ["done", "waiting", "planned"], next: "Waiting on the insurer", move: "Asked the insurer for an estimate",
    trail: [
      { at: "Mon 9:05 am", text: "Dr. Shah planned a root canal" },
      { at: "Mon 9:06 am", text: "Asked the insurer for an estimate" },
    ],
  },
  {
    id: "nadia", name: "Nadia Rahman", care: "New patient", marks: ["booked"], next: "First exam, Mon 10:00 am", move: "Registered her by phone last night",
    trail: [
      { at: "Tue 9:48 pm", text: "Nadia called after hours" },
      { at: "Tue 9:50 pm", text: "Took her name, birthday and insurance once" },
      { at: "8:02 am", text: "You approved the first exam. Nadia got a text" },
    ],
  },
];

const START_TALLY: Tally = { calls: 38, updates: 57, booked: 16 };

// What happens while the reader watches, in order. `now` is the line the team sees as it happens.
export const EVENTS: { id: string; now: string; patch: Patch; trail: Trail[]; tally: Partial<Tally> }[] = [
  {
    id: "margaret", now: "Margaret’s denture came back from the lab. She booked her fitting by text.",
    patch: { marks: ["done", "done", "booked"], next: "Fitting, Thu 2:00 pm", move: "Lab case arrived. She booked by text" },
    trail: [
      { at: "12:22 pm", text: "Lab case marked received in your records" },
      { at: "12:22 pm", text: "Texted Margaret two times to choose from" },
      { at: "12:24 pm", text: "She picked Thu 2:00 pm. Booked, then read back" },
    ],
    tally: { updates: 1, booked: 1 },
  },
  {
    id: "nadia", now: "Nadia called to ask about parking. Ophi answered in your clinic’s words.",
    patch: { marks: ["booked"], next: "First exam, Mon 10:00 am", move: "Answered her parking question" },
    trail: [{ at: "12:27 pm", text: "Nadia called about parking. Answered from your rules" }],
    tally: { calls: 1 },
  },
  {
    id: "chloe", now: "Chloé booked her overdue cleaning from her page.",
    patch: { marks: ["booked"], next: "Cleaning, Wed Dec 9, 11:00 am", move: "Reminded her. She booked from her page" },
    trail: [
      { at: "12:30 pm", text: "Sent the reminder with a link to her page" },
      { at: "12:33 pm", text: "She tapped Wed Dec 9, 11:00 am. Booked, then read back" },
    ],
    tally: { updates: 1, booked: 1 },
  },
  {
    id: "owen", now: "Owen’s insurance estimate came back. Ophi sent it to him.",
    patch: { marks: ["done", "done", "planned"], next: "Ready to book", move: "Estimate back. Sent it to Owen" },
    trail: [
      { at: "12:36 pm", text: "Estimate arrived in your records" },
      { at: "12:36 pm", text: "Sent Owen his part, with times to book" },
    ],
    tally: { updates: 1 },
  },
];

// What one yes sets off for the held request; the trail lines themselves are copy.team.approved.
export const APPROVAL = {
  id: "jordan",
  patch: { marks: ["done", "booked"], next: "Surgery, Mon Dec 14, 9:00 am", move: "You approved. Jordan got a text" } satisfies Patch,
  tally: { updates: 1, booked: 1 } satisfies Partial<Tally>,
};

const add = (tally: Tally, more: Partial<Tally>): Tally => ({ calls: tally.calls + (more.calls ?? 0), updates: tally.updates + (more.updates ?? 0), booked: tally.booked + (more.booked ?? 0) });

// The team view after `events` things have happened, with the held request approved or not.
export function teamAt(events: number, approved: boolean) {
  let tally = START_TALLY;
  const rows = new Map(START.map((row) => [row.id, row]));
  for (const { id, patch, trail, tally: more } of EVENTS.slice(0, events)) {
    const row = rows.get(id)!;
    rows.set(id, { ...row, ...patch, trail: [...row.trail, ...trail] });
    tally = add(tally, more);
  }
  if (approved) {
    const row = rows.get(APPROVAL.id)!;
    rows.set(APPROVAL.id, { ...row, ...APPROVAL.patch, ask: undefined });
    tally = add(tally, APPROVAL.tally);
  }
  const latest = events ? EVENTS[events - 1] : null;
  return { rows: [...rows.values()], tally, latest: latest?.id ?? null, now: latest?.now ?? null };
}
