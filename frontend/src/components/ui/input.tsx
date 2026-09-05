import type { ComponentProps } from "react";
import { cn } from "../../lib/utils";

export function Input({ className, ...props }: ComponentProps<"input">) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-xl border border-slate-600/30 bg-slate-900/40 px-3 py-1 text-sm text-slate-100",
        "placeholder:text-slate-500",
        "transition-colors focus:border-indigo-500/60 focus:outline-none focus:ring-2 focus:ring-indigo-500/30",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "file:mr-2 file:rounded-lg file:border-0 file:bg-slate-800 file:px-3 file:py-1 file:text-xs file:font-medium file:text-slate-300 hover:file:bg-slate-700",
        className,
      )}
      {...props}
    />
  );
}
