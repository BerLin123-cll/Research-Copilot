"""Agent 状态定义（LangGraph State）。"""
from typing import Any, TypedDict


class ResearchState(TypedDict, total=False):
    topic: str                 # 研究主题
    task_id: str               # 关联的研究任务 ID
    researchable: bool         # 话题质量闸门：是否适合深度研究（planner 判定）
    rejection_reason: str      # 话题闸门拒绝原因（不可研究时）
    plan: list[str]            # 研究计划步骤
    current_step: int          # 当前执行步骤
    search_queries: list[str]  # 搜索查询（分析后可补充）
    raw_results: list[dict]    # 原始搜索结果
    synthesized_info: str      # 综合分析信息
    report: str                # 最终报告
    sources: list[dict]        # 引用来源
    info_sufficient: bool      # 信息是否足够
    iterations: int            # 当前搜索迭代轮数
    max_iterations: int        # 最大搜索迭代轮数
    last_round_new_count: int  # 上一轮实际新增的资料条数（防空转）
    kb_chunks_saved: int       # 已写入知识库的分块数
    error: str | None          # 错误信息
