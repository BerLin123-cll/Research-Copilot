"""知识库 REST API：文档上传/URL 入库、列表、删除、RAG 问答。"""
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.schemas import ChatMessageOut, ChatRequest, ChatResponse, DocumentOut, UrlIngestRequest
from app.services import knowledge_service
from app.tools.web_fetch import fetch_webpage

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/documents", response_model=DocumentOut, status_code=201)
async def upload_document(file: UploadFile = File(...)):
    """上传文档（PDF / Markdown / TXT / HTML）并入库。"""
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="文件为空")
    filename = file.filename or "untitled.txt"
    doc = await knowledge_service.ingest_document(filename=filename, raw=raw)
    return doc.to_dict()


@router.post("/ingest-url", response_model=DocumentOut, status_code=201)
async def ingest_url(body: UrlIngestRequest):
    """抓取网页链接并作为资料入库。"""
    page = await fetch_webpage(body.url.strip())
    content = page.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="网页抓取失败或内容为空")
    doc = await knowledge_service.ingest_document(
        filename=page.get("title", body.url)[:200] + ".txt",
        text=content,
        source_type="url",
        url=body.url.strip(),
    )
    return doc.to_dict()


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents():
    docs = await knowledge_service.list_documents()
    return [d.to_dict() for d in docs]


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    ok = await knowledge_service.delete_document(document_id)
    if not ok:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"ok": True, "deleted": document_id}


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """基于知识库问答（RAG），返回回答与引用。"""
    session_id = body.session_id or str(uuid.uuid4())
    answer, citations = await knowledge_service.chat_with_knowledge(
        session_id=session_id,
        question=body.question.strip(),
        document_id=body.document_id,
    )
    return {"session_id": session_id, "answer": answer, "citations": citations}


@router.get("/chat/history", response_model=list[ChatMessageOut])
async def chat_history(session_id: str):
    if not session_id:
        raise HTTPException(status_code=400, detail="缺少 session_id")
    messages = await knowledge_service.chat_history(session_id)
    return [m.to_dict() for m in messages]
