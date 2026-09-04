# 架构设计文档

## 1. 系统总览

智研助手（Research Copilot）是一个个人智能研究 Agent：用户输入研究主题，后端 Agent 自主规划、多工具收集信息、综合分析并生成结构化 Markdown 报告；前端实时展示 Agent 思考过程（时间线 + 工具调用），并附带基于 RAG 的知识库问答能力。

```
┌────────────────────────────────────────────────────────────┐
│ 前端层 React 19 + TS + Tailwind (Vite)                       │
│  研究任务面板 / 实时执行时间线 / 报告查看 / 知识库管理 / RAG 问答 │
└──────────────────────────┬─────────────────────────────────┘
                           │ REST API (JSON) / WebSocket (事件流)
┌──────────────────────────▼─────────────────────────────────┐
│ 后端服务层 FastAPI (Uvicorn, async)                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Agent 核心 (LangGraph)                                │  │
│  │  planner → searcher ⇄ analyzer → reporter            │  │
│  │  （analyzer 判定信息不足则条件边回环到 searcher）        │  │
│  └──────────────┬──────────────────────────┬────────────┘  │
│  工具层          │ RAG 检索                   │ 数据层        │
│  web_search     │ embedder / retriever      │ PostgreSQL    │
│  arxiv_search   │ vector_store (pgvector)   │ 任务/报告/文档 │
│  web_fetch      │ document_processor        │ 向量分块(同库) │
│  calculator     │                           │ 聊天记录       │
└─────────────────┴───────────────────────────┴───────────────┘
```

## 2. 核心流程：Agent 状态图

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ planner │───▶│ searcher│───▶│analyzer │───▶│ reporter│───▶ END
└─────────┘    └─────────┘    └────┬────┘    └─────────┘
                                   │ 信息不足 && 未达迭代上限
                                   └──────────▶ searcher（下一轮查询）
