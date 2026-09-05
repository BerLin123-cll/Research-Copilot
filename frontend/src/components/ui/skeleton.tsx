import type { ComponentProps } from "react";
import { cn } from "../../lib/utils";

/** 加载占位骨架 */
export function Skeleton({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("animate-pulse rounded-md bg-slate-700/50", className)} {...props} />;
}
