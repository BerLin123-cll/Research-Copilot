import { useRef, useState } from "react";
import type { DocumentItem } from "../../types";
import { api } from "../../lib/api";
import { formatBytes } from "../../lib/utils";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { Input } from "../ui/input";
import { Separator } from "../ui/separator";

const ACCEPT = ".pdf,.md,.txt";

export interface DocumentUploaderProps {
  /** 上传/入库成功后回调（父组件负责刷新列表） */
  onUploaded: (doc: DocumentItem) => void;
}

/** 文档上传（file 上传）+ URL 入库 */
export function DocumentUploader({ onUploaded }: DocumentUploaderProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [url, setUrl] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const doUpload = async () => {
    if (!file || uploading) return;
    setUploading(true);
    setError(null);
    try {
      const doc = await api.uploadDocument(file);
      onUploaded(doc);
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
    } catch (e) {
      setError(e instanceof Error ? e.message : "上传失败，请稍后重试");
    } finally {
      setUploading(false);
    }
  };

  const doIngest = async () => {
    const u = url.trim();
    if (!u || ingesting) return;
    setIngesting(true);
    setError(null);
    try {
      const doc = await api.ingestUrl(u);
      onUploaded(doc);
      setUrl("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "URL 入库失败，请稍后重试");
    } finally {
      setIngesting(false);
    }
  };

  return (
    <Card className="space-y-4 p-4">
      <div>
        <h3 className="mb-2 text-sm font-semibold text-slate-800">📄 上传文档</h3>
        <div className="flex gap-2">
          <Input
            ref={fileRef}
            type="file"
            accept={ACCEPT}
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="file:mr-2 file:rounded-md file:border-0 file:bg-slate-100 file:px-2 file:py-1 file:text-xs file:font-medium file:text-slate-600 hover:file:bg-slate-200"
          />
          <Button onClick={() => void doUpload()} loading={uploading} disabled={!file}>
            上传
          </Button>
        </div>
        <p className="mt-1 text-xs text-slate-400">
          支持 .pdf / .md / .txt
          {file && ` · 已选择：${file.name}（${formatBytes(file.size)}）`}
        </p>
      </div>

      <Separator />

      <div>
        <h3 className="mb-2 text-sm font-semibold text-slate-800">🌐 URL 入库</h3>
        <div className="flex gap-2">
          <Input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/article"
            disabled={ingesting}
          />
          <Button variant="secondary" onClick={() => void doIngest()} loading={ingesting} disabled={!url.trim()}>
            入库
          </Button>
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
    </Card>
  );
}
