import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { MessageSquare, Plus } from "lucide-react";
import type { ChatMessage, DocumentItem } from "../../types";
import { api } from "../../lib/api";
import { cn, formatDateTime } from "../../lib/utils";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import { Skeleton } from "../ui/skeleton";

/** 会话 ID 的 localStorage 键 */
const SESSION_KEY = "rc_chat_session";

export interface ChatWithDocsProps {
  documents: DocumentItem[];
}

/**
 * 知识库 RAG 问答：
 * - 会话 ID 存 localStorage（key: rc_chat_session），首次问答由后端创建
 * - 引用标注渲染为可点击徽章 [1]，点击展开对应 snippet
 */
export function ChatWithDocs({ documents }: ChatWithDocsProps) {
  const [sessionId, setSessionId] = useState<string>(
    () => localStorage.getItem(SESSION_KEY) ?? "",
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);
  const [docFilter, setDocFilter] = useState("");
  const [expanded, setExpanded] = useState<Record<string, number[]>>({});
  const [loadingHistory, setLoadingHistory] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // 新消息时自动滚动到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 已有会话时加载历史
  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    setLoadingHistory(true);
    api
      .getChatHistory(sessionId)
      .then((h) => {
        if (!cancelled) setMessages(h);
      })
      .catch(() => {
        if (!cancelled) setMessages([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingHistory(false);
      });
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  const send = async () => {
    const q = question.trim();
    if (!q || sending) return;
    setSending(true);
    setQuestion("");

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      session_id: sessionId,
      role: "user",
      content: q,
      citations: [],
      created_at: new Date().toISOString(),
    };
    setMessages((m) => [...m, userMsg]);

    try {
      const res = await api.chatKnowledge({
        session_id: sessionId || undefined,
        question: q,
        document_id: docFilter || undefined,
      });
      const sid = sessionId || res.session_id;
      if (!sessionId) {
        setSessionId(sid);
        localStorage.setItem(SESSION_KEY, sid);
      }
      const asstMsg: ChatMessage = {
        id: crypto.randomUUID(),
        session_id: sid,
        role: "assistant",
        content: res.answer,
        citations: res.citations,
        created_at: new Date().toISOString(),
      };
      setMessages((m) => [...m, asstMsg]);
    } catch (e) {
      const errMsg: ChatMessage = {
        id: crypto.randomUUID(),
        session_id: sessionId,
        role: "assistant",
        content: `请求失败：${e instanceof Error ? e.message : "未知错误"}`,
        citations: [],
        created_at: new Date().toISOString(),
      };
      setMessages((m) => [...m, errMsg]);
    } finally {
      setSending(false);
    }
  };

  const newSession = () => {
    localStorage.removeItem(SESSION_KEY);
    setSessionId("");
    setMessages([]);
    setExpanded({});
  };

  const toggleCitation = (messageId: string, index: number) => {
    setExpanded((prev) => {
      const cur = prev[messageId] ?? [];
      const next = cur.includes(index)
        ? cur.filter((i) => i !== index)
        : [...cur, index];
      return { ...prev, [messageId]: next };
    });
  };

  /** 渲染回答正文中的引用标注 [n] 为可点击徽章 */
  const renderContent = (
    content: string,
    citations: ChatMessage["citations"],
    onToggle: (index: number) => void,
  ): ReactNode[] => {
    const parts = content.split(/(\[\d+\])/g);
    return parts.map((part, i) => {
      const m = part.match(/^\[(\d+)\]$/);
      if (m) {
        const idx = Number(m[1]);
        const cite = citations.find((c) => c.index === idx);
        if (cite) {
          return (
            <button
              key={i}
              type="button"
              onClick={() => onToggle(idx)}
              title={`查看引用来源：${cite.filename}`}
              className="mx-0.5 inline-flex items-center rounded-full border border-indigo-400/30 bg-indigo-500/15 px-1.5 py-0.5 align-baseline text-[11px] font-semibold text-indigo-300 transition-colors hover:bg-indigo-500/25"
            >
              {idx}
            </button>
          );
        }
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <Card className="flex h-[640px] flex-col">
      {/* 头部 */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-700/30 px-4 py-3">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-100">
          <MessageSquare className="h-4 w-4 text-indigo-400" />
          知识库问答
        </h3>
        <select
          value={docFilter}
          onChange={(e) => setDocFilter(e.target.value)}
          className="ml-auto h-8 rounded-lg border border-slate-600/30 bg-slate-900/40 px-2 text-xs text-slate-300 focus:border-indigo-500/60 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
          title="限定检索范围"
        >
          <option value="">全部文档</option>
          {documents.map((d) => (
            <option key={d.id} value={d.id}>
              {d.filename}
            </option>
          ))}
        </select>
        <Button variant="outline" size="sm" onClick={newSession}>
          <Plus className="mr-1 h-4 w-4" />
          新会话
        </Button>
      </div>

      {/* 消息区 */}
      <ScrollArea className="flex-1 p-4">
        {loadingHistory && messages.length === 0 ? (
          <div className="space-y-4">
            <Skeleton className="ml-auto h-10 w-1/2 rounded-2xl" />
            <Skeleton className="h-20 w-2/3 rounded-2xl" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex h-full items-center justify-center px-6 text-center text-sm text-slate-500">
            <div>
              <MessageSquare className="mx-auto mb-2 h-8 w-8 text-slate-600" />
              向知识库提问吧！
              <br />
              例如：这篇文档的核心观点是什么？
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg) => {
              const expandedIdx = expanded[msg.id] ?? [];
              const isUser = msg.role === "user";
              return (
                <div key={msg.id} className={cn("flex", isUser ? "justify-end" : "justify-start")}>
                  <div className={cn("max-w-[85%]", isUser ? "text-right" : "text-left")}>
                    <div
                      className={cn(
                        "inline-block rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                        isUser
                          ? "bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-lg shadow-indigo-500/20"
                          : "border border-slate-600/30 bg-slate-900/40 text-slate-100",
                      )}
                    >
                      {isUser ? (
                        <span className="whitespace-pre-wrap">{msg.content}</span>
                      ) : (
                        <span className="whitespace-pre-wrap">
                          {renderContent(msg.content, msg.citations, (idx) =>
                            toggleCitation(msg.id, idx),
                          )}
                        </span>
                      )}
                    </div>
                    <p className="mt-1 px-1 text-[11px] text-slate-500">
                      {formatDateTime(msg.created_at)}
                      {!isUser && msg.citations.length > 0 && ` · ${msg.citations.length} 条引用`}
                    </p>

                    {/* 展开的引用 snippet */}
                    {!isUser && expandedIdx.length > 0 && (
                      <div className="mt-2 space-y-2">
                        {expandedIdx.map((ci) => {
                          const cite = msg.citations.find((c) => c.index === ci);
                          if (!cite) return null;
                          return (
                            <div
                              key={ci}
                              className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-left"
                            >
                              <div className="mb-1 flex flex-wrap items-center gap-2 text-amber-200">
                                <span className="text-xs font-semibold">引用 [{cite.index}]</span>
                                <span className="max-w-48 truncate text-xs">{cite.filename}</span>
                                <Badge variant="outline" className="ml-auto shrink-0">
                                  相关度 {typeof cite.score === "number" ? cite.score.toFixed(3) : "—"}
                                </Badge>
                              </div>
                              <p className="line-clamp-4 text-xs leading-relaxed text-slate-300">
                                {cite.snippet}
                              </p>
                              <p className="mt-1 break-all font-mono text-[10px] text-amber-300/70">
                                {cite.document_id}
                              </p>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            <div ref={bottomRef} />
          </div>
        )}
      </ScrollArea>

      {/* 输入区 */}
      <form
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          void send();
        }}
        className="flex items-center gap-2 border-t border-slate-700/30 p-3"
      >
        <Input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={sessionId ? "继续提问…" : "输入问题，开始新的知识库会话…"}
          disabled={sending}
          className="flex-1"
        />
        <Button type="submit" loading={sending} disabled={!question.trim()}>
          发送
        </Button>
      </form>
    </Card>
  );
}
