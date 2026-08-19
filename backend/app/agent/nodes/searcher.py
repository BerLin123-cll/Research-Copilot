"""搜索节点：调用搜索/抓取工具收集信息，并将研究资料同步到知识库。"""
import logging

from app.agent.events import EventBus, event_bus
from app.agent.nodes.utils import append_unique_sources
from app.agent.state import ResearchState
from app.config import get_settings
from app.models.research import ResearchTask
from app.rag.document_processor import split_text
from app.rag.embedder import embedder
from app.rag import vector_store
from app.tools import arxiv_search, web_fetch, web_search

logger = logging.getLogger(__name__)

# 每轮最多抓取的网页数量（控制执行时长）
_MAX_FETCHES_PER_ROUND = 4


def make_searcher(ctx) -> object:
    """返回 searcher 节点。ctx 提供 task_id / session。"""

    async def searcher(state: ResearchState) -> dict:
        bus: EventBus = event_bus
        task_id = state["task_id"]
        s = get_settings()
        iteration = state.get("iterations", 1)

        queries = [str(q) for q in (state.get("search_queries") or [state["topic"]]) if str(q).strip()]
        raw_results = list(state.get("raw_results") or [])
        sources = list(state.get("sources") or [])
        kb_chunks_saved = state.get("kb_chunks_saved", 0)

        await bus.publish(task_id, EventBus.node_event("start", "searcher"))
        await bus.publish(
            task_id,
            EventBus.status_event("running", f"正在搜索资料（第 {iteration} 轮）…"),
        )

        new_results: list[dict] = []
        fetch_budget = _MAX_FETCHES_PER_ROUND

        for query in queries:
            # ---- 网络搜索 ----
            await bus.publish(task_id, EventBus.tool_call_event("web_search", {"query": query}))
            web_results = await web_search.web_search(query)
            await bus.publish(
                task_id,
                EventBus.tool_result_event(
                    "web_search",
                    {"query": query, "count": len(web_results), "results": web_results[:3]},
                    success=bool(web_results),
                ),
            )
            for r in web_results:
                item = {"type": "web", "query": query, **r}
                raw_results.append(item)
                new_results.append(item)

            # ---- arXiv 学术搜索 ----
            await bus.publish(task_id, EventBus.tool_call_event("arxiv_search", {"query": query}))
            papers = await arxiv_search.arxiv_search(query)
            await bus.publish(
                task_id,
                EventBus.tool_result_event(
                    "arxiv_search",
                    {"query": query, "count": len(papers), "papers": papers[:3]},
                    success=bool(papers),
                ),
            )
            for p in papers:
                item = {
                    "type": "arxiv",
                    "query": query,
                    "title": p.get("title", ""),
                    "url": p.get("url", ""),
                    "snippet": p.get("summary", ""),
                    "authors": p.get("authors", []),
                    "published": p.get("published"),
                }
                raw_results.append(item)
                new_results.append(item)

            # ---- 抓取 Top 网页（有预算时） ----
            for r in web_results[:2]:
                if fetch_budget <= 0:
                    break
                url = r.get("url")
                if not url:
                    continue
                fetch_budget -= 1
                await bus.publish(task_id, EventBus.tool_call_event("fetch_webpage", {"url": url}))
                page = await web_fetch.fetch_webpage(url)
                content = page.get("content", "")
                ok = bool(content)
                await bus.publish(
                    task_id,
                    EventBus.tool_result_event(
                        "fetch_webpage",
                        {"url": url, "title": page.get("title", ""), "content_length": len(content)},
                        success=ok,
                    ),
                )
                if ok:
                    item = {
                        "type": "page",
                        "query": query,
                        "url": url,
                        "title": page.get("title", ""),
                        "content": content[:8000],
                    }
                    raw_results.append(item)
                    new_results.append(item)

        # ---- 汇总来源（按 URL 去重） ----
        source_items = []
        for r in raw_results:
            if r.get("type") in ("web", "arxiv", "page"):
                source_items.append(
                    {"title": r.get("title", "") or r.get("url", ""), "url": r.get("url", "")}
                )
        sources, _ = append_unique_sources(sources, source_items)

        # ---- 将本轮研究资料写入知识库（pgvector），供后续深度问答 ----
        if s.save_research_to_kb and kb_chunks_saved < s.research_kb_max_chunks:
            texts = []
            for r in new_results:
                if r.get("type") == "page" and r.get("content"):
                    texts.append(r["content"])
                elif r.get("type") == "arxiv" and r.get("snippet"):
                    texts.append(r["snippet"])
                elif r.get("type") == "web" and r.get("snippet"):
                    texts.append(r["snippet"])
            corpus = "\n\n".join(texts)
            chunks = split_text(corpus)[: s.research_kb_max_chunks - kb_chunks_saved]
            if chunks:
                await bus.publish(
                    task_id,
                    EventBus.status_event("running", f"正在同步研究资料到知识库（{len(chunks)} 个分块）…"),
                )
                try:
                    vectors = await embedder.embed(chunks)
                    doc_id = f"research:{task_id}:{iteration}"
                    saved = await vector_store.upsert_chunks(
                        document_id=doc_id,
                        filename=f"research-{task_id[:8]}-round{iteration}.txt",
                        source_type="research",
                        url=None,
                        chunks=chunks,
                        vectors=vectors,
                        extra_meta={"task_id": task_id, "round": iteration},
                    )
                    kb_chunks_saved += saved
                except Exception as e:  # noqa: BLE001
                    logger.warning("研究资料写入知识库失败: %s", e)

        # ---- 持久化 ----
        task = await ctx.session.get(ResearchTask, task_id)
        if task:
            task.search_queries = queries
            task.sources = sources
            task.status = "running"
            await ctx.session.commit()

        await bus.publish(
            task_id,
            EventBus.tool_result_event(
                "knowledge_base_sync",
                {"chunks_saved": kb_chunks_saved},
                success=True,
            ),
        )
        await bus.publish(task_id, EventBus.node_event("end", "searcher"))
        return {
            "raw_results": raw_results,
            "sources": sources,
            "kb_chunks_saved": kb_chunks_saved,
            "current_step": iteration,
        }

    return searcher
