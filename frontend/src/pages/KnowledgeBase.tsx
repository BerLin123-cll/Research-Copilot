import { useCallback, useEffect, useState } from "react";
import type { DocumentItem } from "../types";
import { api } from "../lib/api";
import { DocumentList } from "../components/knowledge/DocumentList";
import { DocumentUploader } from "../components/knowledge/DocumentUploader";
import { ChatWithDocs } from "../components/knowledge/ChatWithDocs";

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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">知识库</h1>
        <p className="mt-1 text-sm text-slate-500">
          上传文档或导入 URL，构建你的私有知识库，并基于它进行 RAG 问答。
        </p>
      </div>
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div className="space-y-6">
          <DocumentUploader onUploaded={handleUploaded} />
          <DocumentList documents={documents} loading={loading} onDelete={(id) => void handleDelete(id)} />
        </div>
        <ChatWithDocs documents={documents} />
      </div>
    </div>
  );
}
