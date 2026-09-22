import * as React from "react";
import { cn } from "cn";
import { ChevronDownIcon } from "lucide-react";

type NativeSelectProps = React.ComponentProps<"select">;

// shadcn native-select, re-cut to match the film input: same height, border and corners.
function NativeSelect({ className, ...props }: NativeSelectProps) {
  return (
    <div
      className={cn("relative w-fit has-[select:disabled]:opacity-60", className)}
      data-slot="native-select-wrapper"
    >
      <select
        data-slot="native-select"
        className="h-12 w-full min-w-0 appearance-none rounded-[var(--radius)] border border-input bg-transparent py-1 pr-10 pl-3 text-base text-ink transition-colors outline-none select-none hover:border-ink/70 focus-visible:border-ink disabled:pointer-events-none disabled:cursor-not-allowed aria-invalid:border-2 aria-invalid:border-ink"
        {...props}
      />
      <ChevronDownIcon
        className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-ink-soft select-none"
        aria-hidden="true"
        data-slot="native-select-icon"
      />
    </div>
  );
}

function NativeSelectOption({ className, ...props }: React.ComponentProps<"option">) {
  return (
    <option
      data-slot="native-select-option"
      className={cn("bg-[Canvas] text-[CanvasText]", className)}
      {...props}
    />
  );
}

export { NativeSelect, NativeSelectOption };
