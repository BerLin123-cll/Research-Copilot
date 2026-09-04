"""报告节点：基于综合分析信息生成结构化 Markdown 报告并落库。"""
import logging

from app.agent.events import EventBus, event_bus
from app.agent.nodes.utils import load_prompt
from app.agent.state import ResearchState
from app.core.llm_client import llm
from app.models.report import Report
from app.models.research import ResearchTask

logger = logging.getLogger(__name__)

_PROMPT = load_prompt("reporter_prompt.txt")


def _format_sources(sources: list[dict]) -> str:
    lines = []
    for i, s in enumerate(sources, start=1):
        published = s.get("published") or ""
        date_part = f"（{published[:10]}）" if published else ""
        lines.append(f"[{i}] {s.get('title', '')} — {s.get('url', '')}{date_part}")
    return "\n".join(lines) or "（无）"


def make_reporter(ctx) -> object:
    """返回 reporter 节点。ctx 提供 task_id / session / bus。"""

    async def reporter(state: ResearchState) -> dict:
        bus: EventBus = event_bus
        task_id = state["task_id"]

        await bus.publish(task_id, EventBus.node_event("start", "reporter"))
        await bus.publish(task_id, EventBus.status_event("running", "正在撰写研究报告…"))

        sources = state.get("sources") or []
        synthesized = state.get("synthesized_info") or ""
        prompt = _PROMPT.format(
            topic=state["topic"],
            synthesized_info=synthesized,
            sources=_format_sources(sources),
        )

        try:
            report_content = (await llm.chat([{"role": "user", "content": prompt}])).strip()
        except Exception as e:  # noqa: BLE001
            logger.error("报告生成失败: %s", e)
            report_content = (
                f"# {state['topic']}\n\n"
                f"> 报告生成失败（{e}），以下是已收集资料：\n\n"
                f"## 综合信息\n\n{synthesized}"
            )

        summary = report_content.split("\n\n")[0][:200] if report_content else ""

        # 落库
        report = Report(task_id=task_id, title=state["topic"], content=report_content, summary=summary)
        ctx.session.add(report)
        await ctx.session.commit()
        await ctx.session.refresh(report)

        task = await ctx.session.get(ResearchTask, task_id)
        if task:
            task.report_id = report.id
            task.status = "completed"
            await ctx.session.commit()

        await bus.publish(task_id, {"type": "report_ready", "report_id": report.id})
        await bus.publish(task_id, EventBus.node_event("end", "reporter"))
        await bus.publish(task_id, {"type": "done", "task_id": task_id})
        return {"report": report_content, "report_id": report.id}

    return reporter
