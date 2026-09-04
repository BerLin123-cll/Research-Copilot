"""分析节点：综合已有资料，判断信息是否足够并给出提炼。"""
import logging

from app.agent.events import EventBus, event_bus
from app.agent.nodes.utils import extract_json, load_prompt
from app.agent.state import ResearchState
from app.core.llm_client import llm

logger = logging.getLogger(__name__)

_PROMPT = load_prompt("analyzer_prompt.txt")

# 传给 LLM 的资料上下文上限（避免超出 token）
_MAX_RESULTS_FOR_LLM = 40


def _build_results_text(raw_results: list[dict]) -> str:
    lines = []
    for i, r in enumerate(raw_results[: _MAX_RESULTS_FOR_LLM], start=1):
        title = r.get("title") or r.get("url") or ""
        snippet = r.get("snippet") or r.get("content", "")[:300]
        published = r.get("published") or ""
        date_part = f", {published[:10]}" if published else ""
        lines.append(f"[{i}] ({r.get('type', 'unknown')}{date_part}) {title}\n    {snippet}")
    return "\n".join(lines)


def _is_new_query(query: str, prev_queries: list[str]) -> bool:
    """判断查询是否与已有查询重复（归一化完全相等，或一方被另一方包含）。"""
    q = (query or "").strip().lower()
    if not q:
        return False
    for p in prev_queries:
        pn = (p or "").strip().lower()
        if not pn:
            continue
        if q == pn:
            return False
        # 长查询间互相包含视为近似重复（如"2025 最新进展" vs "最新进展 2025"）
        if len(q) >= 4 and q in pn:
            return False
        if len(pn) >= 4 and pn in q:
            return False
    return True


def make_analyzer(ctx) -> object:
    """返回 analyzer 节点。ctx 提供 task_id / session / bus。"""

    async def analyzer(state: ResearchState) -> dict:
        bus: EventBus = event_bus
        task_id = state["task_id"]
        iteration = state.get("iterations", 1)
        max_iterations = state.get("max_iterations", 3)
        new_count = state.get("last_round_new_count", 0)

        await bus.publish(task_id, EventBus.node_event("start", "analyzer"))
        await bus.publish(task_id, EventBus.status_event("running", "正在综合分析资料…"))

        results_text = _build_results_text(state.get("raw_results") or [])
        prompt = _PROMPT.format(
            topic=state["topic"],
            iteration=iteration,
            max_iterations=max_iterations,
            new_count=new_count,
            results=results_text or "（无资料）",
        )

        try:
            raw = await llm.chat([{"role": "user", "content": prompt}], json_mode=True)
            data = extract_json(raw)
            info_sufficient = bool(data.get("information_sufficient", True))
            synthesized = str(data.get("synthesized_info", "")).strip()
            missing = [str(x) for x in data.get("missing_points", [])][:5]
            next_queries = [str(q) for q in data.get("next_queries", [])][:5]
        except Exception as e:  # noqa: BLE001
            logger.warning("分析节点 LLM 失败，默认信息足够: %s", e)
            info_sufficient = True
            synthesized = results_text[:2000]
            missing, next_queries = [], []

        # 已达最大迭代时强制进入报告阶段
        if iteration >= max_iterations:
            info_sufficient = True

        # 防空转：连续空轮（本轮无新增资料且已搜过 ≥2 轮）→ 强制进入报告
        if new_count == 0 and iteration >= 2:
            info_sufficient = True

        # 查询去重：过滤掉与已有查询重复的下一轮查询；去重后无新查询 → 强制报告
        if not info_sufficient:
            prev_queries = [str(q) for q in (state.get("search_queries") or [])]
            next_queries = [q for q in next_queries if _is_new_query(q, prev_queries)]
            if not next_queries:
                info_sufficient = True

        await bus.publish(
            task_id,
            {"type": "analysis", "information_sufficient": info_sufficient, "synthesized_info": synthesized[:500]},
        )
        await bus.publish(task_id, EventBus.node_event("end", "analyzer"))
        return {
            "info_sufficient": info_sufficient,
            "synthesized_info": synthesized,
            "search_queries": next_queries if not info_sufficient else [],
            "iterations": iteration + 1,
        }

    return analyzer
