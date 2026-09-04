"""网络搜索工具：DuckDuckGo（免费、无需 API Key、中文支持好）。

兼容新旧两个包名：ddgs（新） / duckduckgo_search（旧）。
"""
import asyncio
import logging
from importlib import import_module
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

try:
    DDGS = import_module("ddgs").DDGS
except ImportError:  # pragma: no cover
    try:
        DDGS = import_module("duckduckgo_search").DDGS
    except ImportError:
        DDGS = None  # type: ignore[assignment]

# 全局并发信号量：限制同时进行的 DDG 请求数，避免多任务并发时同 IP 被限流
_ddg_sem: asyncio.Semaphore | None = None


def _get_ddg_sem() -> asyncio.Semaphore:
    global _ddg_sem
    if _ddg_sem is None:
        _ddg_sem = asyncio.Semaphore(get_settings().web_search_max_concurrency)
    return _ddg_sem


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
            kwargs: dict[str, Any] = {"query": query, "max_results": max_results}
            if s.web_search_timelimit:
                try:
                    # 新版 ddgs 支持 timelimit: d/w/m/y（一天/一周/一月/一年内）
                    kwargs["timelimit"] = s.web_search_timelimit
                    rows = ddgs.text(**kwargs)
                except TypeError:
                    # 旧版本不支持 timelimit 参数，去掉后重试
                    kwargs.pop("timelimit", None)
                    rows = ddgs.text(**kwargs)
            else:
                rows = ddgs.text(**kwargs)
            for r in rows:
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href") or r.get("url", ""),
                        "snippet": r.get("body", ""),
                    }
                )
        return results

    async def _bounded() -> list[dict[str, Any]]:
        async with _get_ddg_sem():
            # DDGS 是同步阻塞调用，放到线程池避免阻塞事件循环；带超时防止长时间无响应
            return await asyncio.wait_for(asyncio.to_thread(_run), timeout=s.tool_timeout)

    try:
        return await _bounded()
    except asyncio.TimeoutError:
        logger.warning("web_search 超时: query=%s", query)
        return []
    except Exception as e:  # noqa: BLE001
        logger.warning("web_search 失败: %s (query=%s)", e, query)
        return []
