# 部署指南（生产上线 · Docker Compose）

> 推荐部署方式：**Docker Compose 一键编排**。
> 技术栈全部免费开源：**PostgreSQL + pgvector**（业务数据与向量库同库）+ **fastembed 本地嵌入模型**（无需 Embedding API Key）。
> 只缺一个 LLM API Key（推荐 DeepSeek，OpenAI 兼容）。

## 0. 架构

| 容器 | 镜像 | 说明 |
|---|---|---|
| `postgres` | `pgvector/pgvector:pg16` | PostgreSQL 16 + pgvector 扩展（向量库，免费开源），数据持久化在 Docker 卷 `pgdata` |
| `backend` | 项目自建 | FastAPI + LangGraph Agent + RAG；启动时自动执行 alembic 迁移（建表 + 建向量表/HNSW 索引） |
| `frontend` | 项目自建 | Nginx 托管 React 静态资源，`/api`、`/ws` 反向代理到 backend |

访问入口：**http://localhost:8080**

## 1. 安装 Docker Desktop（Windows / Mac）

1. 打开 Docker 官网 https://www.docker.com/products/docker-desktop/ ，点击 **Download for Windows (AMD64)**（Mac 选择 Apple Silicon / Intel 对应版本）。
2. 运行安装包，全程默认下一步即可（Windows 安装完成后**需重启电脑**）。
3. 启动 **Docker Desktop**（桌面图标），等待右下角鲸鱼图标变为稳定状态、状态栏显示 **Engine running**。
   - 首次启动会提示同意协议，直接同意。
   - 如提示需要 WSL2：安装时 Docker Desktop 会自动配置（要求 Win10 64 位 21H2 以上 / Win11），或按提示启用「适用于 Linux 的 Windows 子系统」功能后重启。
4. 验证安装：打开 PowerShell 执行 `docker --version` 与 `docker compose version`，能打印版本号即成功。

> 💡 **PostgreSQL 无需单独下载安装**：Docker 部署时由 `pgvector/pgvector:pg16` 镜像自动提供 PostgreSQL 数据库（该镜像 = 官方 PostgreSQL 16 + pgvector 扩展），你不需要在电脑上装任何 PostgreSQL 软件。
> 若你**不想用 Docker 跑数据库**、想在本机独立安装 PostgreSQL 客户端/服务，见文末「附录 B」。

## 2. 准备项目配置

```bash
# 在项目根目录（本仓库）执行
cp .env.example .env
```

用编辑器打开 `.env`，**只需填写**：

```env
LLM_API_KEY=sk-你的DeepSeek密钥        # ★ 必填，申请：https://platform.deepseek.com
```

其余保持默认即可（`EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5`，512 维，免费本地模型；数据库连接在 compose 内自动指向容器内的 PostgreSQL）。

> 国内网络拉取镜像/模型慢时可设代理或换源，见「常见问题」。

## 3. 构建并启动（在项目根目录执行）

```bash
docker compose --env-file .env -f docker/docker-compose.yml up -d --build
```

- `--env-file .env` 让 compose 的变量替换（如构建参数 `EMBEDDING_MODEL`）明确读取项目根目录的 `.env`（compose 文件在 `docker/` 子目录时默认可能读不到它）。
- 首次执行会**构建后端/前端镜像**（拉取基础镜像 + 安装依赖 + 预下载嵌入模型，bge-small-zh 约 100MB / multilingual-e5-large 约 2GB）并**拉取 pgvector 镜像**，需要几分钟到十几分钟（取决于网络）。
- 构建完成后三个容器自动启动，backend 会等待 postgres 健康检查通过后再执行 `alembic upgrade head`（自动创建业务表 + `vector` 扩展 + `document_chunks` 向量表 + HNSW 索引）。

## 4. 验证部署

```bash
# 查看容器状态（三个都应为 running / healthy）
docker compose -f docker/docker-compose.yml ps

# 查看后端日志（应看到 "Application startup complete" 且无 ERROR）
docker compose -f docker/docker-compose.yml logs -f backend

# 健康检查
curl http://localhost:8080/api/health
# 期望：{"status":"ok","app":"Research Copilot","env":"production"}
```

浏览器打开 **http://localhost:8080**：

- **研究台**：输入主题 → 创建研究 → 实时时间线 → 查看报告
- **知识库**：上传文档/网页链接 → 与资料对话（RAG 引用回答）

> 可选：向数据库写入示例文档体验 RAG：
> `docker compose -f docker/docker-compose.yml exec backend python /app/../scripts/seed_data.py` 不可行时，改为在宿主机执行 `python scripts/seed_data.py`（需本机 Python 环境，或直接上传自己的文档）。

## 5. 日常运维

```bash
# 停止（保留数据）
docker compose -f docker/docker-compose.yml stop
# 启动
docker compose -f docker/docker-compose.yml start
# 查看日志（某个服务）
docker compose -f docker/docker-compose.yml logs -f backend
# 升级代码后重建
docker compose --env-file .env -f docker/docker-compose.yml up -d --build
# 完全移除容器（保留数据卷 pgdata）
docker compose -f docker/docker-compose.yml down
# 连数据库（Docker Desktop 自带终端或 psql 客户端）
docker compose -f docker/docker-compose.yml exec postgres psql -U research -d research
```

## 6. 换更强的免费 Embedding 模型（可选）

> ⚠️ 注意：**fastembed 不支持 `BAAI/bge-m3`**（会报 `Model ... is not supported`）。
> fastembed 已支持的中文/多语言模型中，效果优先推荐：
> - `intfloat/multilingual-e5-large` —— 1024 维，多语言顶尖（含中文），约 2GB
> - `jinaai/jina-embeddings-v2-base-zh` —— 768 维，中文优化、支持 8192 token

