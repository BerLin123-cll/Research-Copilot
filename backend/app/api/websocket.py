"""WebSocket 实时推送：Agent 执行事件流。"""
import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agent.events import event_bus
from app.core.database import SessionLocal
from app.models.research import ResearchTask

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# 终止类事件：收到后服务端关闭连接，队列随 unsubscribe 清理，避免残留订阅
_TERMINAL_EVENTS = {"done", "error", "cancelled"}


@router.websocket("/ws/research/{task_id}")
async def ws_research(websocket: WebSocket, task_id: str):
    """订阅任务事件流：先推当前快照，再实时推送 Agent 事件。"""
    await websocket.accept()

    # 推送任务当前状态快照（弥补订阅前已发生的事件）
    try:
        async with SessionLocal() as session:
            task = await session.get(ResearchTask, task_id)
            if task:
                await websocket.send_json({"type": "snapshot", "task": task.to_dict()})
    except Exception as e:  # noqa: BLE001
        logger.warning("WebSocket 快照推送失败: %s", e)

    queue = await event_bus.subscribe(task_id)
    try:
        while True:
            event = await queue.get()
            try:
                await websocket.send_json(event)
                # 任务已结束（done/error/cancelled）→ 主动关闭连接
                if event.get("type") in _TERMINAL_EVENTS:
                    break
            except WebSocketDisconnect:
                break
    except asyncio.CancelledError:
        raise
    except WebSocketDisconnect:
        pass
    except Exception as e:  # noqa: BLE001
        logger.debug("WebSocket 连接异常结束: %s", e)
    finally:
        await event_bus.unsubscribe(task_id, queue)