```

- **planner**：LLM（JSON mode）先判定话题是否适合深度研究（话题闸门），不适合时直接产出说明性结果并结束任务（发布 `rejection` 事件），不进入搜索；适合时分解为计划步骤与搜索查询，失败时使用兜底方案。
- **searcher**：对每条查询执行 `web_search`（DuckDuckGo）+ `arxiv_search`（arXiv）+ 预算内 `fetch_webpage`；结果按 URL 去重进入 `sources`；研究资料（可选）分块向量化写入 pgvector（`source_type="research"`），供后续深度问答；返回本轮新增资料数供 analyzer 防空转。
- **analyzer**：LLM 综合已有资料，判断 `information_sufficient`，输出综合提炼与（不足时的）下一轮查询；下一轮查询与已有查询去重，去重后为空则强制进入报告；达到 `AGENT_MAX_ITERATIONS` 或连续空轮（≥2 轮无新增资料）时强制进入报告阶段。
- **reporter**：LLM 生成结构化 Markdown 报告，包含"信息时效性说明"小节（资料时间跨度 / 信息截止日期），落库 `reports` 表并关联任务；发布 `report_ready` / `done` 事件。

## 3. 实时事件流（WebSocket，无 Redis）

采用**进程内内存事件总线**（`app/agent/events.py`）：

- 每个研究任务维护一个订阅队列列表（`task_id → [asyncio.Queue]`）。
- Agent 节点在执行中发布事件：`status` / `plan` / `node_start` / `node_end` / `tool_call` / `tool_result` / `analysis` / `report_ready` / `error` / `done`。
- 前端 `GET /ws/research/{task_id}` 先收到 `snapshot`（当前任务状态），随后实时收到事件流。
- 单机部署下无需 Redis/Celery；任务在进程内以 `asyncio.create_task` 后台执行。
- **扩展点**：若未来需要多实例横向扩展，可将事件总线替换为 Redis Pub/Sub，Agent 编排迁移到 Celery/任务队列，接口与事件契约无需改动。

## 4. 数据模型

| 表 | 说明 | 关键字段 |
|---|---|---|
| `research_tasks` | 研究任务 | topic, status, plan(JSON), search_queries(JSON), sources(JSON), report_id, error |
| `reports` | 研究报告 | task_id, title, content(Markdown), summary |
| `documents` | 知识库文档 | filename, source_type(upload/url), status, chunk_count, meta |
| `document_chunks` | 向量分块（pgvector） | document_id, chunk, embedding(vector), meta |
| `chat_messages` | 知识库问答记录 | session_id, role, content, citations(JSON) |

## 5. RAG 知识库

- **入库**：上传文件（PDF/MD/TXT/HTML）或网页 URL → `document_processor` 解析 → `RecursiveCharacterTextSplitter`（chunk_size=512, overlap=50）→ Embedding → PostgreSQL（pgvector, cosine）。
- **检索**：问题向量化 → pgvector 余弦距离 Top-K（默认 5）→ 可选按文档过滤；`retriever.rerank` 为 cross-encoder 重排序扩展点（默认不启用）。
- **研究资料自动入库**：`SAVE_RESEARCH_TO_KB=true` 时，研究过程中抓取的网页/论文摘要分块入库（`source_type="research"`），上限 `RESEARCH_KB_MAX_CHUNKS=30`。
- **Embedding 默认本地化**：`EMBEDDING_PROVIDER=local` 使用 fastembed + BAAI/bge-small-zh-v1.5（开源免费、ONNX、免 GPU、免 Key）；`openai` 模式可切 OpenAI 兼容 API。表结构维度 = `EMBEDDING_DIM`，换模型需同步修改并重建向量表。
- **向量库 = pgvector（免费开源）**：向量随业务数据同库存储于 PostgreSQL，`document_chunks` 表 + HNSW 余弦索引由 alembic 迁移/启动初始化自动创建；Docker 部署使用 `pgvector/pgvector:pg16` 镜像，无需独立向量库服务。

## 6. 设计决策记录

| 决策 | 说明 |
|---|---|
| 不使用 Redis/Celery | 单机个人项目，asyncio 后台任务 + 内存事件总线已足够；保留迁移路径 |
| SQLModel → SQLAlchemy 2.0 async | 异步场景更稳、生态成熟；Pydantic v2 负责 schema |
| LLM 为 OpenAI 兼容 | 通过 env 切换 DeepSeek / OpenAI / 其他网关 |
| Embedding 本地开源优先 | fastembed + bge 系列，零成本免 Key；保留 OpenAI 兼容模式作为备选 |
| 向量库 = pgvector（PostgreSQL 扩展） | 免费开源、与业务数据同库（单库运维），HNSW 索引加速检索；无需独立向量库服务 |
| 数据库统一 PostgreSQL | 业务表 + 向量表同库，备份/迁移只关心一个数据库 |
| 研究原始结果不进表 | `raw_results` 仅存在于图状态（内存），持久化的是去重后的 `sources`，避免膨胀 |
| 网页抓取 httpx 为主 | Playwright 作为可选依赖，默认关闭 |
| nginx 配置并入前端镜像 | 保持 docker build 上下文精简（原文档 docker/nginx.conf 的位置调整） |

## 7. 健壮性设计（话题闸门 / 新鲜度 / 并发防护）

| 关注点 | 机制 |
|---|---|
| 非研究话题死循环 | planner 话题闸门：`researchable=false` 直接产出说明性结果结束任务，不进入搜索；图本身有 `AGENT_MAX_ITERATIONS`（默认 3）硬上限，迭代计数严格递增，必然终止 |
| 搜索内容过旧 | `WEB_SEARCH_TIMELIMIT`（DDG 时间过滤，默认不限）、`ARXIV_SORT_BY` 可配；网页抓取解析发布日期并贯穿 sources/analyzer/reporter；analyzer 优先采信近期资料；报告输出"信息时效性说明"；planner 对时效主题自动加时间限定词 |
| 多任务并发互相干扰 | `MAX_CONCURRENT_RESEARCH`（默认 3）全局信号量排队；`WEB_SEARCH_MAX_CONCURRENCY`（默认 2）限制 DDG 并发防限流；任务间状态/会话/事件总线按 task_id 隔离 |
| 任务卡死 | `AGENT_TASK_TIMEOUT`（默认 900s）整图看门狗；`LLM_TIMEOUT`（120s）+ 429/5xx 指数退避重试；`TOOL_TIMEOUT`（30s）保护同步阻塞工具；超时任务标记 failed 并发事件 |
| 任务取消 | `POST /api/research/{task_id}/cancel` + task 注册表，取消后标记 `cancelled`；DELETE 顺带取消 |
| 残留连接 | WebSocket 收到终止事件（done/error/cancelled）后主动关闭，事件队列随 unsubscribe 清理；前端收到终态快照/事件后断开连接 |
