import { cva } from "class-variance-authority";

// Secondary actions share one shape: an outlined pill ending in a sage tag, echoing the orange join pill.
// Pass the same surface and size to the pill and its tag. Controls on the sage band take the paper tone so
// they stay distinct from it; "band-desktop" is the introduction, which leaves the band for bare paper on phones.
export const pill = cva(
  "group/pill inline-flex w-fit items-center gap-3.5 rounded-full border bg-transparent pr-1.5 whitespace-nowrap text-ink transition-[border-color,background] duration-250 hover:border-field-line hover:bg-field",
  {
    variants: {
      surface: {
        paper: "border-pill-line",
        band: "border-band-line",
        "band-desktop": "border-band-line phone:border-pill-line",
      },
      size: { default: "min-h-11 pl-4.5 text-[13px]", footer: "min-h-[38px] pl-3.5 text-[11px]" },
    },
    defaultVariants: { surface: "paper", size: "default" },
  },
);

// A copied tag (data-done) turns ink, but hovering the pill still shows the hover tone.
export const pillTag = cva(
  "pill-tag inline-flex items-center justify-center gap-1.5 rounded-full px-2.25 text-[11px] text-label transition-[background,color] duration-250 group-hover/pill:bg-tag-hover group-hover/pill:text-ink data-[done]:not-group-hover/pill:bg-ink data-[done]:not-group-hover/pill:text-paper xray:text-ink-soft xray:group-hover/pill:text-ink xray:data-[done]:not-group-hover/pill:text-paper",
  {
    variants: {
      surface: { paper: "bg-sage", band: "bg-paper", "band-desktop": "bg-paper phone:bg-sage" },
      size: { default: "h-8 min-w-8", footer: "h-7 min-w-7" },
    },
    defaultVariants: { surface: "paper", size: "default" },
  },
);

export const pillIcon = "size-[15px] transition-transform duration-350 ease-out";
