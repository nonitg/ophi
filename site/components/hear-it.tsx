"use client";

import { useEffect, useId, useState } from "react";
import { Icon } from "@/components/icons";
import { pill, pillIcon, pillTag } from "@/components/pill";

// Claims on the page point at the recorded moment that backs them. The call player (components/call-player.tsx) plays
// it on HEAR_EVENT and says on NOW_EVENT which button's moment is playing, so that button can offer a pause.
export const HEAR_EVENT = "ophi:hear";
export const NOW_EVENT = "ophi:now";
// `show` also brings the call sheet into view, for a press that means "take me to the calls".
export type HearDetail = { slug: string; t: number; source: string; show?: boolean };
export type NowDetail = { source: string | null };

export function HearIt({ slug, t, label, about, show }: { slug: string; t: number; label: string; about?: string; show?: boolean }) {
  const id = useId();
  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    const heard = (event: Event) => setPlaying((event as CustomEvent<NowDetail>).detail.source === id);
    window.addEventListener(NOW_EVENT, heard);
    return () => window.removeEventListener(NOW_EVENT, heard);
  }, [id]);
  return (
    // Pressing it again pauses: the moment plays where the reader is, so the way to stop it has to be here too.
    <button type="button" className={pill({ className: "hear-it" })} aria-pressed={playing} aria-label={about ? `${label}: ${about}` : undefined} onClick={() => window.dispatchEvent(new CustomEvent<HearDetail>(HEAR_EVENT, { detail: { slug, t, source: id, show } }))}>
      {label}<span className={pillTag()} data-done={playing || undefined}><Icon name={playing ? "pause" : "play"} className={`${pillIcon} ${playing ? "" : "group-hover/pill:translate-x-px"}`} /></span>
    </button>
  );
}
