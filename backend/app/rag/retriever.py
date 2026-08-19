"""检索器：Embedding → pgvector 语义检索（可扩展重排序）。"""
import logging
from typing import Any

from app.rag import vector_store
from app.rag.embedder import embedder

logger = logging.getLogger(__name__)


async def retrieve(
    query: str,
    top_k: int | None = None,
    document_id: str | None = None,
) -> list[dict[str, Any]]:
    """语义检索：将问题向量化后在知识库中查找相关片段。

    重排序（cross-encoder）作为可选扩展点：在数据量较大时可在此
    接入 reranker 对候选集二次排序（默认不启用，保持依赖精简）。
    """
    query_vector = await embedder.embed_one(query)
    if not query_vector:
        return []
    results = await vector_store.search_chunks(
        query_vector=query_vector, top_k=top_k, document_id=document_id
    )
    return results


async def rerank(candidates: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    """重排序扩展点（默认原样返回，可按需实现 cross-encoder）。"""
    return candidates
