import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { Input } from "../ui/input";
import { useResearchStore } from "../../stores/researchStore";

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
      setError("创建研究任务失败，请确认后端服务已启动（http://localhost:8000）。");
    }
  };

  return (
    <Card className="p-5">
      <form onSubmit={(e) => void submit(e)} className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="输入研究主题，例如：大语言模型检索增强生成（RAG）的最新进展"
          disabled={submitting}
          className="flex-1"
        />
        <Button type="submit" loading={submitting} disabled={!topic.trim()}>
          🔬 开始研究
        </Button>
      </form>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </Card>
  );
}
