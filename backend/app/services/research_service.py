"""研究任务编排服务：创建任务、后台执行 Agent 图、持久化。"""
import asyncio
import logging

from app.agent.events import event_bus
from app.agent.graph import build_graph
from app.agent.state import ResearchState
from app.config import get_settings
from app.core.database import SessionLocal
from app.models.research import ResearchTask

logger = logging.getLogger(__name__)


class RunContext:
    """Agent 图运行期上下文：任务 ID + 共享数据库会话。"""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        self.session = None  # 由 run_research_in_background 注入


def initial_state(task_id: str, topic: str) -> ResearchState:
    s = get_settings()
    return {
        "topic": topic,
        "task_id": task_id,
        "plan": [],
        "current_step": 0,
        "search_queries": [],
        "raw_results": [],
        "synthesized_info": "",
        "report": "",
        "sources": [],
        "info_sufficient": False,
        "iterations": 1,
        "max_iterations": s.agent_max_iterations,
        "kb_chunks_saved": 0,
        "error": None,
    }


async def run_research_in_background(task_id: str, topic: str) -> None:
    """后台执行完整研究流程（planner → searcher ⇄ analyzer → reporter）。"""
    ctx = RunContext(task_id)
    try:
        async with SessionLocal() as session:
            ctx.session = session
            graph = build_graph(ctx)
            await graph.ainvoke(initial_state(task_id, topic))
    except Exception as e:  # noqa: BLE001
        logger.exception("研究任务 %s 执行失败", task_id)
        await _mark_failed(task_id, str(e))
        await event_bus.publish(task_id, {"type": "error", "message": str(e)})
        await event_bus.publish(task_id, {"type": "done", "task_id": task_id})


async def _mark_failed(task_id: str, error: str) -> None:
    async with SessionLocal() as session:
        task = await session.get(ResearchTask, task_id)
        if task:
            task.status = "failed"
            task.error = error[:2000]
            await session.commit()


async def schedule_research(task: ResearchTask) -> None:
    """在事件循环中调度后台任务（FastAPI 生命周期内有效）。"""
    asyncio.create_task(run_research_in_background(task.id, task.topic))
