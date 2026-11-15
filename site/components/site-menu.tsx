"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, MotionConfig, motion } from "motion/react";
import { copy } from "@/lib/copy";
import { Icon } from "@/components/icons";
import { leave, soft, spring } from "@/components/motion";

// Below the wide layout the header's section links fold into one button, so phones can still jump around a long
// page. The list drops down under the header; picking a section, tapping outside or Escape closes it.
export function SiteMenu() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const close = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    addEventListener("keydown", close);
    return () => removeEventListener("keydown", close);
  }, [open]);

  return (
    <MotionConfig reducedMotion="user">
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} aria-controls="site-menu" aria-label={open ? "Close menu" : "Open menu"}
        className="hidden size-11 flex-none place-items-center rounded-full text-ink [transition:background_.2s,scale_.16s_var(--ease-out)] hover:bg-ink/5 active:scale-[.97] tablet:grid phone:size-10">
        {/* Two bars that cross into a close mark. */}
        <span className="relative h-3 w-[18px]" aria-hidden="true">
          <motion.span className="absolute inset-x-0 top-0 h-[1.5px] rounded-full bg-current" initial={false} animate={open ? { y: 5.25, rotate: 45 } : { y: 0, rotate: 0 }} transition={spring} />
          <motion.span className="absolute inset-x-0 bottom-0 h-[1.5px] rounded-full bg-current" initial={false} animate={open ? { y: -5.25, rotate: -45 } : { y: 0, rotate: 0 }} transition={spring} />
        </span>
      </button>
      <AnimatePresence>
        {open && (
          <>
            <motion.div key="scrim" className="absolute inset-x-0 top-full h-svh bg-ink/20 backdrop-blur-[2px]" onClick={() => setOpen(false)}
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, transition: leave }} transition={soft} aria-hidden="true" />
            <motion.nav key="menu" id="site-menu" aria-label="On this page" className="absolute inset-x-0 top-full rounded-b-[28px] bg-paper pb-4 shadow-[0_24px_48px_-24px_#193a3040]"
              initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8, transition: leave }} transition={soft}>
              <ul className="mx-auto grid w-full max-w-[1240px] px-9 phone:px-5">
                {copy.nav.map(({ href, label }, i) => (
                  <motion.li key={href} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ ...soft, delay: 0.04 * i }}>
                    <a href={href} onClick={() => setOpen(false)} className="group/link flex min-h-15 items-center justify-between font-serif text-[26px] leading-none tracking-[-.02em]">
                      {label}
                      <Icon name="next" className="size-5 text-ink-soft transition-transform duration-200 ease-(--ease-out) group-hover/link:translate-x-0.5" />
                    </a>
                  </motion.li>
                ))}
              </ul>
            </motion.nav>
          </>
        )}
      </AnimatePresence>
    </MotionConfig>
  );
}
