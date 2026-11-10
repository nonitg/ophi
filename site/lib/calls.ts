// The recorded calls on the homepage. Each is a real call on Ophi's phone line, exported by ophi-phone
// (scripts/site_demo_export.py) as public/calls/<slug>.mp3 plus lib/calls/<slug>.json. The words and timings are
// the recording's; only the titles and the plain-language notes are written here.
import { copy } from "@/lib/copy";
import askForPerson from "./calls/ask-for-person.json";
import bookCleaning from "./calls/book-cleaning.json";
import emergency from "./calls/emergency.json";
import frustrated from "./calls/frustrated.json";
import newPatient from "./calls/new-patient.json";
import question from "./calls/question.json";
import slowDown from "./calls/slow-down.json";

export type Turn = { who: "ophi" | "caller"; start: number; end: number; text: string };
type Action = { t: number; tool: string; args: Record<string, unknown>; result: Record<string, unknown> };
export type Proposal = { kind: string; title: string; details: Record<string, string>; flags: string[] };
export type Recording = {
  slug: string;
  duration: number;
  // YYYY-MM-DD the call was placed.
  recordedAt: string;
  turns: Turn[];
  actions: Action[];
  proposals: Proposal[];
  // What Ophi wrote for the team at the end; a transferred call has none.
  summary: string | null;
  // Loudness per speaker, `rate` readings a second.
  peaks: { rate: number; caller: number[]; ophi: number[] };
};

// What the page needs from a recording: small enough to send to the browser with the page.
export type DemoCall = {
  slug: string;
  title: string;
  blurb: string;
  caller: string;
  src: string;
  duration: number;
  turns: Turn[];
  // What Ophi did behind the words. `before` is the turn it led to (turns.length: after the last one).
  notes: { t: number; before: number; text: string }[];
  bars: { caller: number[]; ophi: number[] };
  summary: string;
};

const BARS = 120;

// A tool call in the caller's terms; null for calls that aren't worth a line.
export function noteFor({ tool, args, result }: Action): string | null {
  switch (tool) {
    case "verify_patient": return result.verified ? "Checked the name and date of birth against the patient file" : "No match under that name, so it asked for the spelling";
    case "get_open_slots": return "Read the open times from the schedule";
    case "propose_booking": return "Sent the booking to the front desk to approve";
    case "propose_new_patient": return "Sent the new patient and first visit to the front desk to approve";
    case "propose_reschedule": return "Sent the change to the front desk to approve";
    case "propose_cancel": return "Sent the cancellation to the front desk to approve";
    case "request_callback": return "Left a message for the team to call back";
    case "transfer_to_staff": return "Transferred to the team, with a note saying why";
    case "set_pace": return args.pace === "slower" ? "Slowed its speech, and now waits longer before replying" : "Back to its usual pace";
    default: return null;
  }
}

// The loudest reading in each of `count` equal stretches, eased so quiet speech still shows.
function bars(peaks: number[], count: number): number[] {
  const step = peaks.length / count;
  return Array.from({ length: count }, (_, i) => {
    const slice = peaks.slice(Math.floor(i * step), Math.max(Math.floor(i * step) + 1, Math.floor((i + 1) * step)));
    return Math.round(Math.sqrt(Math.max(0, ...slice)) * 100) / 100;
  });
}

export function demoCall(rec: Recording): DemoCall {
  const words = copy.listen.calls[rec.slug as keyof typeof copy.listen.calls] ?? { title: rec.slug, blurb: "", caller: "Caller" };
  const notes: DemoCall["notes"] = [];
  for (const action of rec.actions) {
    const text = noteFor(action);
    // A note sits just before the reply it led to.
    const reply = rec.turns.findIndex((turn) => turn.who === "ophi" && turn.end > action.t);
    const before = reply === -1 ? rec.turns.length : reply;
    if (text && !notes.some((n) => n.before === before && n.text === text)) notes.push({ t: action.t, before, text });
  }
  return {
    slug: rec.slug, ...words, src: `/calls/${rec.slug}.mp3`, duration: rec.duration, turns: rec.turns, notes,
    bars: { caller: bars(rec.peaks.caller, BARS), ophi: bars(rec.peaks.ophi, BARS) },
    // A transfer leaves the team its reason instead of a summary.
    summary: rec.summary ?? rec.proposals[0]?.details.message ?? "",
  };
}

// The recorded moment that shows a skill: Ophi's first words after `tool` runs, or its first reply in the call.
// It plays from what the caller said to set it off. A transfer's proof is the note it left the team, not the hand-off line.
export function moment(rec: Recording, tool?: string): { t: number; quote: string; note?: string } | null {
  const action = rec.actions.find((a) => a.tool === tool);
  const after = tool ? action?.t : rec.turns.find((turn) => turn.who === "caller")?.end;
  const reply = after === undefined ? -1 : rec.turns.findIndex((turn) => turn.who === "ophi" && turn.end > after);
  if (reply === -1) return null;
  const said = rec.turns.slice(0, reply).findLast((turn) => turn.who === "caller") ?? rec.turns[reply];
  const reason = action?.args.reason;
  return { t: Math.max(0, said.start - .3), quote: rec.turns[reply].text, ...(typeof reason === "string" && { note: reason }) };
}

// "November 10, 2026": the transcripts name dates relative to the day they were recorded.
export const recordedOn = (rec: Recording) => new Date(`${rec.recordedAt}T12:00:00Z`).toLocaleDateString("en-CA", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });

// In listening order. The first call is also the request shown waiting at the front desk.
export const recordings = [bookCleaning, slowDown, askForPerson, frustrated, emergency, newPatient, question] as Recording[];
