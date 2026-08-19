"""知识库管理服务：文档入库、检索、问答。"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import SessionLocal
from app.core.llm_client import llm
from app.models.chat import ChatMessage
from app.models.document import Document
from app.rag import vector_store
from app.rag.document_processor import process_document
from app.rag.embedder import embedder
from app.rag.retriever import retrieve

logger = logging.getLogger(__name__)


async def ingest_document(
    filename: str,
    raw: bytes | None = None,
    text: str | None = None,
    source_type: str = "upload",
    url: str | None = None,
    meta: dict | None = None,
) -> Document:
    """解析 → 分块 → 向量化 → 写入 pgvector（PostgreSQL）。"""
    async with SessionLocal() as session:
        doc = Document(
            filename=filename,
            source_type=source_type,
            url=url,
            status="processing",
            meta=meta or {},
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        try:
            chunks = process_document(filename, raw=raw, text=text)
            if not chunks:
                doc.status = "failed"
                doc.error = "未能从文档中提取到有效内容"
                await session.commit()
                await session.refresh(doc)
                return doc
            vectors = await embedder.embed(chunks)
            saved = await vector_store.upsert_chunks(
                doc.id, filename, source_type, url, chunks, vectors
            )
            doc.chunk_count = saved
            doc.status = "ready"
            await session.commit()
        except Exception as e:  # noqa: BLE001
            logger.exception("文档入库失败: %s", filename)
            doc.status = "failed"
            doc.error = str(e)[:2000]
            await session.commit()
        await session.refresh(doc)
        return doc


async def delete_document(document_id: str) -> bool:
    """删除文档（向量 + 数据库记录）。"""
    async with SessionLocal() as session:
        doc = await session.get(Document, document_id)
        if not doc:
            return False
        await vector_store.delete_document_chunks(document_id)
        await session.delete(doc)
        await session.commit()
        return True


async def list_documents() -> list[Document]:
    async with SessionLocal() as session:
        stmt = select(Document).order_by(Document.created_at.desc())
        return list((await session.execute(stmt)).scalars().all())


async def chat_with_knowledge(
    session_id: str,
    question: str,
    document_id: str | None = None,
) -> tuple[str, list[dict]]:
    """基于知识库 RAG 回答，返回 (回答, 引用列表)。"""
    s = get_settings()
    hits = await retrieve(question, top_k=s.rag_top_k, document_id=document_id)

    context_parts: list[str] = []
    citations: list[dict] = []
    for i, h in enumerate(hits, start=1):
        context_parts.append(f"[{i}] {h['chunk']}")
        citations.append(
            {
                "index": i,
                "document_id": h["document_id"],
                "filename": h["filename"],
                "snippet": h["chunk"][:200],
                "score": h["score"],
            }
        )

    if not context_parts:
        context_block = "（知识库中暂无相关资料，请基于常识回答并明确说明）"
    else:
        context_block = "\n\n".join(context_parts)

    prompt = (
        "你是智研助手的知识库问答助手。请严格基于以下资料回答问题；"
        "资料中找不到答案时，请明确说明'知识库中没有相关信息'，不要编造。\n\n"
        f"资料：\n{context_block}\n\n"
        f"问题：{question}"
    )
    answer = (await llm.chat([{"role": "user", "content": prompt}])).strip()

    # 持久化对话
    async with SessionLocal() as session:
        session.add(ChatMessage(session_id=session_id, role="user", content=question, citations=[]))
        session.add(
            ChatMessage(session_id=session_id, role="assistant", content=answer, citations=citations)
        )
        await session.commit()
    return answer, citations


async def chat_history(session_id: str) -> list[ChatMessage]:
    async with SessionLocal() as session:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list((await session.execute(stmt)).scalars().all())
