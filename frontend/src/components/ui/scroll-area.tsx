import type { ComponentProps } from "react";
import { cn } from "../../lib/utils";

/** 带自定义细滚动条的滚动容器 */
export function ScrollArea({ className, ...props }: ComponentProps<"div">) {
  return (
    <div className={cn("custom-scrollbar overflow-auto", className)} {...props} />
  );
}
