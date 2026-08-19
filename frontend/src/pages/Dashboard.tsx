import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ResearchInput } from "../components/research/ResearchInput";
import { Badge } from "../components/ui/badge";
import { Card } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { useResearch } from "../hooks/useResearch";
import { useResearchStore } from "../stores/researchStore";
import { formatDateTime, taskStatusMeta } from "../lib/utils";

/** 主控制台：研究输入 + 任务列表（点击进入详情） */
export function Dashboard() {
  const navigate = useNavigate();
  const { fetchTasks } = useResearch();
  const tasks = useResearchStore((s) => s.tasks);
  const tasksLoading = useResearchStore((s) => s.tasksLoading);

  useEffect(() => {
    void fetchTasks();
  }, [fetchTasks]);

  return (
    <div className="space-y-8">
      <section>
        <h1 className="mb-3 text-xl font-bold text-slate-900">开始新的研究</h1>
        <ResearchInput />
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">研究任务</h2>
          <span className="text-sm text-slate-400">共 {tasks.length} 个</span>
        </div>

        {tasksLoading && tasks.length === 0 ? (
          <div className="space-y-3">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : tasks.length === 0 ? (
          <Card className="p-10 text-center text-sm text-slate-400">
            暂无研究任务，输入一个主题开始你的第一次研究吧 🚀
          </Card>
        ) : (
          <div className="space-y-3">
            {tasks.map((t) => {
              const meta = taskStatusMeta[t.status];
              const planCount = t.plan?.length ?? 0;
              return (
                <Card
                  key={t.id}
                  onClick={() => navigate(`/research/${t.id}`)}
                  className="cursor-pointer p-4 transition-shadow hover:shadow-md"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <p className="truncate font-medium text-slate-900" title={t.topic}>
                        {t.topic}
                      </p>
                      <p className="mt-1 text-xs text-slate-400">
                        创建于 {formatDateTime(t.created_at)}
                        {t.sources && t.sources.length > 0 && ` · 已引用 ${t.sources.length} 个来源`}
                        {planCount > 0 && ` · 计划 ${t.current_step}/${planCount} 步`}
                      </p>
                    </div>
                    <Badge variant={meta.tone}>
                      <span>{meta.icon}</span>
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
