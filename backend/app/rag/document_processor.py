"""文档加载与分块：支持 PDF / Markdown / TXT / HTML / 网页 URL。"""
import logging
from typing import BinaryIO

from app.config import get_settings

logger = logging.getLogger(__name__)

# 常见停用词/噪音过滤（分块后简单清理）
_BLOCKLIST = (
    "navigation", "footer", "copyright", "cookie", "sign in", "subscribe",
)


def load_pdf(file: BinaryIO) -> str:
    from pypdf import PdfReader

    reader = PdfReader(file)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def load_text(raw: bytes) -> str:
    for enc in ("utf-8", "gb18030", "latin-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="ignore")


def load_markdown(text: str) -> str:
    # 简单清洗：去掉代码围栏以外的无关行保留结构
    return text


def load_html(html: str) -> str:
    from html.parser import HTMLParser

    class P(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.parts: list[str] = []

        def handle_data(self, data: str) -> None:
            t = data.strip()
            if t:
                self.parts.append(t)

    p = P()
    p.feed(html)
    return "\n".join(p.parts)


def split_text(text: str) -> list[str]:
    """递归字符分块：chunk_size=512, overlap=50。"""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=get_settings().chunk_size,
        chunk_overlap=get_settings().chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    # 清理过短/无意义分块
    cleaned = [c.strip() for c in chunks if c.strip()]
    return cleaned


def process_document(
    filename: str,
    raw: bytes | None = None,
    text: str | None = None,
) -> list[str]:
    """统一入口：根据扩展名解析并分块，返回 chunk 列表。"""
    name = (filename or "").lower()
    if text is None:
        if raw is None:
            return []
        text = load_text(raw)

    if name.endswith(".pdf"):
        import io

        text = load_pdf(io.BytesIO(raw or b""))
    elif name.endswith((".md", ".markdown")):
        text = load_markdown(text)
    elif name.endswith(".html") or name.endswith(".htm"):
        text = load_html(text)

    if not text or not text.strip():
        return []
    return split_text(text)
