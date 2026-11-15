// One drawn icon family: 20px grid, 1.4 stroke, round caps, so every control shares the pills' softness.
const paths = {
  arrow: <path d="M6 14 14 6M7.5 6H14v6.5" />,
  next: <path d="M4 10h12M11 5l5 5-5 5" />,
  up: <path d="M10 15.5V4.5M5 9.5l5-5 5 5" />,
  down: <path d="M10 4.5v11M5 10.5l5 5 5-5" />,
  play: <path d="M7.5 5.2v9.6l7.6-4.8z" fill="currentColor" />,
  pause: <path d="M7.2 5.2v9.6M12.8 5.2v9.6" />,
  plus: <path d="M10 4.5v11M4.5 10h11" />,
  close: <path d="m5.5 5.5 9 9m0-9-9 9" />,
  check: <path d="m4.5 10.5 3.5 3.5 7.5-8" />,
  chevron: <path d="m5.5 8 4.5 4.5L14.5 8" />,
  copy: <><rect x="7" y="7" width="9" height="9.5" rx="2" /><path d="M13 5V4.5A1.5 1.5 0 0 0 11.5 3h-7A1.5 1.5 0 0 0 3 4.5v7A1.5 1.5 0 0 0 4.5 13H5" /></>,
  // The parts behind a reply (components/how-it-works.tsx).
  wave: <path d="M4.5 8.5v3M7.25 6v8M10 4v12M12.75 6.5v7M15.5 8.5v3" />,
  route: <path d="M3.5 10H8l4.2-4.6h4.3M8 10l4.2 4.6h4.3" />,
  calendar: <><rect x="3.5" y="4.5" width="13" height="12" rx="2.5" /><path d="M3.5 8.5h13M7 3v3M13 3v3M7.6 12.4l1.7 1.7 3.2-3.4" /></>,
  speech: <path d="M4 5.5A1.5 1.5 0 0 1 5.5 4h9A1.5 1.5 0 0 1 16 5.5v6a1.5 1.5 0 0 1-1.5 1.5H9.5L6 16v-3h-.5A1.5 1.5 0 0 1 4 11.5z" />,
  person: <><circle cx="10" cy="7" r="3" /><path d="M4.5 16.5c.5-3 2.7-4.7 5.5-4.7s5 1.7 5.5 4.7" /></>,
  // The clinic's records: a two-drawer cabinet.
  records: <><rect x="3.5" y="3.5" width="13" height="13" rx="2.5" /><path d="M3.5 10h13M8.5 6.8h3M8.5 13.2h3" /></>,
  // The three doors a patient can use, and the lock on their page.
  phone: <path d="M6.3 3.5h1.9l1.1 3-1.5 1.2a8.4 8.4 0 0 0 4.5 4.5l1.2-1.5 3 1.1v1.9a1.5 1.5 0 0 1-1.6 1.5A12.2 12.2 0 0 1 4.8 5.1a1.5 1.5 0 0 1 1.5-1.6Z" />,
  page: <><rect x="4.5" y="3" width="11" height="14" rx="2.5" /><path d="M7.5 7h5M7.5 10h5M7.5 13h3" /></>,
  // A clipboard: forms a patient fills in.
  forms: <><rect x="4.5" y="4" width="11" height="13" rx="2.5" /><path d="M8 2.8h4v2.6H8zM7.5 10h5M7.5 13h3" /></>,
  lock: <><rect x="5" y="9" width="10" height="7.5" rx="2" /><path d="M7.2 9V6.8a2.8 2.8 0 0 1 5.6 0V9" /></>,
  // An original maple leaf, not the flag's eleven-point one. Filled, so it still reads at text size.
  leaf: <><path d="M10 1.4 11.3 4.6 13 3.8 12.6 8 15.2 6.3 15.6 7.7 18.4 7.2 17.2 9.6 18 10.4 14.4 12.7 14.9 14.3 10.7 13.4 9.3 13.4 5.1 14.3 5.6 12.7 2 10.4 2.8 9.6 1.6 7.2 4.4 7.7 4.8 6.3 7.4 8 7 3.8 8.7 4.6Z" fill="currentColor" strokeWidth=".9" /><path d="M10 13.4v5" /></>,
};

export type IconName = keyof typeof paths;

export function Icon({ name, className }: { name: IconName; className?: string }) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {paths[name]}
    </svg>
  );
}
