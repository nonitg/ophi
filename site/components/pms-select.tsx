"use client";

import { useEffect, useId, useRef, useState, useSyncExternalStore, type KeyboardEvent } from "react";
import { PMS_OPTIONS } from "@/lib/pms";
import { copy } from "@/lib/copy";
import { Icon } from "@/components/icons";

const subscribeNever = () => () => {};

// Clinic software: a custom listbox that opens in place with a short settle, matching the email pill.
// On the sage band the trigger takes the band outline; while open it keeps its hover look.
const trigger = "pms-trigger flex h-[46px] w-full appearance-none items-center justify-between gap-3 rounded-full border border-band-line bg-transparent pr-4.5 pl-5 text-left text-[13px] text-ink transition-[border-color,background] duration-250 hover:border-field-line hover:bg-field focus-visible:border-sage-deep focus-visible:outline-none aria-expanded:border-field-line aria-expanded:bg-field";

// Select-only combobox (WAI-ARIA APG): focus stays on the trigger, the active option is announced via aria-activedescendant.
// Before hydration a native select keeps the optional answer working without JavaScript.
export function PmsSelect() {
  const [value, setValue] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [dropUp, setDropUp] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const list = useRef<HTMLUListElement>(null);
  const typed = useRef({ text: "", at: 0 });
  const id = useId();
  // False on the server and during hydration, true once the client has taken over.
  const enhanced = useSyncExternalStore(subscribeNever, () => true, () => false);

  useEffect(() => {
    if (!open) return;
    const close = (event: PointerEvent) => { if (!root.current?.contains(event.target as Node)) setOpen(false); };
    document.addEventListener("pointerdown", close);
    return () => document.removeEventListener("pointerdown", close);
  }, [open]);

  useEffect(() => {
    if (open) list.current?.children[active]?.scrollIntoView({ block: "nearest" });
  }, [open, active]);

  function show() {
    const box = root.current!.getBoundingClientRect();
    // Opens upward only when the menu would be cut off below and there is more room above.
    setDropUp(innerHeight - box.bottom < 300 && box.top > innerHeight - box.bottom);
    setActive(Math.max(0, PMS_OPTIONS.indexOf(value as never)));
    setOpen(true);
  }

  function choose(index: number) {
    setValue(PMS_OPTIONS[index]);
    setOpen(false);
  }

  function jumpTo(key: string) {
    const now = Date.now();
    typed.current = { text: (now - typed.current.at < 600 ? typed.current.text : "") + key.toLowerCase(), at: now };
    const match = PMS_OPTIONS.findIndex((option) => option.toLowerCase().startsWith(typed.current.text));
    if (match >= 0) setActive(match);
  }

  function onKeyDown(event: KeyboardEvent) {
    const last = PMS_OPTIONS.length - 1;
    const moves: Record<string, number> = { ArrowDown: Math.min(active + 1, last), ArrowUp: Math.max(active - 1, 0), Home: 0, End: last, PageDown: Math.min(active + 5, last), PageUp: Math.max(active - 5, 0) };
    if (!open) {
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) { event.preventDefault(); show(); }
      return;
    }
    if (event.key in moves) { event.preventDefault(); setActive(moves[event.key]); }
    else if (event.key === "Enter" || event.key === " ") { event.preventDefault(); choose(active); }
    else if (event.key === "Escape") { event.preventDefault(); setOpen(false); }
    else if (event.key === "Tab") choose(active);
    else if (event.key.length === 1) jumpTo(event.key);
  }

  if (!enhanced) {
    return (
      <div className="relative mt-2.5">
        <label className="sr-only" htmlFor="pms">{copy.form.pms}</label>
        <select id="pms" name="pms" className={`${trigger} bg-(image:--select-chevron) bg-size-[18px] bg-[position:right_16px_center] bg-no-repeat`} defaultValue=""><option value="">{copy.form.pmsPlaceholder}</option>{PMS_OPTIONS.map((option) => <option key={option} value={option}>{option}</option>)}</select>
      </div>
    );
  }

  return (
    <div ref={root} className="group/pms relative mt-2.5" data-open={open || undefined}>
      <span className="sr-only" id={`${id}-label`}>{copy.form.pms}</span>
      <input type="hidden" name="pms" value={value} />
      <button type="button" id="pms" role="combobox" className={`${trigger} data-[empty]:text-muted tiny:gap-2 tiny:pr-3.5 tiny:pl-4`} data-empty={value === "" || undefined}
        aria-labelledby={`${id}-label`} aria-haspopup="listbox" aria-expanded={open} aria-controls={`${id}-list`}
        aria-activedescendant={open ? `${id}-${active}` : undefined}
        onClick={() => (open ? setOpen(false) : show())} onKeyDown={onKeyDown} onBlur={() => setOpen(false)}>
        {/* Phones show the shorter prompt, which fits the narrower trigger whole. */}
        <span className="min-w-0 truncate">{value || <><span className="phone:hidden">{copy.form.pmsPlaceholder}</span><span className="hidden phone:inline">{copy.form.pmsPlaceholderShort}</span></>}</span>
        <Icon name="chevron" className="pms-chevron size-[18px] flex-none transition-transform duration-350 ease-out group-data-[open]/pms:rotate-180" />
      </button>
      <ul ref={list} id={`${id}-list`} role="listbox" aria-labelledby={`${id}-label`} tabIndex={-1}
        // Closed, it waits out its motion before hiding; open, it shows at once.
        className={`pms-menu invisible absolute inset-x-0 z-20 max-h-[min(440px,62svh)] overflow-y-auto overscroll-contain rounded-[22px] border border-[#d1d8c6] bg-paper p-1.5 opacity-0 shadow-[0_18px_42px_-14px_#10231940,0_2px_6px_-2px_#1023191a] [scrollbar-width:none] [transition:opacity_.18s_ease-out,transform_.32s_var(--ease-out),visibility_0s_.32s] [&::-webkit-scrollbar]:hidden group-data-[open]/pms:visible group-data-[open]/pms:transform-none group-data-[open]/pms:opacity-100 group-data-[open]/pms:delay-0 xray:border-line xray:bg-[#142a22] xray:shadow-[0_18px_42px_-14px_#000000b3] ${dropUp ? "bottom-[calc(100%+6px)] origin-bottom [transform:translateY(6px)_scale(.98)]" : "top-[calc(100%+6px)] origin-top [transform:translateY(-6px)_scale(.98)]"}`}>
        {PMS_OPTIONS.map((option, index) => (
          <li key={option} id={`${id}-${index}`} role="option" aria-selected={option === value} data-active={index === active || undefined}
            // The last two options are exits for non-clinic readers, set apart from the software list.
            className="flex min-h-[34px] items-center justify-between rounded-full px-3.5 text-[13px] transition-[background] duration-150 aria-selected:font-medium data-[active]:bg-sage nth-last-2:relative nth-last-2:mt-[7px] nth-last-2:before:absolute nth-last-2:before:inset-x-3.5 nth-last-2:before:-top-1 nth-last-2:before:border-t nth-last-2:before:border-line xray:data-[active]:bg-[#e6ece31a]"
            onPointerMove={() => setActive(index)} onPointerDown={(event) => event.preventDefault()} onClick={() => choose(index)}>
            {option}
            {option === value && <Icon name="check" className="size-4 text-sage-deep" />}
          </li>
        ))}
      </ul>
    </div>
  );
}
