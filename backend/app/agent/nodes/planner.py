"""规划节点：先判定话题是否适合深度研究，再将主题分解为计划步骤与搜索查询。"""
import logging

from app.agent.events import EventBus, event_bus
from app.agent.nodes.utils import extract_json, load_prompt
from app.agent.state import ResearchState
from app.core.llm_client import llm
from app.models.report import Report
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

    async def _reject(task_id: str, reason: str) -> dict:
        """话题闸门：不适合深度研究 → 友好拒绝并说明，任务直接完成。"""
        bus: EventBus = event_bus
        content = (
            f"# 无法研究\n\n"
            f"> 该输入不适合作为深度研究主题，已为你跳过搜索流程，避免浪费时间。\n\n"
            f"## 原因\n\n{reason}\n\n"
            f"## 建议\n\n"
            f"请尝试输入一个具体的、可系统调研的议题，例如：\n"
            f"- 大语言模型检索增强生成（RAG）的最新进展\n"
            f"- 2025 年国内新能源汽车市场格局\n"
            f"- 联邦学习在医疗领域的应用案例"
        )
        summary = reason[:200]
        await bus.publish(task_id, {"type": "rejection", "reason": reason})
        await bus.publish(task_id, EventBus.status_event("running", "正在生成说明…"))
        report = Report(task_id=task_id, title="（非研究类输入）", content=content, summary=summary)
        ctx.session.add(report)
        await ctx.session.commit()
        await ctx.session.refresh(report)
        task = await ctx.session.get(ResearchTask, task_id)
        if task:
            task.report_id = report.id
            task.status = "completed"
            task.plan = []
            task.search_queries = []
            await ctx.session.commit()
        await bus.publish(task_id, {"type": "report_ready", "report_id": report.id})
        await bus.publish(task_id, EventBus.node_event("end", "planner"))
        await bus.publish(task_id, {"type": "done", "task_id": task_id})
        return {"researchable": False, "rejection_reason": reason}

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
            researchable = bool(data.get("researchable", True))
            if not researchable:
                reason = str(data.get("rejection_reason") or "该输入不适合作为深度研究主题").strip()
                return await _reject(task_id, reason)
            plan = [str(x) for x in data.get("plan", [])][:8]
            queries = [str(q) for q in data.get("search_queries", [])][:8]
            if not plan:
                plan = [p.format(topic=state["topic"]) for p in _FALLBACK_PLAN]
            if not queries:
                queries = [state["topic"]]
        except Exception as e:  # noqa: BLE001
            # LLM 判定失败时按"可研究"处理，使用兜底方案（不误伤正常主题）
            logger.warning("规划节点 LLM 失败，使用兜底方案: %s", e)
            researchable = True
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
        return {
            "researchable": True,
            "plan": plan,
            "search_queries": queries,
            "current_step": 0,
        }

    return planner
