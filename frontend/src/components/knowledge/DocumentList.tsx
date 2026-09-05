import { useState } from "react";
import { Copy, FileText, Link2, Trash2 } from "lucide-react";
import type { DocumentItem } from "../../types";
import {
  documentStatusMeta,
  formatDateTime,
  sourceTypeLabel,
  truncate,
} from "../../lib/utils";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { Skeleton } from "../ui/skeleton";

export interface DocumentListProps {
  documents: DocumentItem[];
  loading?: boolean;
  onDelete: (id: string) => void;
}

/** 文档列表：状态徽章 / 删除按钮 / 复制 ID */
export function DocumentList({ documents, loading = false, onDelete }: DocumentListProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const copyId = async (id: string) => {
    try {
      await navigator.clipboard.writeText(id);
      setCopiedId(id);
      window.setTimeout(() => setCopiedId(null), 1500);
    } catch {
      /* 剪贴板不可用时静默忽略 */
    }
  };

  if (loading && documents.length === 0) {
    return (
      <Card className="space-y-3 p-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </Card>
    );
  }

  if (documents.length === 0) {
    return (
      <Card className="p-10 text-center text-sm text-slate-400">
        暂无文档，先上传文件或导入 URL 吧
      </Card>
    );
  }

  return (
    <Card className="divide-y divide-slate-700/30">
      <div className="flex items-center justify-between px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-100">文档列表</h3>
        <span className="text-xs text-slate-500">共 {documents.length} 个</span>
      </div>
      {documents.map((doc) => {
        const meta = documentStatusMeta(doc.status);
        return (
          <div key={doc.id} className="flex items-start gap-3 px-4 py-3">
            <span className="mt-0.5 text-indigo-400" aria-hidden="true">
              {doc.url ? <Link2 className="h-5 w-5" /> : <FileText className="h-5 w-5" />}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-slate-100" title={doc.filename}>
                {truncate(doc.filename, 60)}
              </p>
              <div className="mt-1 flex flex-wrap items-center gap-1.5">
                <Badge variant="outline">{sourceTypeLabel(doc.source_type)}</Badge>
                <Badge variant={meta.tone}>{meta.label}</Badge>
                <span className="text-xs text-slate-500">
                  {doc.chunk_count > 0 ? `${doc.chunk_count} 个分块` : "尚未分块"}
                  {doc.created_at && ` · ${formatDateTime(doc.created_at)}`}
                </span>
              </div>
              {doc.error && <p className="mt-1 text-xs text-rose-400">{doc.error}</p>}
            </div>
            <div className="flex shrink-0 items-center gap-1.5">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => void copyId(doc.id)}
                title="复制文档 ID"
              >
                {copiedId === doc.id ? "已复制" : <Copy className="h-4 w-4" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-rose-400 hover:bg-rose-500/10 hover:text-rose-300"
                onClick={() => onDelete(doc.id)}
                title="删除文档"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        );
      })}
    </Card>
  );
}
