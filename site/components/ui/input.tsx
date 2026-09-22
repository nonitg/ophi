import * as React from "react";
import { Input as InputPrimitive } from "@base-ui/react/input";
import { cn } from "cn";

// shadcn input, re-cut as a mark on the film: transparent, ink border, 4px corners.
function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <InputPrimitive
      type={type}
      data-slot="input"
      className={cn(
        "h-12 w-full min-w-0 rounded-[var(--radius)] border border-input bg-transparent px-3 text-base text-ink caret-ink transition-colors outline-none placeholder:text-ink-soft/75 hover:border-ink/70 focus-visible:border-ink disabled:cursor-not-allowed disabled:opacity-60 aria-invalid:border-2 aria-invalid:border-ink",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
