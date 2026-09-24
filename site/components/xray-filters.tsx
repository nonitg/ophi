// Display type on the X-ray film (the headline and footer wordmark's xray: filter) reads the way the tooth does: faint mass, density building
// toward the outline, a bright rim, and halation around it. Edges come from the rendered glyphs rather than
// a text stroke, so a variable font's overlapping contours never show.
export function XrayFilters() {
  return (
    <svg className="absolute size-0 overflow-hidden" aria-hidden="true" focusable="false">
      <filter id="xray-density" x="-10%" y="-10%" width="120%" height="120%" colorInterpolationFilters="sRGB">
        <feFlood floodColor="#e6ece3" floodOpacity=".14" />
        <feComposite in2="SourceAlpha" operator="in" result="mass" />
        <feMorphology in="SourceAlpha" operator="erode" radius="5" result="deep" />
        <feComposite in="SourceAlpha" in2="deep" operator="out" result="shell" />
        <feGaussianBlur in="shell" stdDeviation="2.5" />
        <feComposite in2="SourceAlpha" operator="in" result="shell-soft" />
        <feFlood floodColor="#e6ece3" floodOpacity=".32" />
        <feComposite in2="shell-soft" operator="in" result="falloff" />
        <feMorphology in="SourceAlpha" operator="erode" radius="1.4" result="core" />
        <feComposite in="SourceAlpha" in2="core" operator="out" result="ring" />
        <feFlood floodColor="#f2f7f0" />
        <feComposite in2="ring" operator="in" result="rim" />
        <feGaussianBlur in="SourceAlpha" stdDeviation="12" result="haze" />
        <feFlood floodColor="#bfe3cf" floodOpacity=".2" />
        <feComposite in2="haze" operator="in" result="halo" />
        <feMerge><feMergeNode in="halo" /><feMergeNode in="mass" /><feMergeNode in="falloff" /><feMergeNode in="rim" /></feMerge>
      </filter>
    </svg>
  );
}
