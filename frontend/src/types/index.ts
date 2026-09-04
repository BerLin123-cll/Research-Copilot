/** 研究任务 */
export interface ResearchTask {
  id: string;
  topic: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  plan: string[];
  current_step: number;
  search_queries: string[];
  sources: { title: string; url: string; published?: string | null }[];
  error: string | null;
  report_id: string | null;
  created_at: string | null;
  updated_at: string | null;
}

/** 研究报告 */
export interface Report {
  id: string;
  task_id: string;
  title: string;
  content: string;
  summary: string | null;
  created_at: string | null;
}

/** 知识库文档 */
export interface DocumentItem {
  id: string;
  filename: string;
  source_type: string;
  url: string | null;
  status: string;
  chunk_count: number;
  meta: Record<string, unknown>;
  error: string | null;
  created_at: string | null;
}

/** 知识库问答消息 */
export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  citations: {
    index: number;
    document_id: string;
    filename: string;
    snippet: string;
    score: number;
  }[];
  created_at: string | null;
}

/** Agent 实时事件流 */
export type AgentEvent =
  | { type: "snapshot"; task: ResearchTask }
  | { type: "status"; status: string; message: string }
  | { type: "plan"; steps: string[] }
  | { type: "node_start" | "node_end"; node: string; timestamp: string }
  | { type: "tool_call"; tool: string; input: Record<string, unknown>; timestamp: string }
  | { type: "tool_result"; tool: string; output: Record<string, unknown>; success: boolean; timestamp: string }
  | { type: "analysis"; information_sufficient: boolean; synthesized_info: string }
  | { type: "rejection"; reason: string }
  | { type: "report_ready"; report_id: string }
  | { type: "error"; message: string }
  | { type: "cancelled"; task_id: string }
  | { type: "done"; task_id: string };
