"""网络搜索工具：DuckDuckGo（免费、无需 API Key、中文支持好）。

兼容新旧两个包名：ddgs（新） / duckduckgo_search（旧）。
"""
import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

try:
    from ddgs import DDGS
except ImportError:  # pragma: no cover
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None  # type: ignore[assignment]


async def web_search(query: str, max_results: int | None = None) -> list[dict[str, Any]]:
    """执行网络搜索，返回 [{title, url, snippet}] 列表。"""
    s = get_settings()
    max_results = max_results or s.web_search_max_results
    if DDGS is None:
        logger.warning("duckduckgo-search 未安装，web_search 不可用")
        return []

    def _run() -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href") or r.get("url", ""),
                        "snippet": r.get("body", ""),
                    }
                )
        return results

    try:
        # DDGS 是同步阻塞调用，放到线程池避免阻塞事件循环
        import asyncio

        return await asyncio.to_thread(_run)
    except Exception as e:  # noqa: BLE001
        logger.warning("web_search 失败: %s (query=%s)", e, query)
        return []
