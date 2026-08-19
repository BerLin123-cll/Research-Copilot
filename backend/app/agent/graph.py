"""LangGraph 状态图定义：规划 → 搜索 ⇄ 分析 → 报告。"""
import logging

from langgraph.graph import END, StateGraph

from app.agent.edges.conditional_edges import should_continue
from app.agent.nodes.analyzer import make_analyzer
from app.agent.nodes.planner import make_planner
from app.agent.nodes.reporter import make_reporter
from app.agent.nodes.searcher import make_searcher
from app.agent.state import ResearchState

logger = logging.getLogger(__name__)


def build_graph(ctx) -> object:
    """根据运行上下文构建并编译 Agent 状态图。

    ctx 提供运行期依赖：task_id / async session / event bus。
    """
    graph = StateGraph(ResearchState)
    graph.add_node("planner", make_planner(ctx))
    graph.add_node("searcher", make_searcher(ctx))
    graph.add_node("analyzer", make_analyzer(ctx))
    graph.add_node("reporter", make_reporter(ctx))

    graph.set_entry_point("planner")
    graph.add_edge("planner", "searcher")
    graph.add_edge("searcher", "analyzer")
    graph.add_conditional_edges(
        "analyzer",
        should_continue,
        {"searcher": "searcher", "reporter": "reporter"},
    )
    graph.add_edge("reporter", END)
    return graph.compile()
