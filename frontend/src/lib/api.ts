import type { ChatMessage, DocumentItem, Report, ResearchTask } from "../types";

/** 后端 API 基础路径：优先取环境变量，默认 "/api"（由 Vite 代理到后端） */
const BASE_URL = (import.meta.env.VITE_API_BASE ?? "/api").replace(/\/+$/, "");

/** 携带 HTTP 状态码的 API 错误 */
export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers =
    init?.body instanceof FormData
      ? init.headers
      : { "Content-Type": "application/json", ...init?.headers };

  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers });

  if (!res.ok) {
    let message = `请求失败 (HTTP ${res.status})`;
    try {
      const data = (await res.json()) as { detail?: string; message?: string; error?: string };
      if (typeof data.detail === "string") message = data.detail;
      else if (typeof data.message === "string") message = data.message;
      else if (typeof data.error === "string") message = data.error;
    } catch {
      /* 响应体不是 JSON 时保留默认文案 */
    }
    throw new ApiError(res.status, message);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** 与后端契约一致的 API 封装 */
export const api = {
  // ── 研究任务 ──────────────────────────────────────────────
  /** 创建研究任务（后端创建后立即后台执行） */
  createResearch: (topic: string) =>
    request<ResearchTask>("/research", { method: "POST", body: JSON.stringify({ topic }) }),

  /** 任务列表 */
  listResearch: (limit = 50, offset = 0) =>
    request<ResearchTask[]>(`/research?limit=${limit}&offset=${offset}`),

  /** 任务详情 */
  getResearch: (id: string) => request<ResearchTask>(`/research/${encodeURIComponent(id)}`),

  /** 任务报告 */
  getReport: (taskId: string) => request<Report>(`/research/${encodeURIComponent(taskId)}/report`),

  /** 删除任务 */
  deleteResearch: (id: string) =>
    request<{ ok: true }>(`/research/${encodeURIComponent(id)}`, { method: "DELETE" }),

  // ── 知识库 ────────────────────────────────────────────────
  /** 上传文档（multipart，字段名 file） */
  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentItem>("/knowledge/documents", { method: "POST", body: form });
  },

  /** URL 入库 */
  ingestUrl: (url: string) =>
    request<DocumentItem>("/knowledge/ingest-url", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),

  /** 文档列表 */
  listDocuments: () => request<DocumentItem[]>("/knowledge/documents"),

  /** 删除文档 */
  deleteDocument: (id: string) =>
    request<{ ok: true }>(`/knowledge/documents/${encodeURIComponent(id)}`, { method: "DELETE" }),

  /** 知识库问答（首次问答时由后端创建会话并返回 session_id） */
  chatKnowledge: (body: { session_id?: string; question: string; document_id?: string }) =>
    request<{
      session_id: string;
      answer: string;
      citations: ChatMessage["citations"];
    }>("/knowledge/chat", { method: "POST", body: JSON.stringify(body) }),

  /** 会话历史 */
  getChatHistory: (sessionId: string) =>
    request<ChatMessage[]>(`/knowledge/chat/history?session_id=${encodeURIComponent(sessionId)}`),
};
