import { Fragment, useMemo, type ReactNode } from "react";
import type { AgentEvent } from "../../types";
import { useResearchStore } from "../../stores/researchStore";
import { ToolCallCard } from "./ToolCallCard";
import { Badge } from "../ui/badge";
import { Card } from "../ui/card";
import { Separator } from "../ui/separator";
import { Skeleton } from "../ui/skeleton";
import { cn, formatDateTime, taskStatusMeta } from "../../lib/utils";

/** 节点名 → 展示文案（支持中英文节点名） */
const NODE_META: Record<string, { label: string; icon: string }> = {
  planner: { label: "规划 (Planner)", icon: "🧭" },
  searcher: { label: "搜索 (Searcher)", icon: "🔎" },
  analyzer: { label: "分析 (Analyzer)", icon: "🧠" },
  reporter: { label: "报告 (Reporter)", icon: "📝" },
};

function nodeMeta(node: string): { label: string; icon: string } {
  const key = Object.keys(NODE_META).find((k) => node.toLowerCase().includes(k));
  return key ? NODE_META[key] : { label: node, icon: "🔧" };
}

type ToolCallEvent = Extract<AgentEvent, { type: "tool_call" }>;
type ToolResultEvent = Extract<AgentEvent, { type: "tool_result" }>;
type AnalysisEvent = Extract<AgentEvent, { type: "analysis" }>;
type RejectionEvent = Extract<AgentEvent, { type: "rejection" }>;

type Block =
  | { kind: "node_start"; node: string; timestamp: string }
  | { kind: "node_end"; node: string; timestamp: string }
  | { kind: "plan"; steps: string[] }
  | { kind: "status"; message: string }
  | { kind: "tool_call"; call: ToolCallEvent; result: ToolResultEvent | null }
  | { kind: "analysis"; info: AnalysisEvent }
  | { kind: "rejection"; info: RejectionEvent }
  | { kind: "report_ready"; reportId: string }
  | { kind: "error"; message: string }
  | { kind: "cancelled"; taskId: string }
  | { kind: "done"; taskId: string };

/** 将原始事件流整理为有序 Block 列表；tool_result 就近合并进同名 tool_call */
function buildBlocks(events: AgentEvent[]): Block[] {
  const blocks: Block[] = [];
  const toolIndex: Record<string, number> = {};

  for (const ev of events) {
    switch (ev.type) {
      case "node_start":
        blocks.push({ kind: "node_start", node: ev.node, timestamp: ev.timestamp });
        break;
      case "node_end":
        blocks.push({ kind: "node_end", node: ev.node, timestamp: ev.timestamp });
        break;
      case "plan":
        blocks.push({ kind: "plan", steps: ev.steps });
        break;
      case "status":
        blocks.push({ kind: "status", message: ev.message });
        break;
      case "tool_call": {
        const idx = blocks.length;
        blocks.push({ kind: "tool_call", call: ev, result: null });
        toolIndex[ev.tool] = idx;
        break;
      }
      case "tool_result": {
        const idx = toolIndex[ev.tool];
        if (idx !== undefined) {
          const prev = blocks[idx];
          if (prev.kind === "tool_call" && prev.call.tool === ev.tool && prev.result === null) {
            blocks[idx] = { ...prev, result: ev };
          }
        }
        break;
      }
      case "analysis":
        blocks.push({ kind: "analysis", info: ev });
        break;
      case "rejection":
        blocks.push({ kind: "rejection", info: ev });
        break;
      case "report_ready":
        blocks.push({ kind: "report_ready", reportId: ev.report_id });
        break;
      case "error":
        blocks.push({ kind: "error", message: ev.message });
        break;
      case "cancelled":
        blocks.push({ kind: "cancelled", taskId: ev.task_id });
        break;
      case "done":
        blocks.push({ kind: "done", taskId: ev.task_id });
        break;
      case "snapshot":
        break;
    }
  }
  return blocks;
}

interface Section {
  header: { label: string; icon: string; timestamp: string };
  items: Block[];
}

/** 按 node_start / node_end 把 Block 分组为节点区块；节点外的 Block 归入全局区 */
function buildSections(blocks: Block[]): { globalItems: Block[]; sections: Section[] } {
  const globalItems: Block[] = [];
  const sections: Section[] = [];
  let cur: Section | null = null;

  for (const b of blocks) {
    if (b.kind === "node_start") {
      const meta = nodeMeta(b.node);
      cur = { header: { label: meta.label, icon: meta.icon, timestamp: b.timestamp }, items: [] };
      sections.push(cur);
    } else if (b.kind === "node_end") {
      cur?.items.push(b);
    } else if (cur) {
      cur.items.push(b);
    } else {
      globalItems.push(b);
    }
  }
  return { globalItems, sections };
}

