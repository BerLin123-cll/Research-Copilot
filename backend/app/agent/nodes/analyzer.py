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
        lines.append(f"[{i}] ({r.get('type', 'unknown')}) {title}\n    {snippet}")
    return "\n".join(lines)


def make_analyzer(ctx) -> object:
    """返回 analyzer 节点。ctx 提供 task_id / session / bus。"""

    async def analyzer(state: ResearchState) -> dict:
        bus: EventBus = event_bus
        task_id = state["task_id"]
        iteration = state.get("iterations", 1)
        max_iterations = state.get("max_iterations", 3)

        await bus.publish(task_id, EventBus.node_event("start", "analyzer"))
        await bus.publish(task_id, EventBus.status_event("running", "正在综合分析资料…"))

        results_text = _build_results_text(state.get("raw_results") or [])
        prompt = _PROMPT.format(
            topic=state["topic"],
            iteration=iteration,
            max_iterations=max_iterations,
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
