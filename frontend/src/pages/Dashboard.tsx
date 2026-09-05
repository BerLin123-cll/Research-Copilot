import { useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, CircleDashed, Clock, XCircle } from "lucide-react";
import { ResearchInput } from "../components/research/ResearchInput";
import { Badge } from "../components/ui/badge";
import { Card } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { useResearch } from "../hooks/useResearch";
import { useResearchStore } from "../stores/researchStore";
import { formatDateTime, taskStatusMeta } from "../lib/utils";

/** 主控制台：研究输入 + 数据指标 + 任务列表 */
export function Dashboard() {
  const navigate = useNavigate();
  const { fetchTasks } = useResearch();
  const tasks = useResearchStore((s) => s.tasks);
  const tasksLoading = useResearchStore((s) => s.tasksLoading);

  useEffect(() => {
    void fetchTasks();
  }, [fetchTasks]);

  const stats = useMemo(() => {
    const total = tasks.length;
    const running = tasks.filter((t) => t.status === "pending" || t.status === "running").length;
    const completed = tasks.filter((t) => t.status === "completed").length;
    const failed = tasks.filter((t) => t.status === "failed" || t.status === "cancelled").length;
    return [
      {
        label: "全部任务",
        value: total,
        icon: CircleDashed,
        bg: "bg-indigo-500/15 text-indigo-300 ring-1 ring-inset ring-indigo-500/20",
      },
      {
        label: "进行中",
        value: running,
        icon: Clock,
        bg: "bg-sky-500/15 text-sky-300 ring-1 ring-inset ring-sky-500/20",
      },
      {
        label: "已完成",
        value: completed,
        icon: CheckCircle2,
        bg: "bg-emerald-500/15 text-emerald-300 ring-1 ring-inset ring-emerald-500/20",
      },
      {
        label: "异常/取消",
        value: failed,
        icon: XCircle,
        bg: "bg-rose-500/15 text-rose-300 ring-1 ring-inset ring-rose-500/20",
      },
    ];
  }, [tasks]);

  return (
    <div className="space-y-6">
      <section>
        <h1 className="mb-4 text-2xl font-bold tracking-tight text-slate-100">开始新的研究</h1>
        <ResearchInput />
      </section>

      {/* 数据指标 */}
      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {stats.map((s) => {
          const Icon = s.icon;
          return (
            <Card key={s.label} className="p-4">
              <div className="flex items-center gap-3">
                <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${s.bg}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold leading-none text-slate-100">{s.value}</p>
                  <p className="mt-1 text-xs text-slate-400">{s.label}</p>
                </div>
              </div>
            </Card>
          );
        })}
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-100">研究任务</h2>
          <span className="text-sm text-slate-400">共 {tasks.length} 个</span>
        </div>

        {tasksLoading && tasks.length === 0 ? (
          <div className="space-y-3">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : tasks.length === 0 ? (
          <Card className="p-10 text-center text-sm text-slate-400">
            暂无研究任务，输入一个主题开始你的第一次研究吧
          </Card>
        ) : (
          <div className="space-y-3">
            {tasks.map((t) => {
              const meta = taskStatusMeta[t.status];
              const Icon = meta.Icon;
              const planCount = t.plan?.length ?? 0;
              return (
                <Card
                  key={t.id}
                  onClick={() => navigate(`/research/${t.id}`)}
                  className="cursor-pointer p-4 transition-shadow hover:shadow-lg hover:ring-1 hover:ring-indigo-500/20"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <p className="truncate font-medium text-slate-100" title={t.topic}>
                        {t.topic}
                      </p>
                      <p className="mt-1 text-xs text-slate-400">
                        创建于 {formatDateTime(t.created_at)}
                        {t.sources && t.sources.length > 0 && ` · 已引用 ${t.sources.length} 个来源`}
                        {planCount > 0 && ` · 计划 ${t.current_step}/${planCount} 步`}
                      </p>
                    </div>
                    <Badge variant={meta.tone}>
                      <Icon className="h-3.5 w-3.5" />
                      {meta.label}
                    </Badge>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
