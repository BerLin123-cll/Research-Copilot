"""Agent 执行事件总线：任务 → WebSocket 流式推送（进程内内存实现，无 Redis）。"""
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

Event = dict


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EventBus:
    """内存事件总线：每个任务维护多个订阅队列，事件广播给所有订阅者。"""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, task_id: str) -> asyncio.Queue:
        """订阅任务事件流，返回队列（阻塞读取）。"""
        q: asyncio.Queue = asyncio.Queue(maxsize=1000)
        async with self._lock:
            self._subscribers.setdefault(task_id, []).append(q)
        return q

    async def unsubscribe(self, task_id: str, q: asyncio.Queue) -> None:
        async with self._lock:
            subs = self._subscribers.get(task_id)
            if subs:
                try:
                    subs.remove(q)
                except ValueError:
                    pass
                if not subs:
                    self._subscribers.pop(task_id, None)

    async def publish(self, task_id: str, event: Event) -> None:
        """广播事件给该任务的所有订阅者（队列满时丢弃，避免阻塞 Agent）。"""
        async with self._lock:
            subs = list(self._subscribers.get(task_id, []))
        for q in subs:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:  # pragma: no cover
                logger.warning("事件队列已满，丢弃事件: %s", event.get("type"))

    # ---- 便捷构造 ----
    @staticmethod
    def status_event(status: str, message: str = "") -> Event:
        return {"type": "status", "status": status, "message": message}

    @staticmethod
    def node_event(kind: str, node: str) -> Event:
        return {"type": f"node_{kind}", "node": node, "timestamp": now_iso()}

    @staticmethod
    def tool_call_event(tool: str, input_data: dict) -> Event:
        return {"type": "tool_call", "tool": tool, "input": input_data, "timestamp": now_iso()}

    @staticmethod
    def tool_result_event(tool: str, output: dict, success: bool = True) -> Event:
        return {
            "type": "tool_result",
            "tool": tool,
            "output": output,
            "success": success,
            "timestamp": now_iso(),
        }


event_bus = EventBus()
