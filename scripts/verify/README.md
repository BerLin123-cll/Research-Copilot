# 离线验证工具（scripts/verify）

这两个脚本用于在**不依赖完整第三方环境**的情况下验证后端代码接线正确性：
缺失的第三方包（fastapi / pgvector / arxiv）由 `stubs/` 中的最小桩模块替代，
真实已安装的依赖（langgraph / openai / sqlalchemy / pydantic 等）直接使用。

```bash
# 1) 模块导入 + Agent 状态图编译检查
python scripts/verify/smoke_test.py

# 2) 端到端 Agent 流程测试（桩 LLM/工具 + SQLite）
#    验证 planner → searcher → analyzer → reporter 全链路与报告落库
python scripts/verify/e2e_test.py
```

> 注意：`e2e_test.py` 会临时生成 `scripts/verify/e2e.db`（已 gitignore），运行后自动删除。
> 桩模块仅覆盖本项目自己的 import 接线，不能替代真实环境下的集成测试。
