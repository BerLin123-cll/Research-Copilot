import type { ComponentProps } from "react";
import { cn } from "../../lib/utils";

export function Input({ className, ...props }: ComponentProps<"input">) {
  return (
    <input
      className={cn(
        "h-9 w-full rounded-lg border border-slate-300 bg-white px-3 py-1 text-sm text-slate-900",
        "placeholder:text-slate-400",
        "transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/60",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}
