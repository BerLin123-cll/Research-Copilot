"""网页内容抓取工具。

默认使用 httpx + readability-lxml 提取正文；配置 PLAYWRIGHT_ENABLED=true
时可启用 Playwright 渲染动态页面（需额外安装 playwright 与 chromium）。
"""
import logging
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
    """抓取网页正文，返回 {url, title, content, error?}。"""
    s = get_settings()
    html = ""

    if s.playwright_enabled:
        html = await _fetch_playwright(url)
    if not html:
        html = await _fetch_httpx(url)
    if not html:
        return {"url": url, "title": "", "content": "", "error": "抓取失败"}

    content = _extract_readable(html)
    return {"url": url, "title": _extract_title(html), "content": content}


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
        from playwright.async_api import async_playwright

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
