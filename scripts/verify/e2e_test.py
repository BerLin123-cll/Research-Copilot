"""End-to-end Agent flow test with stubbed LLM/tools and SQLite.

Verifies: planner -> searcher -> analyzer -> reporter, DB persistence,
report creation. Run: python scripts\\verify\\e2e_test.py
"""
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = ROOT / "backend"
STUBS = ROOT / "scripts" / "verify" / "stubs"
VERIFY = ROOT / "scripts" / "verify"

# 必须在导入 app 之前设置环境（config 使用 lru_cache）
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///" + str(VERIFY / "e2e.db").replace("\\", "/")
os.environ["SYNC_DATABASE_URL"] = "sqlite:///" + str(VERIFY / "e2e.db").replace("\\", "/")
os.environ["SAVE_RESEARCH_TO_KB"] = "false"

sys.path.insert(0, str(STUBS))
sys.path.insert(0, str(BACKEND))


async def fake_chat(messages, json_mode=False, temperature=None, max_tokens=None):
    content = messages[-1]["content"] if messages else ""
    if "研究规划专家" in content:
        return '{"plan": ["调研现状", "对比分析"], "search_queries": ["测试查询A", "测试查询B"]}'
    if "研究分析专家" in content:
        return '{"information_sufficient": true, "synthesized_info": "综合提炼：RAG 相关要点。", "missing_points": [], "next_queries": []}'
    if "研究报告撰写专家" in content:
        return "# 测试报告\n\n## 概述\n\n这是端到端测试生成的报告内容。\n\n## 参考资料\n\n[1] 来源示例"
    return "{}"


async def fake_web_search(query, max_results=None):
    return [{"title": "测试网页", "url": "https://example.com", "snippet": "测试摘要" * 10}]


async def fake_arxiv(query, max_results=None, sort_by="relevance"):
    return []


async def fake_fetch(url):
    return {"url": url, "title": "测试页", "content": "网页正文内容。" * 20}


async def main() -> None:
    # 清理上次运行遗留的 SQLite 文件（避免主键重复/旧 schema 干扰）
    db_path = VERIFY / "e2e.db"
    if db_path.exists():
        db_path.unlink()

    from app.core.database import init_db
    from app.core.llm_client import llm
    from app.models.report import Report
    from app.models.research import ResearchTask
    from app.services.research_service import run_research_in_background
    from app.tools import arxiv_search, web_fetch, web_search

    # 打桩：LLM 与网络工具
    llm.chat = fake_chat  # type: ignore[method-assign]
    web_search.web_search = fake_web_search  # type: ignore[assignment]
    arxiv_search.arxiv_search = fake_arxiv  # type: ignore[assignment]
    web_fetch.fetch_webpage = fake_fetch  # type: ignore[assignment]

    await init_db()

    # 与真实 API 流程一致：先创建任务，再后台执行
    from app.core.database import SessionLocal

    task_id = "e2e-task-001"
    async with SessionLocal() as session:
        session.add(ResearchTask(id=task_id, topic="RAG 技术端到端测试", status="pending"))
        await session.commit()

    await run_research_in_background(task_id, "RAG 技术端到端测试")

    async with SessionLocal() as session:
        task = await session.get(ResearchTask, task_id)
        assert task is not None, "任务未创建"
        assert task.status == "completed", f"任务状态异常: {task.status} error={task.error}"
        assert task.plan == ["调研现状", "对比分析"], task.plan
        assert len(task.sources) >= 1, "来源未收集"
        assert task.report_id, "report_id 未关联"
        report = await session.get(Report, task.report_id)
        assert report is not None, "报告未落库"
        assert "测试报告" in report.content, report.content[:100]
        print(f"task: {task.status} | sources={len(task.sources)} | report_id={report.id[:8]}")
        print(f"report title: {report.title} | content len: {len(report.content)}")
    print("E2E_OK - full agent flow (planner->searcher->analyzer->reporter) passed")


if __name__ == "__main__":
    asyncio.run(main())