`.env` 中修改（两者必须同时改）：

```env
EMBEDDING_MODEL=intfloat/multilingual-e5-large
EMBEDDING_DIM=1024
```

然后**重建后端镜像**：`docker compose --env-file .env -f docker/docker-compose.yml up -d --build`
（Dockerfile 的预下载模型会通过构建参数自动跟随 `.env` 的 `EMBEDDING_MODEL`，约 2GB，首次构建会久一些）。

> ⚠️ **维度必须匹配**：向量表列维度 = `EMBEDDING_DIM`，换模型后需**重建向量表**（否则报 `expected N dimensions` 维度错误）：
> `docker compose -f docker/docker-compose.yml exec postgres psql -U research -d research -c "DROP TABLE document_chunks;"` 然后重启 backend（`up -d --build backend`）自动重建。
> 更简单：`docker compose --env-file .env -f docker/docker-compose.yml down -v` 清空数据后重新 `up`（会丢失全部数据，仅用于开发环境）。

## 7. 常见问题

| 现象 | 处理 |
|---|---|
| 构建时拉基础镜像（node/nginx/python）长时间卡住不动 / 极慢 | 镜像加速器太慢：Ctrl+C 取消后重跑（会续传），或先 `docker pull nginx:alpine` 等单独预拉看进度；更治本的是换更快的 `registry-mirrors`（如 `https://docker.1ms.run`、`https://docker.m.daocloud.io`、`https://docker.1panel.live`）或给 Docker Desktop 配置代理 |
| 后端构建卡在 `TextEmbedding(...)` 预下载模型那一步并失败 | 网络问题：Dockerfile 已内置 hf-mirror + 关闭 Xet + 自动重试 3 次；仍失败可跳过预下载 `docker compose --env-file .env -f docker/docker-compose.yml build --build-arg PRELOAD_MODEL=false backend`（首次使用知识库时再下载模型） |
| 后端构建报 `pip ... No matching distribution found for fastapi ... (from versions: none)` | pip 镜像源不可达（网络问题，非依赖问题）：重试一次；或换源重建 `docker compose --env-file .env -f docker/docker-compose.yml build --build-arg PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple/ backend`（可用阿里云/腾讯云/华为云源替换） |
| `docker compose up` 报 `failed to resolve reference ... docker.io/...` / 连接 `registry-1.docker.io:443` 超时 | 国内网络连不上 Docker Hub：Docker Desktop → Settings → Docker Engine → 添加 `registry-mirrors`（如 `https://docker.m.daocloud.io`、`https://docker.1ms.run`）→ Apply & restart；或 Settings → Resources → Proxies 配置代理；再重试 |
| 后端日志报连接 postgres 失败 | 等待几秒重试（compose 已配置 postgres healthcheck 后才启动 backend）；检查 5432 端口是否被本机占用 |
| 任务 running 后变 failed | 检查 `.env` 中 `LLM_API_KEY` 是否填写正确（查看任务 error 字段） |
| 向量维度错误 `expected 512 dimensions` | 换了 `EMBEDDING_MODEL` 但没同步 `EMBEDDING_DIM` / 没重建向量表，见第 6 节 |
| 国内拉镜像慢 | 配置 Docker 镜像加速器（Docker Desktop → Settings → Docker Engine 添加 registry-mirrors，如 `https://docker.m.daocloud.io`），重启 Docker Desktop |
| 国内下载嵌入模型慢/失败 | 后端环境变量加 `HF_ENDPOINT=https://hf-mirror.com` 后重建（在 compose 的 backend.environment 中追加） |
| 端口 8080 被占用 | 修改 `docker/docker-compose.yml` 中 `ports: "8080:80"` 的宿主机端口，如 `"18080:80"` |
| 修改代码后不生效 | `docker compose -f docker/docker-compose.yml up -d --build` 重建对应镜像 |

## 附录 A：本地开发（不用 Docker 跑后端）

仍可本地跑（需要本机已有 PostgreSQL，或用 Docker 只启动数据库）：

```bash
# 只启动数据库（Docker Desktop 中运行）
docker compose -f docker/docker-compose.yml up -d postgres

# 后端（终端 A）
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000

# 前端（终端 B）
cd frontend && npm install && npm run dev   # http://localhost:5173
```

## 附录 B：不想用 Docker？本机独立安装 PostgreSQL

1. 下载安装包：https://www.postgresql.org/download/windows/ （Windows 选 Interactive Installer，一路默认，设置 postgres 超级用户密码并记住）。
2. 安装完成后创建数据库与用户（开始菜单打开 **SQL Shell (psql)**，或在项目根目录的 `docker/` 说明中使用）：

   ```sql
   CREATE USER research WITH PASSWORD 'research';
   CREATE DATABASE research OWNER research;
   ```

3. 安装 pgvector 扩展（Windows 安装器默认不含）：
   - 简单方式：仍然用 Docker 跑 `pgvector/pgvector:pg16`（见正文），或
   - 编译安装：https://github.com/pgvector/pgvector#windows（需 Visual Studio Build Tools），不推荐新手。
4. 修改 `.env`：`DATABASE_URL=postgresql+asyncpg://research:research@localhost:5432/research`（默认已是此值），然后运行 `python scripts/init_db.py`。

> 推荐结论：**直接用 Docker 的 `pgvector/pgvector:pg16` 镜像**，等于 PostgreSQL + 向量扩展一次到位，无需单独下载安装任何数据库软件。
