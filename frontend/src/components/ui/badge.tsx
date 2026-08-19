import type { ComponentProps } from "react";
import { cn } from "../../lib/utils";

export type StatusTone = "neutral" | "info" | "success" | "danger" | "warning";
export type BadgeVariant = "default" | "secondary" | "outline" | StatusTone;

const badgeVariants: Record<BadgeVariant, string> = {
  default: "border-blue-200 bg-blue-50 text-blue-700",
  secondary: "border-slate-200 bg-slate-100 text-slate-600",
  outline: "border-slate-300 bg-white text-slate-600",
  neutral: "border-slate-200 bg-slate-100 text-slate-600",
  info: "border-blue-200 bg-blue-50 text-blue-700",
  success: "border-emerald-200 bg-emerald-50 text-emerald-700",
  danger: "border-red-200 bg-red-50 text-red-700",
  warning: "border-amber-200 bg-amber-50 text-amber-700",
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
