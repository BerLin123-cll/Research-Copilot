"""网页内容抓取工具。

默认使用 httpx + readability-lxml 提取正文；配置 PLAYWRIGHT_ENABLED=true
时可启用 Playwright 渲染动态页面（需额外安装 playwright 与 chromium）。
"""
import logging
import importlib
import re
from html.parser import HTMLParser
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


class _TextParser(HTMLParser):
    """极简回退方案：剥离 HTML 标签提取文本。"""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        t = data.strip()
        if t:
            self.parts.append(t)


def _extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if m:
        return m.group(1).strip()[:255]
    return ""


# 常见发布日期 meta 标签（article:published_time / datePublished / 等）
_PUBLISH_META = re.compile(
    r'<meta[^>]+(?:property|name)\s*=\s*["\']'
    r"(?:article:published_time|datePublished|date|pubdate|og:published_time|"
    r"sailthru\.date|publishdate|dc\.date|parsely-pub-date)[\"']"
    r"[^>]*>",
    re.I,
)
_META_CONTENT = re.compile(r'content\s*=\s*["\']([^"\']+)["\']', re.I)


def _extract_published(html: str) -> str:
    """尝试解析页面发布日期，返回 YYYY-MM-DD（无法解析返回空串）。"""
    m = _PUBLISH_META.search(html)
    if m:
        c = _META_CONTENT.search(m.group(0))
        if c:
            val = c.group(1).strip()
            if re.match(r"^\d{4}-\d{2}-\d{2}", val):
                return val[:10]
            return val[:50]
    # 兜底：正文前 4000 字符内的常见日期写法
    m2 = re.search(r"(20\d{2})[-/年](\d{1,2})[-/月](\d{1,2})", html[:4000])
    if m2:
        return f"{m2.group(1)}-{int(m2.group(2)):02d}-{int(m2.group(3)):02d}"
    return ""


def _extract_readable(html: str) -> str:
    """用 readability 提取正文，失败时回退到纯文本剥离。"""
    try:
        import readability
        from lxml import html as lxml_html

        doc = readability.Document(html)
        cleaned = lxml_html.fromstring(doc.summary())
        return cleaned.text_content().strip()
    except Exception:  # noqa: BLE001
        parser = _TextParser()
        parser.feed(html)
        return "\n".join(parser.parts)


async def fetch_webpage(url: str) -> dict[str, Any]:
    """抓取网页正文，返回 {url, title, content, published?, error?}。"""
    s = get_settings()
    html = ""

    if s.playwright_enabled:
        html = await _fetch_playwright(url)
    if not html:
        html = await _fetch_httpx(url)
    if not html:
        return {"url": url, "title": "", "content": "", "error": "抓取失败"}

    content = _extract_readable(html)
    return {
        "url": url,
        "title": _extract_title(html),
        "content": content,
        "published": _extract_published(html),
    }


async def _fetch_httpx(url: str) -> str:
    s = get_settings()
    try:
        async with httpx.AsyncClient(
            timeout=s.fetch_timeout, headers={"User-Agent": UA}, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as e:  # noqa: BLE001
        logger.warning("fetch_webpage(httpx) 失败: %s (url=%s)", e, url)
        return ""


async def _fetch_playwright(url: str) -> str:
    """可选：Playwright 渲染动态页面。"""
    try:
        async_playwright = importlib.import_module(
            "playwright.async_api"
        ).async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=30000, wait_until="networkidle")
            html = await page.content()
            await browser.close()
            return html
    except Exception as e:  # noqa: BLE001
        logger.warning("fetch_webpage(playwright) 失败: %s (url=%s)", e, url)
        return ""
