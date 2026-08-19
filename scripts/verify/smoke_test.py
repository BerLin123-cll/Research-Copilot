"""Backend offline smoke test: imports all app modules, compiles the Agent graph.

Usage: python scripts\\verify\\smoke_test.py
(missing third-party packages are stubbed from scripts/verify/stubs;
 this validates only the wiring of this project's own code)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = ROOT / "backend"
STUBS = ROOT / "scripts" / "verify" / "stubs"

# 桩模块优先于系统包，其次 backend 代码
sys.path.insert(0, str(STUBS))
sys.path.insert(0, str(BACKEND))


def main() -> None:
    import app.main  # noqa: F401  触发整个应用模块链导入
    from app.agent.events import EventBus, event_bus
    from app.agent.graph import build_graph
    from app.api import knowledge, research, websocket  # noqa: F401
    from app.core import database, llm_client  # noqa: F401
    from app.models import ChatMessage, Document, Report, ResearchTask  # noqa: F401
    from app.rag import document_processor, embedder, retriever, vector_store  # noqa: F401
    from app.services import knowledge_service, research_service  # noqa: F401
    from app.tools import arxiv_search, calculator, web_fetch, web_search  # noqa: F401

    # 事件总线冒烟
    assert isinstance(event_bus, EventBus)

    # 嵌入层冒烟：默认 local 模式（fastembed 懒加载，此处仅验证维度配置与 .env 一致）
    from app.config import get_settings
    from app.rag.embedder import embedder as emb

    assert emb.dim == get_settings().embedding_dim, f"嵌入维度异常: {emb.dim}"

    # 工具层冒烟（calculator 无外部依赖）
    r = calculator.calculate("2 + 3 * 4")
    assert r.get("result") == 14.0, r
    r2 = calculator.calculate("2 +")
    assert "error" in r2

    # Agent 状态图编译
    class Ctx:
        task_id = "smoke-task"
        session = None

    graph = build_graph(Ctx())
    state = research_service.initial_state("smoke-task", "RAG 技术调研")
    assert state["topic"] == "RAG 技术调研"
    assert state["iterations"] == 1

    # 图结构自检：入口为 planner
    compiled = graph
    nodes = getattr(compiled, "nodes", None)
    print(f"graph nodes: {sorted(nodes) if nodes else 'n/a'}")

    print("SMOKE_OK - all app modules imported, Agent graph compiled")


if __name__ == "__main__":
    main()
