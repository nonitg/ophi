import React from "react";
import { Cold } from "./Cold";
import { Patient } from "./Patient";
import { Problem } from "./Problem";
import { Demo } from "./Demo";
import { Value } from "./Value";
import { Market } from "./Market";
import { Team } from "./Team";
import { Vision } from "./Vision";
import { Close } from "./Close";
import { End } from "./End";

// Section id (timeline.ts) → scene component.
export const scenes: Record<string, React.FC> = {
  cold: Cold,
  patient: Patient,
  problem: Problem,
  demo: Demo,
  value: Value,
  market: Market,
  team: Team,
  vision: Vision,
  close: Close,
  end: End,
};
