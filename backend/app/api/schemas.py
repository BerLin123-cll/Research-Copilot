"""API 请求/响应模式（Pydantic v2）。"""
from pydantic import BaseModel, Field


# ---------- 研究 ----------
class ResearchCreate(BaseModel):
    topic: str = Field(min_length=2, max_length=500, description="研究主题")


class SourceItem(BaseModel):
    title: str = ""
    url: str = ""


class ResearchOut(BaseModel):
    id: str
    topic: str
    status: str
    plan: list[str] = []
    current_step: int = 0
    search_queries: list[str] = []
    sources: list[dict] = []
    error: str | None = None
    report_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ReportOut(BaseModel):
    id: str
    task_id: str
    title: str
    content: str
    summary: str | None = None
    created_at: str | None = None


# ---------- 知识库 ----------
class DocumentOut(BaseModel):
    id: str
    filename: str
    source_type: str
    url: str | None = None
    status: str
    chunk_count: int = 0
    meta: dict = {}
    error: str | None = None
    created_at: str | None = None


class UrlIngestRequest(BaseModel):
    url: str = Field(min_length=4, max_length=1000)


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, description="为空时服务端自动生成")
    question: str = Field(min_length=1, max_length=2000)
    document_id: str | None = None


class Citation(BaseModel):
    index: int
    document_id: str
    filename: str
    snippet: str
    score: float


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: list[dict] = []


class ChatMessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    citations: list[dict] = []
    created_at: str | None = None
