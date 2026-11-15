"use client";

import { useEffect } from "react";

// Marks every [data-reveal] block `.in` the first time it comes into view, so it rises into place (globals.css).
export function Reveal() {
  useEffect(() => {
    const blocks = document.querySelectorAll<HTMLElement>("[data-reveal]");
    if (!("IntersectionObserver" in window)) {
      blocks.forEach((el) => el.classList.add("in"));
      return;
    }
    const observer = new IntersectionObserver((entries) => {
      for (const { isIntersecting, target } of entries) {
        if (!isIntersecting) continue;
        target.classList.add("in");
        observer.unobserve(target);
      }
    }, { rootMargin: "0px 0px -12% 0px" });
    blocks.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);
  return null;
}