function renderBlock(b: Block): ReactNode {
  switch (b.kind) {
    case "node_start":
      return null;
    case "node_end":
      return (
        <p className="text-xs text-slate-400">
          ———— {nodeMeta(b.node).label} 结束
        </p>
      );
    case "plan":
      return (
        <div className="rounded-lg border border-blue-200 bg-blue-50/60 p-3">
          <p className="mb-1.5 text-xs font-medium text-blue-700">📋 研究计划</p>
          <ol className="space-y-1">
            {b.steps.map((s, si) => (
              <li key={si} className="flex gap-2 text-sm text-slate-700">
                <span className="shrink-0 font-medium text-blue-600">{si + 1}.</span>
                <span>{s}</span>
              </li>
            ))}
          </ol>
        </div>
      );
    case "status":
      return (
        <p className="text-xs text-slate-500">
          💬 {b.message}
        </p>
      );
    case "tool_call":
      return <ToolCallCard call={b.call} result={b.result} index={0} />;
    case "analysis":
      return (
        <div className="rounded-lg border border-violet-200 bg-violet-50/60 p-3">
          <p className="mb-1 text-xs font-medium text-violet-700">
            🧠 综合分析{" "}
            {b.info.information_sufficient
              ? "（信息已充分 ✅）"
              : "（信息不足，继续补充搜索 🔄）"}
          </p>
          <p className="whitespace-pre-wrap text-sm text-slate-700">{b.info.synthesized_info}</p>
        </div>
      );
    case "rejection":
      return (
        <div className="rounded-lg border border-amber-200 bg-amber-50/70 p-3">
          <p className="mb-1 text-xs font-medium text-amber-700">🚫 不适合深度研究</p>
          <p className="text-sm text-slate-700">{b.info.reason}</p>
          <p className="mt-1 text-xs text-slate-500">已跳过搜索流程，生成说明性结果。</p>
        </div>
      );
    case "report_ready":
      return (
        <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          📄 报告已生成（report_id: {b.reportId}）
        </p>
      );
    case "error":
      return (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          ❌ {b.message}
        </p>
      );
    case "cancelled":
      return (
        <p className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-600">
          ⏹️ 任务已被取消
        </p>
      );
    case "done":
      return (
        <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          🏁 研究任务已完成
        </p>
      );
    default:
      return null;
  }
}

/** 渲染一组 Block；为工具调用维护全局递增序号 */
function renderItems(items: Block[], prefix: string): ReactNode {
  let toolSeq = 0;
  return items.map((b, i) => {
    let node: ReactNode;
    if (b.kind === "tool_call") {
      toolSeq += 1;
      node = <ToolCallCard call={b.call} result={b.result} index={toolSeq} />;
    } else {
      node = renderBlock(b);
    }
    return <Fragment key={`${prefix}-${i}`}>{node}</Fragment>;
  });
}

/** Agent 执行时间线：状态徽章 + 按节点分组的事件流 */
export function ResearchTimeline() {
  const currentTask = useResearchStore((s) => s.currentTask);
  const events = useResearchStore((s) => s.events);
  const wsConnected = useResearchStore((s) => s.wsConnected);

  const blocks = useMemo(() => buildBlocks(events), [events]);
  const { globalItems, sections } = useMemo(() => buildSections(blocks), [blocks]);
  const globalPlan = useMemo(
    () => blocks.find((b) => b.kind === "plan")?.steps ?? null,
    [blocks],
  );

  if (!currentTask) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-36 w-full" />
        <Skeleton className="h-36 w-full" />
      </div>
    );
  }

  const statusMeta = taskStatusMeta[currentTask.status];
  const isEmpty = events.length === 0;

  return (
    <div className="space-y-4">
      {/* 状态头 */}
      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant={statusMeta.tone} className="text-sm">
            <span>{statusMeta.icon}</span>
            {statusMeta.label}
          </Badge>
          <span className="text-xs text-slate-400">
            更新于 {formatDateTime(currentTask.updated_at ?? currentTask.created_at)}
          </span>
          <span className="ml-auto inline-flex items-center gap-1.5 text-xs text-slate-500">
            <span
              className={cn(
                "size-2 rounded-full",
                wsConnected ? "bg-emerald-500" : "bg-slate-300",
              )}
            />
            {wsConnected ? "实时连接中" : "未连接（自动重连中）"}
          </span>
        </div>
        {currentTask.error && (
          <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            ❌ {currentTask.error}
          </p>
        )}
      </Card>

      {/* 空态 */}
      {isEmpty && (
        <div className="space-y-3">
          <Card className="p-6 text-center text-sm text-slate-400">
            {currentTask.status === "pending"
              ? "任务已创建，等待 Agent 开始执行…"
              : "等待 Agent 输出事件…"}
          </Card>
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      )}

      {/* 全局计划 */}
      {!isEmpty && globalPlan && (
        <Card className="p-4">
          <h3 className="mb-3 text-sm font-semibold text-slate-700">📋 研究计划</h3>
          <ol className="space-y-2">
            {globalPlan.map((step, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700">
                  {i + 1}
                </span>
                <span className="text-slate-700">{step}</span>
              </li>
            ))}
          </ol>
        </Card>
      )}

      {/* 节点外的全局事件（计划已在顶部卡片展示，这里跳过 plan） */}
      {!isEmpty && globalItems.length > 0 && (
        <div className="space-y-2">
          {renderItems(globalItems.filter((b) => b.kind !== "plan"), "g")}
        </div>
      )}

      {/* 按节点分组的时间线 */}
      {!isEmpty && (
        <div className="space-y-6">
          {sections.map((sec, si) => (
            <section key={`s-${si}`}>
              <div className="mb-2 flex items-center gap-2">
                <span className="text-base">{sec.header.icon}</span>
                <h3 className="text-sm font-semibold text-slate-800">{sec.header.label}</h3>
                <span className="text-xs text-slate-400">{formatDateTime(sec.header.timestamp)}</span>
                <Separator className="ml-2 flex-1" />
              </div>
              <div className="space-y-2 border-l-2 border-slate-200 pl-4">
                {renderItems(sec.items, `i-${si}`)}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
