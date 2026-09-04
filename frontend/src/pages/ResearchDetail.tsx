import { Suspense, lazy, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ResearchTimeline } from "../components/research/ResearchTimeline";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { useResearch } from "../hooks/useResearch";
import { useResearchStore } from "../stores/researchStore";
import { useWebSocket } from "../hooks/useWebSocket";
import type { Report } from "../types";
import { cn, formatDateTime, taskStatusMeta } from "../lib/utils";

// 报告查看器懒加载
const ReportViewer = lazy(() =>
  import("../components/research/ReportViewer").then((m) => ({ default: m.ReportViewer })),
);

/** 研究详情页：实时时间线 + 报告查看（Tab 切换，报告懒加载） */
export function ResearchDetail() {
  const { id } = useParams<{ id: string }>();
  const taskId = id ?? "";

  const { fetchTask, fetchReport, cancelResearch } = useResearch();
  const currentTask = useResearchStore((s) => s.currentTask);
  const events = useResearchStore((s) => s.events);
  const wsConnected = useWebSocket(taskId);

  const [tab, setTab] = useState("timeline");
  const [report, setReport] = useState<Report | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  // 进入页面：连接 WS（useWebSocket 负责）并加载任务
  useEffect(() => {
    if (!taskId) return;
    setReport(null);
    setReportLoading(false);
    void fetchTask(taskId);
  }, [taskId, fetchTask]);

  // 切换到「报告」Tab 且任务已有 report_id 时，懒加载报告
  const reportId = currentTask?.report_id;
  useEffect(() => {
    if (tab !== "report" || report || reportLoading || !reportId) return;
    setReportLoading(true);
    void fetchReport(taskId)
      .then((r) => {
        if (r) setReport(r);
      })
      .finally(() => setReportLoading(false));
  }, [tab, report, reportLoading, reportId, taskId, fetchReport]);

  if (!currentTask) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    );
  }

  const meta = taskStatusMeta[currentTask.status];
  const canCancel = currentTask.status === "pending" || currentTask.status === "running";
  const rejection = [...events].reverse().find((e) => e.type === "rejection");

  const handleCancel = async () => {
    if (!canCancel || cancelling) return;
    setCancelling(true);
    await cancelResearch(currentTask.id);
    // 取消请求已发出；状态变更由 cancelled 事件/轮询刷新，稍后兜底刷新一次
    window.setTimeout(() => void fetchTask(currentTask.id), 1500);
    setCancelling(false);
  };

  return (
    <div className="space-y-5">
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-slate-400 transition-colors hover:text-slate-600">
        ← 返回研究台
      </Link>

      {/* 任务头 */}
      <Card className="p-5">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="min-w-0 flex-1 break-all text-lg font-bold text-slate-900">
            {currentTask.topic}
          </h1>
          <Badge variant={meta.tone} className="text-sm">
            <span>{meta.icon}</span>
            {meta.label}
          </Badge>
          {canCancel && (
            <Button
              variant="outline"
              size="sm"
              loading={cancelling}
              disabled={cancelling}
              onClick={() => void handleCancel()}
              className="text-slate-600 hover:text-red-600"
            >
              ⏹️ 取消任务
            </Button>
          )}
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
          <span>
            任务 ID：
            <code className="rounded bg-slate-100 px-1 py-0.5 font-mono">{currentTask.id}</code>
          </span>
          <span>创建于 {formatDateTime(currentTask.created_at)}</span>
          <span>更新于 {formatDateTime(currentTask.updated_at)}</span>
          <span
            className={cn(
              "inline-flex items-center gap-1.5",
              wsConnected ? "text-emerald-600" : "text-slate-400",
            )}
          >
            <span className={cn("size-2 rounded-full", wsConnected ? "bg-emerald-500" : "bg-slate-300")} />
            {wsConnected ? "实时连接" : "未连接"}
          </span>
        </div>
        {rejection && (
          <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
            🚫 该输入不适合作为深度研究主题：{rejection.reason}
          </p>
        )}
        {currentTask.error && (
          <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            ❌ {currentTask.error}
          </p>
        )}
      </Card>

      {/* Tab：时间线 / 报告 */}
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="timeline">🕐 执行时间线</TabsTrigger>
          <TabsTrigger value="report">📄 研究报告</TabsTrigger>
        </TabsList>
        <TabsContent value="timeline">
          <ResearchTimeline />
        </TabsContent>
        <TabsContent value="report">
          <Suspense
            fallback={
              <div className="space-y-3">
                <Skeleton className="h-10 w-1/3" />
                <Skeleton className="h-64 w-full" />
              </div>
            }
          >
            <ReportViewer report={report} loading={reportLoading} />
          </Suspense>
        </TabsContent>
      </Tabs>
    </div>
  );
}
