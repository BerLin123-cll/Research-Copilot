import { useCallback, useEffect, useMemo, useState } from "react";
import { BookOpen, FileText, Globe, MessageCircle } from "lucide-react";
import type { DocumentItem } from "../types";
import { api } from "../lib/api";
import { DocumentList } from "../components/knowledge/DocumentList";
import { DocumentUploader } from "../components/knowledge/DocumentUploader";
import { ChatWithDocs } from "../components/knowledge/ChatWithDocs";
import { Card } from "../components/ui/card";

/** 知识库管理页：上传 / 列表 + RAG 问答 */
export function KnowledgeBase() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await api.listDocuments());
    } catch {
      /* 静默失败，页面展示空态 */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleUploaded = (doc: DocumentItem) => {
    setDocuments((d) => [doc, ...d.filter((x) => x.id !== doc.id)]);
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteDocument(id);
      setDocuments((d) => d.filter((x) => x.id !== id));
    } catch {
      /* 删除失败静默忽略 */
    }
  };

  const stats = useMemo(() => {
    const urlCount = documents.filter((d) => d.source_type === "url" || d.source_type === "web").length;
    const fileCount = documents.length - urlCount;
    return [
      {
        label: "文档总数",
        value: documents.length,
        icon: BookOpen,
        bg: "bg-indigo-500/15 text-indigo-300 ring-1 ring-inset ring-indigo-500/20",
      },
      {
        label: "本地文件",
        value: fileCount,
        icon: FileText,
        bg: "bg-sky-500/15 text-sky-300 ring-1 ring-inset ring-sky-500/20",
      },
      {
        label: "URL 来源",
        value: urlCount,
        icon: Globe,
        bg: "bg-emerald-500/15 text-emerald-300 ring-1 ring-inset ring-emerald-500/20",
      },
      {
        label: "可问答",
        value: documents.filter((d) => d.status === "ready" || d.status === "completed").length,
        icon: MessageCircle,
        bg: "bg-violet-500/15 text-violet-300 ring-1 ring-inset ring-violet-500/20",
      },
    ];
  }, [documents]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">知识库</h1>
        <p className="text-sm text-slate-400">
          上传文档或导入 URL，构建你的私有知识库，并基于它进行 RAG 问答。
        </p>
      </div>

      {/* 数据指标 */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
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
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-1">
          <DocumentUploader onUploaded={handleUploaded} />
          <DocumentList documents={documents} loading={loading} onDelete={(id) => void handleDelete(id)} />
        </div>
        <div className="lg:col-span-2">
          <ChatWithDocs documents={documents} />
        </div>
      </div>
    </div>
  );
}
