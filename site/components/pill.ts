import { cva } from "class-variance-authority";

// Secondary actions share one shape: an outlined pill ending in a sage tag, echoing the orange join pill.
// Pass the same surface and size to the pill and its tag. Controls on the sage band take the paper tone so
// they stay distinct from it; "band-desktop" is the introduction, which leaves the band for bare paper on phones.
export const pill = cva(
  "group/pill inline-flex w-fit items-center gap-3.5 rounded-full border bg-transparent pr-1.5 whitespace-nowrap text-ink [transition:border-color_.25s,background_.25s,scale_.16s_var(--ease-out)] hover:border-field-line hover:bg-field active:scale-[.97]",
  {
    variants: {
      surface: {
        paper: "border-pill-line",
        band: "border-band-line",
        "band-desktop": "border-band-line phone:border-pill-line",
      },
      size: { default: "min-h-12 pl-5 text-[15px]", footer: "min-h-10 pl-4 text-[14px]" },
    },
    defaultVariants: { surface: "paper", size: "default" },
  },
);

// A copied tag (data-done) turns ink, but hovering the pill still shows the hover tone.
export const pillTag = cva(
  "pill-tag inline-flex items-center justify-center gap-1.5 rounded-full px-2.25 text-label transition-[background,color] duration-250 group-hover/pill:bg-tag-hover group-hover/pill:text-ink data-[done]:not-group-hover/pill:bg-ink data-[done]:not-group-hover/pill:text-paper xray:text-ink-soft xray:group-hover/pill:text-ink xray:data-[done]:not-group-hover/pill:text-paper",
  {
    variants: {
      surface: { paper: "bg-sage", band: "bg-paper", "band-desktop": "bg-paper phone:bg-sage" },
      size: { default: "h-9 min-w-9 text-[13px]", footer: "h-7 min-w-7 text-[12px]" },
    },
    defaultVariants: { surface: "paper", size: "default" },
  },
);

export const pillIcon = "size-4 transition-transform duration-200 ease-(--ease-out) motion-reduce:transition-none";

// The one orange action: asking for access. "form" sits inside the email field (call sites add their own spacing
// for tight widths); "lead" stands alone under the headline, level with the pill beside it.
export const primaryPill = cva(
  "inline-flex flex-none items-center justify-between rounded-full border-0 bg-orange font-medium text-ink [transition:background_.2s,scale_.16s_var(--ease-out)] hover:bg-[#f59973] active:scale-[.97] xray:text-paper xray:shadow-[0_0_28px_-6px_#dff3e6b3] xray:hover:bg-white",
  {
    variants: { size: { form: "h-[46px] gap-[21px] pr-4.5 pl-5 text-[14px]", lead: "h-12 gap-4 pr-4.5 pl-5.5 text-[15px]" } },
    defaultVariants: { size: "form" },
  },
);
