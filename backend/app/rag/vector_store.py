"""pgvector 向量存储操作（向量直接存储在 PostgreSQL 中，免费开源）。

- 依赖 PostgreSQL 的 pgvector 扩展（docker-compose 使用 pgvector/pgvector:pg16 镜像自动启用）
- 向量表：document_chunks（由 ensure_vector_table / alembic 迁移创建）
- 检索：余弦距离（embedding <=> query），返回相似度 = 1 - distance
"""
import logging
import uuid
from typing import Any

from sqlalchemy import delete, select, text

from app.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.models.vector_chunk import VectorChunk

logger = logging.getLogger(__name__)


async def ensure_vector_table() -> None:
    """确保 vector 扩展、向量表与 HNSW 索引就绪（幂等，可重复调用）。"""
    is_pg = engine.dialect.name == "postgresql"
    if is_pg:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    # 建表（已在 alembic 迁移中建过则为 no-op）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    if is_pg:
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw "
                        "ON document_chunks USING hnsw (embedding vector_cosine_ops)"
                    )
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("创建 HNSW 索引失败（可接受，仅影响大数据量检索速度）: %s", e)


async def upsert_chunks(
    document_id: str,
    filename: str,
    source_type: str,
    url: str | None,
    chunks: list[str],
    vectors: list[list[float]],
    extra_meta: dict[str, Any] | None = None,
) -> int:
    """将文档分块写入 pgvector 表，返回写入条数。extra_meta 可附加自定义元数据。"""
    if len(chunks) != len(vectors):
        raise ValueError("chunks 与 vectors 数量不一致")
    async with SessionLocal() as session:
        for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
            session.add(
                VectorChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    filename=filename,
                    source_type=source_type,
                    url=url or "",
                    chunk_index=i,
                    chunk=chunk,
                    embedding=[float(v) for v in vec],
                    meta=dict(extra_meta) if extra_meta else {},
                )
            )
        await session.commit()
    return len(chunks)


async def search_chunks(
    query_vector: list[float],
    top_k: int | None = None,
    document_id: str | None = None,
) -> list[dict[str, Any]]:
    """余弦相似度检索，返回 [{document_id, filename, url, chunk, chunk_index, score}]。"""
    s = get_settings()
    top_k = top_k or s.rag_top_k
    distance = VectorChunk.embedding.cosine_distance(query_vector).label("distance")
    stmt = select(VectorChunk, distance).order_by(distance).limit(top_k)
    if document_id:
        stmt = stmt.where(VectorChunk.document_id == document_id)
    async with SessionLocal() as session:
        rows = (await session.execute(stmt)).all()
    results = []
    for chunk, dist in rows:
        results.append(
            {
                "document_id": chunk.document_id,
                "filename": chunk.filename,
                "url": chunk.url,
                "chunk": chunk.chunk,
                "chunk_index": chunk.chunk_index,
                "score": round(1 - float(dist), 4),
            }
        )
    return results


async def delete_document_chunks(document_id: str) -> None:
    """删除某个文档的所有向量。"""
    async with SessionLocal() as session:
        await session.execute(delete(VectorChunk).where(VectorChunk.document_id == document_id))
        await session.commit()
