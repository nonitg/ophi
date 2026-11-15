import { useEffect, useState, type RefObject } from "react";

// Whether at least `threshold` of an element is on screen: the page's moving parts only run while they can be seen.
// With `once`, it stays true after the first sighting (for things that build themselves a single time). `initial` is
// the answer until the element is first measured, the server's render included.
export function useInView(ref: RefObject<HTMLElement | null>, threshold = 0.5, once = false, initial = false) {
  const [inView, setInView] = useState(initial);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(([entry]) => {
      setInView(entry.isIntersecting);
      if (once && entry.isIntersecting) observer.disconnect();
    }, { threshold });
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref, threshold, once]);
  return inView;
}
