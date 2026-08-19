import { useState } from "react";
import type { AgentEvent } from "../../types";
import { cn, truncate } from "../../lib/utils";

type ToolCallEvent = Extract<AgentEvent, { type: "tool_call" }>;
type ToolResultEvent = Extract<AgentEvent, { type: "tool_result" }>;

export interface ToolCallCardProps {
  call: ToolCallEvent;
  result: ToolResultEvent | null;
  index: number;
}

/**
 * 工具调用记录卡片：
 * - 工具名徽章 + 输入 JSON 摘要（可点击展开完整输入/输出）
 * - 状态色：成功绿 / 失败红 / 执行中灰
 */
export function ToolCallCard({ call, result, index }: ToolCallCardProps) {
  const [expanded, setExpanded] = useState(false);

  const status: "pending" | "success" | "failed" = result
    ? result.success
      ? "success"
      : "failed"
    : "pending";

  const statusText = status === "pending" ? "执行中" : status === "success" ? "成功" : "失败";
  const statusTextClass =
    status === "pending"
      ? "text-slate-500"
      : status === "success"
        ? "text-emerald-600"
        : "text-red-600";
  const cardClass =
    status === "pending"
      ? "border-slate-200 bg-slate-50"
      : status === "success"
        ? "border-emerald-200 bg-emerald-50/60"
        : "border-red-200 bg-red-50/60";

  const inputSummary = truncate(JSON.stringify(call.input ?? {}), 140);

  return (
    <div className={cn("rounded-lg border px-3 py-2.5", cardClass)}>
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center gap-2 text-left"
      >
        <span className="inline-flex shrink-0 items-center gap-1 rounded-md border border-slate-200 bg-white px-1.5 py-0.5 font-mono text-xs font-medium text-slate-700">
          🛠 {call.tool}
        </span>
        <span className="min-w-0 flex-1 truncate font-mono text-xs text-slate-500">
          <span className="mr-1 text-slate-400">#{index}</span>
          {inputSummary}
        </span>
        <span className={cn("shrink-0 text-xs font-medium", statusTextClass)}>
          {status === "pending" ? (
            <span className="inline-flex items-center gap-1">
              <span className="size-1.5 animate-pulse rounded-full bg-slate-400" />
              {statusText}
            </span>
          ) : (
            statusText
          )}
        </span>
        <span className="shrink-0 text-xs text-slate-400">{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div className="custom-scrollbar mt-2 space-y-2 border-t border-slate-200/70 pt-2">
          <div>
            <p className="mb-1 text-xs font-medium text-slate-500">输入</p>
            <pre className="custom-scrollbar max-h-52 overflow-auto rounded-md bg-slate-900 p-2 font-mono text-xs leading-relaxed text-slate-100">
              {JSON.stringify(call.input ?? {}, null, 2)}
            </pre>
          </div>
          <div>
            <p className="mb-1 text-xs font-medium text-slate-500">
              输出{" "}
              {result && (
                <span className={result.success ? "text-emerald-500" : "text-red-500"}>
                  （{result.success ? "成功" : "失败"}）
                </span>
              )}
            </p>
            {result ? (
              <pre className="custom-scrollbar max-h-52 overflow-auto rounded-md bg-slate-900 p-2 font-mono text-xs leading-relaxed text-slate-100">
                {JSON.stringify(result.output ?? {}, null, 2)}
              </pre>
            ) : (
              <p className="text-xs text-slate-400">等待工具返回…</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
