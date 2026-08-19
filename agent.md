智研助手 (Research Copilot) —— 个人智能研究Agent

一个面向个人开发者、具备完整Agent技术栈的智能研究助手。用户只需输入研究主题，Agent自动规划研究路径、调用工具收集信息、通过RAG构建知识库，最终生成结构化研究报告。

一、项目概述
1.1 项目定位
智研助手是一个基于大语言模型（LLM）的智能研究Agent，旨在帮助用户高效完成主题研究。无论是技术调研、市场分析、学术论文综述还是竞品分析，用户只需输入一个研究主题，Agent即可自动完成信息收集、资料整理、深度分析和报告生成。
1.2 核心场景
表格
场景	示例
技术调研	"调研2026年前端状态管理方案，对比Zustand、Pinia、Redux Toolkit"
市场分析	"分析中国新能源汽车充电桩行业现状与头部企业"
学术综述	"梳理RAG技术在2024-2026年的最新进展与评估方法"
竞品分析	"对比Notion、Obsidian、Logseq的优缺点和适用人群"
1.3 项目亮点
全自动研究流程：从主题输入到报告输出，全程Agent自主规划与执行
多源信息融合：网络搜索 + 学术论文 + 网页抓取，信息来源丰富
RAG知识库：研究资料自动向量化存储，支持后续深度问答与关联分析
透明可追溯：前端实时展示Agent的思考过程（CoT）、工具调用记录和资料来源
个人开发者友好：架构清晰、依赖精简、部署简单，单台服务器即可运行
二、技术栈
2.1 整体架构
plain
┌─────────────────────────────────────────────────────────────────┐
│                        前端层 (React)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ 研究任务面板 │  │ 资料库浏览器 │  │ 实时Agent执行流展示      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST API / WebSocket
┌────────────────────────▼────────────────────────────────────────┐
│                      后端服务层 (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Agent核心 (LangGraph)                   │   │
│  │  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌───────────┐  │   │
│  │  │ 规划节点 │→│ 搜索节点  │→│ 分析节点 │→│ 报告节点   │  │   │
│  │  │(Planning)│  │(Searching)│  │(Analyzing)│  │(Reporting)│  │   │
│  │  └─────────┘  └──────────┘  └─────────┘  └───────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ 工具调用层   │  │ RAG检索引擎  │  │ 向量库 (pgvector)         │  │
│  │ - 网页搜索   │  │ - 文档分块   │  │ - PostgreSQL 扩展         │  │
│  │ - 论文搜索   │  │ - 语义检索   │  │ - 资料向量存储           │  │
│  │ - 网页抓取   │  │ - 重排序     │  │ - 元数据索引             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
2.2 技术选型详解
表格
层级	技术	选型理由
前端框架	React 19 + TypeScript	生态成熟、类型安全、组件化开发效率高
前端样式	Tailwind CSS + shadcn/ui	原子化CSS快速构建UI，shadcn提供高质量可复用组件
状态管理	Zustand	轻量、无样板代码，适合中等复杂度状态管理
实时通信	WebSocket	Agent执行过程流式推送到前端，展示思考链
后端框架	FastAPI (Python)	异步高性能、自动API文档、Python生态与AI库无缝衔接
Agent框架	LangGraph	支持循环、条件分支、状态持久化，适合构建复杂多步Agent
LLM接口	OpenAI API / 兼容接口	GPT-4o-mini 成本低效果好；可无缝切换 Claude、DeepSeek 等
Embedding	fastembed + BAAI/bge-small-zh-v1.5	开源免费本地模型、无需API Key、512维
向量数据库	PostgreSQL + pgvector	免费开源、与业务数据同库、HNSW余弦索引、Docker一键部署
文档处理	LangChain Document Loaders	支持PDF、Markdown、HTML、TXT等多种格式
网页搜索	DuckDuckGo API (via duckduckgo-search)	免费、无需API Key、中文支持好
论文搜索	arXiv API	免费、学术权威、支持按时间/领域筛选
网页抓取	Playwright / Jina AI Reader API	动态页面渲染，提取正文内容
任务队列	Celery + Redis (可选)	长时间研究任务异步执行，避免HTTP超时
数据库	PostgreSQL	存储研究任务、报告、用户配置等结构化数据
部署	Docker Compose	一键编排前后端、向量库、数据库，个人服务器即可运行
三、项目结构
plain
research-copilot/
├── 📁 frontend/                          # React 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── research/
│   │   │   │   ├── ResearchInput.tsx     # 研究主题输入框
│   │   │   │   ├── ResearchTimeline.tsx  # Agent执行时间线（核心交互）
│   │   │   │   ├── ToolCallCard.tsx      # 工具调用记录卡片
│   │   │   │   └── ReportViewer.tsx      # 研究报告渲染
│   │   │   ├── knowledge/
│   │   │   │   ├── DocumentUploader.tsx  # 资料上传组件
│   │   │   │   ├── DocumentList.tsx      # 资料列表
│   │   │   │   └── ChatWithDocs.tsx      # 基于RAG的资料问答
│   │   │   └── ui/                       # shadcn/ui 基础组件
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx             # 主控制台
│   │   │   ├── ResearchDetail.tsx        # 研究详情页
│   │   │   └── KnowledgeBase.tsx         # 知识库管理页
│   │   ├── stores/
│   │   │   └── researchStore.ts          # Zustand 状态管理
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts           # WebSocket 实时通信
│   │   │   └── useResearch.ts            # 研究任务相关逻辑
│   │   ├── types/
│   │   │   └── index.ts                  # TypeScript 类型定义
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── 📁 backend/                           # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                       # FastAPI 应用入口
│   │   ├── config.py                     # 配置管理（环境变量）
│   │   │
│   │   ├── api/                          # REST API 路由
│   │   │   ├── research.py               # 研究任务相关接口
│   │   │   ├── knowledge.py              # 知识库管理接口
│   │   │   └── websocket.py              # WebSocket 实时推送
│   │   │
│   │   ├── agent/                        # Agent 核心逻辑
│   │   │   ├── graph.py                  # LangGraph 状态图定义
│   │   │   ├── nodes/
│   │   │   │   ├── planner.py            # 规划节点：分解研究任务
│   │   │   │   ├── searcher.py           # 搜索节点：调用工具收集信息
│   │   │   │   ├── analyzer.py           # 分析节点：整理与提炼信息
│   │   │   │   └── reporter.py           # 报告节点：生成结构化报告
│   │   │   ├── edges/
│   │   │   │   └── conditional_edges.py  # 条件边：决定下一步走向
│   │   │   ├── state.py                  # Agent 状态定义（TypedDict）
│   │   │   └── prompts/
│   │   │       ├── planner_prompt.txt    # 规划阶段 Prompt
│   │   │       ├── analyzer_prompt.txt   # 分析阶段 Prompt
│   │   │       └── reporter_prompt.txt   # 报告生成 Prompt
│   │   │
│   │   ├── tools/                        # 工具调用层
│   │   │   ├── __init__.py
│   │   │   ├── web_search.py             # DuckDuckGo 搜索工具
│   │   │   ├── arxiv_search.py           # arXiv 论文搜索工具
│   │   │   ├── web_fetch.py              # 网页内容抓取工具
│   │   │   └── calculator.py             # 计算工具（示例扩展）
│   │   │
│   │   ├── rag/                          # RAG 检索引擎
│   │   │   ├── __init__.py
│   │   │   ├── embedder.py               # 文本嵌入服务
│   │   │   ├── vector_store.py           # pgvector 向量存储操作（PostgreSQL 扩展）
│   │   │   ├── retriever.py              # 检索器（语义搜索+重排序）
│   │   │   └── document_processor.py     # 文档加载与分块
│   │   │
│   │   ├── models/                       # 数据模型（SQLModel/Pydantic）
│   │   │   ├── research.py               # 研究任务模型
│   │   │   ├── document.py               # 文档资料模型
│   │   │   └── report.py                 # 研究报告模型
│   │   │
│   │   ├── services/                     # 业务服务层
│   │   │   ├── research_service.py       # 研究任务编排服务
│   │   │   └── knowledge_service.py      # 知识库管理服务
│   │   │
│   │   └── core/                         # 基础设施
│   │       ├── database.py               # PostgreSQL 连接（含 pgvector）
│   │       └── llm_client.py             # LLM 统一封装
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic/                          # 数据库迁移
│
├── 📁 docker/                            # Docker 配置
│   ├── docker-compose.yml
│   └── nginx.conf                        # 反向代理配置
│
├── 📁 docs/                              # 文档
│   ├── architecture.md                   # 架构设计文档
│   ├── api.md                            # API 接口文档
│   └── deployment.md                     # 部署指南
│
├── 📁 scripts/                           # 辅助脚本
│   ├── init_db.py                        # 数据库初始化
│   └── seed_data.py                      # 示例数据
│
├── .env.example                          # 环境变量模板
├── .gitignore
└── README.md



graph TD
    A[用户输入主题] --> B[规划节点 Planner]
    B --> C{需要搜索?}
    C -->|是| D[搜索节点 Searcher]
    C -->|否| E[分析节点 Analyzer]
    D --> F[调用搜索工具]
    F --> G[保存结果到RAG]
    G --> C
    E --> H{信息足够?}
    H -->|否| D
    H -->|是| I[报告节点 Reporter]
    I --> J[生成Markdown报告]
    J --> K[返回给用户]


    状态定义（State）：
    class ResearchState(TypedDict):
    topic: str                    # 研究主题
    plan: List[str]               # 研究计划步骤
    current_step: int             # 当前执行步骤
    search_queries: List[str]     # 生成的搜索查询
    raw_results: List[dict]       # 原始搜索结果
    synthesized_info: str         # 综合分析信息
    report: str                   # 最终报告
    sources: List[dict]           # 引用来源
    should_continue: bool         # 是否继续搜索


    4.2 工具调用层（Tool Calling）
    | 工具                      | 功能     | 输入                            | 输出                   |
| ----------------------- | ------ | ----------------------------- | -------------------- |
| `web_search`            | 网络搜索   | query, max\_results           | 搜索结果列表（标题、摘要、URL）    |
| `arxiv_search`          | 学术论文搜索 | query, max\_results, sort\_by | 论文列表（标题、作者、摘要、PDF链接） |
| `fetch_webpage`         | 网页内容抓取 | url                           | 清洗后的正文内容             |
| `search_knowledge_base` | 知识库检索  | query, top\_k                 | 相关文档片段               |


工具调用示例（前端展示）：
{
  "tool": "web_search",
  "input": { "query": "Zustand vs Pinia 2026 前端状态管理对比" },
  "output": { "results": 10, "sources": [...] },
  "timestamp": "2026-08-16T16:41:00Z"
}


4.3 RAG 知识库
资料流入库流程：
文档上传：支持 PDF、Markdown、TXT、网页链接
文档解析：使用 LangChain 的 PyPDFLoader、UnstructuredMarkdownLoader 等
智能分块：采用 RecursiveCharacterTextSplitter，chunk_size=512, overlap=50
向量化：通过 fastembed + BAAI/bge-small-zh-v1.5 生成 512 维向量（开源免费本地模型）
存储索引：写入 PostgreSQL（pgvector 扩展，HNSW 余弦索引），附带元数据（来源、时间、类型）
检索流程：
用户提问 → Embedding 向量化
pgvector 余弦相似度搜索（cosine similarity）
重排序（可选，使用 cross-encoder）
返回 Top-K 相关片段，附带原文出处
4.4 前端实时交互
研究时间线组件（核心交互）：
实时展示 Agent 的每一步操作（思考 → 工具调用 → 结果处理）
类似 GitHub Actions 的执行日志，带状态标识（⏳ 进行中 / ✅ 完成 / ❌ 失败）
可展开查看每个工具调用的详细输入输出
支持"暂停/继续"研究任务
知识库问答：
类 ChatGPT 的对话界面
回答附带引用标注（点击跳转到原文片段）
支持多轮对话，上下文关联