import { useState } from "react";
import type { Report } from "../../types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Check } from "lucide-react";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { Separator } from "../ui/separator";
import { Skeleton } from "../ui/skeleton";

export interface ReportViewerProps {
  report: Report | null;
  loading?: boolean;
}

/** 研究报告查看器：react-markdown 渲染 + 复制全文按钮 */
export function ReportViewer({ report, loading = false }: ReportViewerProps) {
  const [copied, setCopied] = useState(false);

  const copyContent = async () => {
    if (!report) return;
    try {
      await navigator.clipboard.writeText(report.content);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* 剪贴板不可用时静默忽略 */
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  if (!report) {
    return (
      <Card className="p-10 text-center text-sm text-slate-400">
        暂无报告，任务完成（或收到 report_ready 事件）后将在这里展示研究报告
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-slate-100">{report.title || "研究报告"}</h2>
          {report.summary && (
            <p className="mt-1 text-sm text-slate-400">{report.summary}</p>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={() => void copyContent()}>
          {copied ? <Check className="mr-1 h-4 w-4" /> : <Copy className="mr-1 h-4 w-4" />}
          {copied ? "已复制" : "复制全文"}
        </Button>
      </div>
      <Separator className="mb-4" />
      <div className="markdown-body">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{report.content}</ReactMarkdown>
      </div>
    </Card>
  );
}
