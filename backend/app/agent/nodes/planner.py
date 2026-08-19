"""规划节点：将研究主题分解为计划步骤与搜索查询。"""
import logging

from app.agent.events import EventBus, event_bus
from app.agent.nodes.utils import extract_json, load_prompt
from app.agent.state import ResearchState
from app.core.llm_client import llm
from app.models.research import ResearchTask

logger = logging.getLogger(__name__)

_PROMPT = load_prompt("planner_prompt.txt")

_FALLBACK_PLAN = (
    "调研 {topic} 的现状与核心内容",
    "收集 {topic} 的对比案例与关键数据",
    "综合分析并形成结论与建议",
)


def make_planner(ctx) -> object:
    """返回 planner 节点。ctx 提供 task_id / session / bus。"""

    async def planner(state: ResearchState) -> dict:
        bus: EventBus = event_bus
        task_id = state["task_id"]
        await bus.publish(task_id, EventBus.node_event("start", "planner"))
        await bus.publish(task_id, EventBus.status_event("running", "正在规划研究路径…"))

        try:
            raw = await llm.chat(
                [{"role": "user", "content": _PROMPT.format(topic=state["topic"])}],
                json_mode=True,
            )
            data = extract_json(raw)
            plan = [str(x) for x in data.get("plan", [])][:8]
            queries = [str(q) for q in data.get("search_queries", [])][:8]
            if not plan:
                plan = [p.format(topic=state["topic"]) for p in _FALLBACK_PLAN]
            if not queries:
                queries = [state["topic"]]
        except Exception as e:  # noqa: BLE001
            logger.warning("规划节点 LLM 失败，使用兜底方案: %s", e)
            plan = [p.format(topic=state["topic"]) for p in _FALLBACK_PLAN]
            queries = [state["topic"]]

        # 持久化计划
        task = await ctx.session.get(ResearchTask, task_id)
        if task:
            task.plan = plan
            task.search_queries = queries
            task.status = "running"
            await ctx.session.commit()

        await bus.publish(task_id, {"type": "plan", "steps": plan})
        await bus.publish(task_id, EventBus.node_event("end", "planner"))
        return {"plan": plan, "search_queries": queries, "current_step": 0}

    return planner
