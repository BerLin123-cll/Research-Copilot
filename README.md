# 🔬 智研助手 Research Copilot

一个面向个人开发者、具备完整 Agent 技术栈的**智能研究助手**。输入研究主题，Agent 自动规划研究路径、调用工具收集信息（网络搜索 + 学术论文 + 网页抓取）、通过 RAG 构建知识库，最终生成结构化 Markdown 研究报告——全程在前端实时可视化。

## ✨ 核心能力

- **全自动研究流程**：主题输入 → 规划 → 搜索 ⇄ 分析（信息不足自动补充检索）→ 结构化报告
- **多源信息融合**：DuckDuckGo 网络搜索 + arXiv 学术论文 + 网页正文抓取
- **RAG 知识库**：上传 PDF/Markdown/TXT/HTML 或网页链接，向量化存储，支持带引用的深度问答
- **透明可追溯**：WebSocket 实时推送 Agent 思考过程，时间线展示每个节点与工具调用的输入输出
- **一键 Docker 上线**：PostgreSQL(pgvector) + 本地开源 Embedding + 前端 Nginx，三个容器全部免费开源，只需一个 LLM API Key

## 🧰 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 19 · TypeScript · Vite · Tailwind CSS · Zustand · React Router · WebSocket |
| 后端 | FastAPI · LangGraph · SQLAlchemy 2.0 (async) · OpenAI 兼容 LLM（默认 DeepSeek） |
| Embedding | **fastembed + BAAI/bge-small-zh-v1.5**（开源免费本地模型，ONNX、免 GPU、无需 Key） |
| 向量库 | **PostgreSQL + pgvector 扩展**（免费开源，向量与业务数据同库存储，HNSW 索引） |
| 数据库 | **PostgreSQL 16**（Docker 镜像 `pgvector/pgvector:pg16`） |

## 🚀 Docker 一键上线（生产部署 · 推荐）

**前置**：安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/) 并启动（Windows 安装后需重启；无需单独安装 PostgreSQL，镜像自带）。

```bash
# 1) 准备配置（只需填 LLM_API_KEY，其余默认即可）
cp .env.example .env

# 2) 构建并启动（postgres(pgvector) + backend + frontend）
docker compose --env-file .env -f docker/docker-compose.yml up -d --build
```

浏览器打开 **http://localhost:8080**。详细步骤与运维命令见 [docs/deployment.md](docs/deployment.md)。

## 🚀 本地开发启动（不用 Docker）

**前置**：安装 [Python 3.11+](https://www.python.org/downloads/)（勾选 *Add to PATH*）、[Node.js 20+](https://nodejs.org/)（LTS）与 PostgreSQL（可用 Docker 只跑数据库：`docker compose -f docker/docker-compose.yml up -d postgres`）。

### 方式一：一键脚本（推荐）

```bash
python scripts/start.py
```

自动完成：复制 `.env` → 创建虚拟环境 → 安装依赖 → 启动前后端。浏览器打开 **http://localhost:5173**。

> 首次启动后端会自动下载嵌入模型（约 100MB）；只需在 `.env` 里填一个 `LLM_API_KEY`（DeepSeek 申请：https://platform.deepseek.com）。
> **国内网络安装依赖慢**：中断后重跑即可断点续传，或加镜像源加速：
> `python scripts/start.py --pip-index https://pypi.tuna.tsinghua.edu.cn/simple --npm-registry https://registry.npmmirror.com`

### 方式二：手动启动

```bash
# 1) 准备配置（只需填 LLM_API_KEY，其余默认即可）
cp .env.example .env

# 2) 后端（终端 A）
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate     Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3) 前端（终端 B）
cd frontend
npm install
npm run dev
```

打开 **http://localhost:5173**：

- **研究台**：输入主题 → 创建研究 → 实时观看 Agent 时间线 → 查看报告
- **知识库**：上传文档或网页链接 → 与资料对话（带引用标注）

## 📁 项目结构

```
research-copilot/
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── agent/         # LangGraph：state / nodes(planner,searcher,analyzer,reporter) / edges / prompts
│   │   ├── api/           # REST 路由 + WebSocket
│   │   ├── tools/         # web_search / arxiv_search / web_fetch / calculator
│   │   ├── rag/           # embedder / vector_store / retriever / document_processor
│   │   ├── models/        # research / document / report / chat
│   │   ├── services/      # research_service / knowledge_service
│   │   └── core/          # database / llm_client
│   ├── alembic/           # 数据库迁移
│   └── requirements.txt
├── frontend/              # React 前端
├── docker/               # docker-compose.yml（postgres(pgvector) + backend + frontend）
├── docs/                 # architecture.md / api.md / deployment.md
├── scripts/              # start.py(一键启动) / init_db.py / seed_data.py / verify/
├── .env.example
└── README.md
```

## 📖 文档

- [架构设计](docs/architecture.md)
- [API 接口](docs/api.md)
- [部署指南（Docker Desktop 操作 + PostgreSQL）](docs/deployment.md)

## 🧪 离线验证（可选）

不依赖完整第三方环境即可检查后端接线正确性：

```bash
python scripts/verify/smoke_test.py   # 模块导入 + Agent 图编译
python scripts/verify/e2e_test.py     # 桩 LLM/工具下的全流程端到端测试
```

## ⚙️ 主要配置（.env）

| 变量 | 默认 | 说明 |
|---|---|---|
| `LLM_API_KEY` / `LLM_MODEL` | DeepSeek `deepseek-chat` | ★必填，研究 Agent 对话模型（OpenAI 兼容） |
| `EMBEDDING_PROVIDER` | `local` | 本地开源模型；可改 `openai` 用 API |
| `EMBEDDING_MODEL` / `EMBEDDING_DIM` | `BAAI/bge-small-zh-v1.5` / `512` | 免费本地向量模型；换模型需同步改维度并重建向量表 |
| `DATABASE_URL` | PostgreSQL `research:research@localhost:5432` | 业务 + 向量（pgvector）同库 |
| `AGENT_MAX_ITERATIONS` | 3 | 信息不足时的最大补充检索轮数 |

> 国内网络下载模型较慢时，可设置环境变量 `HF_ENDPOINT=https://hf-mirror.com` 使用镜像。

## 📄 License

个人学习/研究用途，自由使用。

## 🚀 快速启动
docker compose -f docker/docker-compose.yml up -d --build   # 改代码后重建
docker compose -f docker/docker-compose.yml logs -f backend # 看日志
docker compose -f docker/docker-compose.yml down            # 停止（数据保留在卷 pgdata）
docker compose -f docker/docker-compose.yml exec postgres psql -U research -d research   # 进数据库