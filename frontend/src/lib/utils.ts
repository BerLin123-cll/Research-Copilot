import type { ResearchTask } from "../types";
import type { StatusTone } from "../components/ui/badge";

/** 合并多个 class 名称，过滤 falsy 值 */
export function cn(...parts: Array<string | null | false | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

/** 将 ISO 时间格式化为 "YYYY-MM-DD HH:mm"，非法/空值返回占位符 */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return String(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** 截断长文本并追加省略号 */
export function truncate(text: string, max: number): string {
  const t = text ?? "";
  return t.length > max ? `${t.slice(0, max)}…` : t;
}

/** 字节数格式化为可读文本 */
export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** 研究任务状态 → 文案/色板/图标 */
export const taskStatusMeta: Record<
  ResearchTask["status"],
  { label: string; tone: StatusTone; icon: string }
> = {
  pending: { label: "等待中", tone: "neutral", icon: "🕐" },
  running: { label: "进行中", tone: "info", icon: "⏳" },
  completed: { label: "已完成", tone: "success", icon: "✅" },
  failed: { label: "失败", tone: "danger", icon: "❌" },
  cancelled: { label: "已取消", tone: "neutral", icon: "⏹️" },
};

/** 文档状态（后端字符串）→ 文案/色板 */
export function documentStatusMeta(status: string): { label: string; tone: StatusTone } {
  const s = (status ?? "").toLowerCase();
  if (s === "completed" || s === "ready") return { label: "已就绪", tone: "success" };
  if (s === "processing" || s === "ingesting" || s === "pending" || s === "queued") {
    return { label: "处理中", tone: "info" };
  }
  if (s === "failed" || s === "error") return { label: "失败", tone: "danger" };
  return { label: status || "未知", tone: "neutral" };
}

/** 文档来源类型 → 展示文案 */
export function sourceTypeLabel(sourceType: string): string {
  const t = (sourceType ?? "").toLowerCase();
  if (t.includes("url") || t.includes("web")) return "URL";
  if (t.includes("pdf")) return "PDF";
  if (t.includes("markdown") || t === "md") return "Markdown";
  if (t.includes("txt") || t === "text") return "文本";
  return sourceType || "文件";
}
