import { useResearchStore } from "../stores/researchStore";

/**
 * 研究任务相关 API 调用的统一封装。
 * 内部全部委托给 researchStore，页面组件只需关注业务逻辑。
 */
export function useResearch() {
  const fetchTasks = useResearchStore((s) => s.fetchTasks);
  const fetchTask = useResearchStore((s) => s.fetchTask);
  const createResearch = useResearchStore((s) => s.createResearch);
  const deleteResearch = useResearchStore((s) => s.deleteResearch);
  const fetchReport = useResearchStore((s) => s.fetchReport);

  return { fetchTasks, fetchTask, createResearch, deleteResearch, fetchReport };
}
