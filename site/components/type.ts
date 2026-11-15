// The page's one design system: a type scale, one card surface and one layout frame. Every section uses these
// and nothing else, so the page reads as one piece. Nothing a visitor is meant to read sits under 14px.

// Type scale. Display serif for headings, the sans for everything a visitor reads in passing.
export const display = "font-serif text-[length:clamp(50px,6.2vw,92px)] leading-[.98] tracking-[-.04em] text-balance";
export const heading = "font-serif text-[length:clamp(36px,4.1vw,60px)] leading-[1.04] tracking-[-.035em] text-balance";
export const title = "font-serif text-[length:clamp(23px,1.9vw,28px)] leading-[1.15] tracking-[-.02em]";
export const lede = "text-[length:clamp(18px,1.45vw,21px)] leading-[1.55] text-ink-soft text-pretty";
export const body = "text-[17px] leading-[1.55]";
export const small = "text-[15px] leading-[1.5]";
export const caption = "text-[14px] leading-[1.5] text-muted";

// Layout frame: one width, one gutter, one rhythm between sections.
export const frame = "mx-auto w-full max-w-[1240px] px-14 tablet:px-9 phone:px-5";
export const section = "pt-[clamp(96px,10vw,144px)] phone:pt-22";

// The one card: warm white on the ivory page, a soft shadow from above, never an outline alone.
export const card = "rounded-[28px] bg-card shadow-card phone:rounded-[22px]";
// A quieter surface inside a card or on the page: sage, flat.
export const well = "rounded-[20px] bg-sage";
