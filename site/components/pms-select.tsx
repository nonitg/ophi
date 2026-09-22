"use client";

import { useEffect, useId, useRef, useState, useSyncExternalStore, type KeyboardEvent } from "react";
import { PMS_OPTIONS } from "@/lib/subscribe";
import { copy } from "@/lib/copy";
import { Icon } from "@/components/icons";

const subscribeNever = () => () => {};

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
      <div className="pms-field">
        <label className="sr-only" htmlFor="pms">{copy.form.pms}</label>
        <select id="pms" name="pms" className="pms-trigger" defaultValue=""><option value="">{copy.form.pmsPlaceholder}</option>{PMS_OPTIONS.map((option) => <option key={option} value={option}>{option}</option>)}</select>
      </div>
    );
  }

  return (
    <div ref={root} className="pms-field" data-open={open || undefined} data-drop-up={dropUp || undefined}>
      <span className="sr-only" id={`${id}-label`}>{copy.form.pms}</span>
      <input type="hidden" name="pms" value={value} />
      <button type="button" id="pms" role="combobox" className="pms-trigger" data-empty={value === "" || undefined}
        aria-labelledby={`${id}-label`} aria-haspopup="listbox" aria-expanded={open} aria-controls={`${id}-list`}
        aria-activedescendant={open ? `${id}-${active}` : undefined}
        onClick={() => (open ? setOpen(false) : show())} onKeyDown={onKeyDown} onBlur={() => setOpen(false)}>
        <span>{value || copy.form.pmsPlaceholder}</span>
        <Icon name="chevron" className="pms-chevron" />
      </button>
      <ul ref={list} id={`${id}-list`} role="listbox" aria-labelledby={`${id}-label`} className="pms-menu" tabIndex={-1}>
        {PMS_OPTIONS.map((option, index) => (
          <li key={option} id={`${id}-${index}`} role="option" aria-selected={option === value} data-active={index === active || undefined}
            onPointerMove={() => setActive(index)} onPointerDown={(event) => event.preventDefault()} onClick={() => choose(index)}>
            {option}
            {option === value && <Icon name="check" />}
          </li>
        ))}
      </ul>
    </div>
  );
}
