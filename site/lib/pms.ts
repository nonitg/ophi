// Kept apart from lib/subscribe.ts so the signup form's listbox doesn't pull zod into the browser.
// Canadian clinic PMS list first, then exits for readers who are not clinic staff.
// The answer steers which integration ships first, so the labels match how clinics name them.
export const PMS_OPTIONS = [
  "ABELDent",
  "ClearDent",
  "Dentrix",
  "Tracker",
  "Open Dental",
  "Paradigm",
  "Power Practice",
  "Curve",
  "Dentitek",
  "Progident",
  "Other",
  "I don't work in a clinic",
] as const;

export type Pms = (typeof PMS_OPTIONS)[number];
