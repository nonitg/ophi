// One drawn icon family: 20px grid, 1.4 stroke, round caps, so every control shares the pills' softness.
const paths = {
  arrow: <path d="M6 14 14 6M7.5 6H14v6.5" />,
  up: <path d="M10 15.5V4.5M5 9.5l5-5 5 5" />,
  plus: <path d="M10 4.5v11M4.5 10h11" />,
  close: <path d="m5.5 5.5 9 9m0-9-9 9" />,
  check: <path d="m4.5 10.5 3.5 3.5 7.5-8" />,
  chevron: <path d="m5.5 8 4.5 4.5L14.5 8" />,
  copy: <><rect x="7" y="7" width="9" height="9.5" rx="2" /><path d="M13 5V4.5A1.5 1.5 0 0 0 11.5 3h-7A1.5 1.5 0 0 0 3 4.5v7A1.5 1.5 0 0 0 4.5 13H5" /></>,
};

export function Icon({ name, className }: { name: keyof typeof paths; className?: string }) {
  return (
    <svg className={className ? `icon ${className}` : "icon"} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {paths[name]}
    </svg>
  );
}
