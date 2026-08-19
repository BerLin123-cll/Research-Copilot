"""条件边：决定 Agent 下一步走向（继续搜索 or 生成报告）。"""
from app.agent.state import ResearchState


def should_continue(state: ResearchState) -> str:
    """analyzer 之后的路由：
    - 信息已足够 → reporter
    - 已达最大迭代轮数 → reporter
    - 否则 → searcher（用分析器给出的下一轮查询继续搜集）
    """
    if state.get("info_sufficient", False):
        return "reporter"
    if state.get("iterations", 1) > state.get("max_iterations", 3):
        return "reporter"
    return "searcher"
