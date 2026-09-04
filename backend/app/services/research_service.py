"""研究任务编排服务：创建任务、后台执行 Agent 图、持久化。

并发控制：
- 全局信号量限制同时运行的任务数（超出排队等待，状态保持 pending）；
- 整图执行有看门狗超时（AGENT_TASK_TIMEOUT），超时标记 failed；
- 维护 task_id → asyncio.Task 注册表，支持外部取消（cancel_research）。
"""
import asyncio
import logging

from app.agent.events import event_bus
from app.agent.graph import build_graph
from app.agent.state import ResearchState
from app.config import get_settings
from app.core.database import SessionLocal
from app.models.research import ResearchTask

logger = logging.getLogger(__name__)

# 全局并发信号量：同时运行的研究任务上限（超出排队等待）
_research_sem: asyncio.Semaphore | None = None

# 运行中/排队中的任务注册表：task_id -> asyncio.Task（用于取消）
_running_tasks: dict[str, asyncio.Task] = {}


def _get_semaphore() -> asyncio.Semaphore:
    global _research_sem
    if _research_sem is None:
        _research_sem = asyncio.Semaphore(get_settings().max_concurrent_research)
    return _research_sem


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
        "researchable": True,
        "rejection_reason": "",
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
        "last_round_new_count": 0,
        "kb_chunks_saved": 0,
        "error": None,
    }


async def run_research_in_background(task_id: str, topic: str) -> None:
    """后台执行完整研究流程（planner → searcher ⇄ analyzer → reporter）。"""
    ctx = RunContext(task_id)
    s = get_settings()
    try:
        async with _get_semaphore():
            async with SessionLocal() as session:
                ctx.session = session
                graph = build_graph(ctx)
                await asyncio.wait_for(
                    graph.ainvoke(initial_state(task_id, topic)),
                    timeout=s.agent_task_timeout,
                )
    except asyncio.CancelledError:
        # 用户取消（可能在排队等待信号量期间，也可能在执行期间）
        logger.info("研究任务 %s 已被取消", task_id)
        await _mark_cancelled(task_id)
        await event_bus.publish(task_id, {"type": "cancelled", "task_id": task_id})
        await event_bus.publish(task_id, {"type": "done", "task_id": task_id})
        raise
    except asyncio.TimeoutError:
        logger.error("研究任务 %s 执行超时（>%ss）", task_id, s.agent_task_timeout)
        await _mark_failed(task_id, f"研究任务执行超时（超过 {s.agent_task_timeout} 秒）")
        await event_bus.publish(task_id, {"type": "error", "message": "研究任务执行超时"})
        await event_bus.publish(task_id, {"type": "done", "task_id": task_id})
    except Exception as e:  # noqa: BLE001
        logger.exception("研究任务 %s 执行失败", task_id)
        await _mark_failed(task_id, str(e))
        await event_bus.publish(task_id, {"type": "error", "message": str(e)})
        await event_bus.publish(task_id, {"type": "done", "task_id": task_id})


async def _mark_failed(task_id: str, error: str) -> None:
    async with SessionLocal() as session:
        task = await session.get(ResearchTask, task_id)
        if task and task.status not in ("completed", "cancelled"):
            task.status = "failed"
            task.error = error[:2000]
            await session.commit()


async def _mark_cancelled(task_id: str) -> None:
    async with SessionLocal() as session:
        task = await session.get(ResearchTask, task_id)
        if task and task.status not in ("completed", "failed"):
            task.status = "cancelled"
            await session.commit()


def get_running_task(task_id: str) -> asyncio.Task | None:
    """返回任务对应的 asyncio.Task（运行中或排队中）。"""
    return _running_tasks.get(task_id)


def cancel_research(task_id: str) -> bool:
    """发起取消：返回是否成功取消（注册表中存在且未完成）。"""
    t = _running_tasks.get(task_id)
    if t and not t.done():
        t.cancel()
        return True
    return False


def schedule_research(task: ResearchTask) -> None:
    """在事件循环中调度后台任务（FastAPI 生命周期内有效）。"""
    t = asyncio.create_task(run_research_in_background(task.id, task.topic))
    _running_tasks[task.id] = t
    t.add_done_callback(lambda _: _running_tasks.pop(task.id, None))
