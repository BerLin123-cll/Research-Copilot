import type { ComponentProps } from "react";
import { cn } from "../../lib/utils";

export type StatusTone = "neutral" | "info" | "success" | "danger" | "warning";
export type BadgeVariant = "default" | "secondary" | "outline" | StatusTone;

const badgeVariants: Record<BadgeVariant, string> = {
  default: "border-indigo-400/20 bg-indigo-500/15 text-indigo-300",
  secondary: "border-slate-600/20 bg-slate-700/30 text-slate-300",
  outline: "border-slate-600/30 bg-transparent text-slate-400",
  neutral: "border-slate-600/20 bg-slate-700/30 text-slate-300",
  info: "border-sky-400/20 bg-sky-500/15 text-sky-300",
  success: "border-emerald-400/20 bg-emerald-500/15 text-emerald-300",
  danger: "border-rose-400/20 bg-rose-500/15 text-rose-300",
  warning: "border-amber-400/20 bg-amber-500/15 text-amber-300",
};

export interface BadgeProps extends ComponentProps<"span"> {
  variant?: BadgeVariant;
}

export function Badge({ variant = "secondary", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium",
        badgeVariants[variant],
        className,
      )}
      {...props}
    />
  );
}
