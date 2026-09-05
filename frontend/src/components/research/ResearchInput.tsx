import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Sparkles } from "lucide-react";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { Input } from "../ui/input";
import { useResearchStore } from "../../stores/researchStore";
import { cn } from "../../lib/utils";

/** 研究主题输入 + 开始研究按钮（含 loading 状态），创建成功后跳转详情页 */
export function ResearchInput() {
  const [topic, setTopic] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const createResearch = useResearchStore((s) => s.createResearch);
  const navigate = useNavigate();

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const t = topic.trim();
    if (!t || submitting) return;
    setSubmitting(true);
    setError(null);
    const task = await createResearch(t);
    setSubmitting(false);
    if (task) {
      setTopic("");
      navigate(`/research/${task.id}`);
    } else {
      setError("创建研究任务失败，请确认后端服务已启动（http://localhost:8000）");
    }
  };

  return (
    <Card className="relative overflow-hidden p-1">
      <div
        className={cn(
          "pointer-events-none absolute inset-0 opacity-30",
          "bg-gradient-to-r from-indigo-500/10 via-violet-500/10 to-cyan-500/10",
        )}
      />
      <form onSubmit={(e) => void submit(e)} className="relative flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <Input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="输入研究主题，例如：大语言模型检索增强生成（RAG）的最新进展"
            disabled={submitting}
            className="pl-9"
          />
        </div>
        <Button type="submit" loading={submitting} disabled={!topic.trim()} className="shrink-0">
          <Sparkles className="h-4 w-4" />
          开始研究
        </Button>
      </form>
      {error && <p className="relative px-4 pb-4 text-sm text-rose-400">{error}</p>}
    </Card>
  );
}
