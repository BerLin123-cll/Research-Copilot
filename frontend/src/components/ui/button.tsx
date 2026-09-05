import type { ComponentProps } from "react";
import { cn } from "../../lib/utils";
import { Spinner } from "./spinner";

type ButtonVariant = "default" | "secondary" | "outline" | "ghost" | "destructive";
type ButtonSize = "default" | "sm" | "lg" | "icon";

const variantClasses: Record<ButtonVariant, string> = {
  default:
    "bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-lg shadow-indigo-500/25 hover:from-indigo-600 hover:to-violet-600",
  secondary: "bg-slate-800/60 text-slate-100 hover:bg-slate-700/60 border border-white/5",
  outline: "border border-slate-600/40 bg-slate-900/40 text-slate-200 hover:bg-slate-800/60",
  ghost: "text-slate-300 hover:bg-white/5 hover:text-slate-100",
  destructive:
    "bg-gradient-to-r from-rose-500 to-red-500 text-white shadow-lg shadow-rose-500/20 hover:from-rose-600 hover:to-red-600",
};

const sizeClasses: Record<ButtonSize, string> = {
  default: "h-9 px-4 py-2 text-sm",
  sm: "h-8 px-3 text-xs",
  lg: "h-11 px-6 text-base",
  icon: "h-9 w-9",
};

export interface ButtonProps extends ComponentProps<"button"> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

export function Button({
  variant = "default",
  size = "default",
  loading = false,
  disabled,
  className,
  children,
  ...props
}: ButtonProps) {
  // 合并外部 disabled 与 loading，避免被 {...props} 覆盖
  const finalDisabled = disabled || loading;
  return (
    <button
      type="button"
      disabled={finalDisabled}
      className={cn(
        "inline-flex shrink-0 items-center justify-center gap-2 rounded-xl font-medium transition-all",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/60 focus-visible:ring-offset-1",
        "disabled:pointer-events-none disabled:opacity-50",
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    >
      {loading && <Spinner className="size-4" />}
      {children}
    </button>
  );
}
