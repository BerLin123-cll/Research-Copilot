"""Agent 节点共享工具：Prompt 加载、JSON 解析、来源去重。"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> str:
    """从 prompts 目录加载 Prompt 模板。"""
    path = _PROMPT_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt 文件不存在: {path}")
    return path.read_text(encoding="utf-8")


def extract_json(text: str) -> dict:
    """从 LLM 输出中稳健提取 JSON 对象（容忍代码围栏与前后噪音）。"""
    text = (text or "").strip()
    if text.startswith("```"):
        # 去掉 ```json ... ``` 围栏
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"输出中未找到 JSON 对象: {text[:200]}")
    return json.loads(text[start : end + 1])


def dedupe_sources(sources: list[dict], new_items: list[dict]) -> list[dict]:
    """按 URL 去重合并来源列表，返回新增项。"""
    seen = {s.get("url") for s in sources if s.get("url")}
    added: list[dict] = []
    for item in new_items:
        url = item.get("url")
        if url:
            if url in seen:
                continue
            seen.add(url)
        added.append(item)
    return added


def append_unique_sources(sources: list[dict], new_items: list[dict]) -> tuple[list[dict], list[dict]]:
    """合并来源并返回 (新列表, 新增项)。"""
    added = dedupe_sources(sources, new_items)
    return sources + added, added
