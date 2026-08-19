"""学术论文搜索工具：arXiv API（免费、学术权威）。"""
import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

try:
    import arxiv
except ImportError:  # pragma: no cover
    arxiv = None  # type: ignore[assignment]


async def arxiv_search(
    query: str,
    max_results: int | None = None,
    sort_by: str = "relevance",
) -> list[dict[str, Any]]:
    """搜索 arXiv 论文，返回 [{title, authors, summary, url, published}]。"""
    s = get_settings()
    max_results = max_results or s.arxiv_max_results
    if arxiv is None:
        logger.warning("arxiv 包未安装，arxiv_search 不可用")
        return []

    sort_map = {
        "relevance": arxiv.SortCriterion.Relevance,
        "submitted_date": arxiv.SortCriterion.SubmittedDate,
        "updated_date": arxiv.SortCriterion.LastUpdatedDate,
    }

    def _run() -> list[dict[str, Any]]:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_map.get(sort_by, arxiv.SortCriterion.Relevance),
        )
        results: list[dict[str, Any]] = []
        for r in client.results(search):
            results.append(
                {
                    "title": r.title,
                    "authors": [a.name for a in r.authors],
                    "summary": r.summary,
                    "url": r.entry_id,
                    "pdf_url": r.pdf_url,
                    "published": r.published.isoformat() if r.published else None,
                }
            )
        return results

    try:
        import asyncio

        return await asyncio.to_thread(_run)
    except Exception as e:  # noqa: BLE001
        logger.warning("arxiv_search 失败: %s (query=%s)", e, query)
        return []
