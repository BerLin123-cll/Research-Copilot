# API 接口文档

Base URL：开发环境 `http://localhost:8000`；Docker 部署 `http://localhost:8080`（经 nginx 反代）。

## 1. 健康检查

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 服务状态 |

```json
{"status": "ok", "app": "Research Copilot", "env": "development"}
```

## 2. 研究任务

### 创建研究任务 `POST /api/research`

请求体：`{"topic": "调研2026年前端状态管理方案"}`

响应（201）：
```json
{
  "id": "8f3b...", "topic": "...", "status": "pending",
  "plan": [], "current_step": 0, "search_queries": [],
  "sources": [], "error": null, "report_id": null,
  "created_at": "...", "updated_at": "..."
}
```
创建后任务立即在后台执行，进度通过 WebSocket 推送。

### 任务列表 `GET /api/research?limit=50&offset=0`
返回 `ResearchTask[]`，按创建时间倒序。

### 任务详情 `GET /api/research/{task_id}`
返回单个 `ResearchTask`。

### 任务报告 `GET /api/research/{task_id}/report`
返回 `{"id", "task_id", "title", "content"(Markdown), "summary", "created_at"}`；任务无报告时 404。

### 取消任务 `POST /api/research/{task_id}/cancel`
取消运行中/排队中的任务，返回 `{"ok": true, "status": "cancelling|cancelled", "already_terminal": bool}`。
已处于终态（completed/failed/cancelled）时直接返回当前状态。

### 删除任务 `DELETE /api/research/{task_id}`
返回 `{"ok": true, "deleted": task_id}`；删除前会先尝试取消正在运行的任务。

## 3. 知识库

### 上传文档 `POST /api/knowledge/documents`
`multipart/form-data`，字段名 `file`（支持 PDF / Markdown / TXT / HTML）。响应 `Document`。

### 网页链接入库 `POST /api/knowledge/ingest-url`
请求体：`{"url": "https://example.com/article"}`。抓取正文后入库，响应 `Document`。

### 文档列表 `GET /api/knowledge/documents`
返回 `Document[]`：`{id, filename, source_type, url, status(processing/ready/failed), chunk_count, meta, error, created_at}`。

### 删除文档 `DELETE /api/knowledge/documents/{document_id}`
同时删除 pgvector 向量与数据库记录。

### RAG 问答 `POST /api/knowledge/chat`
请求体：
```json
{"session_id": null, "question": "RAG 是什么？", "document_id": null}
```
- `session_id` 为空时服务端自动生成并返回；多轮对话请复用。
- `document_id` 可选，限定在单个文档内检索。

响应：
```json
{
  "session_id": "xxx",
  "answer": "检索增强生成（RAG）是……",
  "citations": [{"index": 1, "document_id": "...", "filename": "rag-intro.md", "snippet": "...", "score": 0.87}]
}
```

### 对话历史 `GET /api/knowledge/chat/history?session_id=xxx`
返回 `ChatMessage[]`（按时间正序，含引用）。

## 4. WebSocket 实时事件流

### `GET /ws/research/{task_id}`（升级为 WebSocket）

连接后立即收到当前状态快照，随后实时收到 Agent 事件。

| type | 字段 | 说明 |
|---|---|---|
| `snapshot` | task | 任务当前状态（弥补订阅前已发生的事件） |
| `status` | status, message | 阶段进度提示 |
| `plan` | steps: string[] | 研究计划步骤 |
| `node_start` / `node_end` | node, timestamp | Agent 节点生命周期 |
| `tool_call` | tool, input, timestamp | 工具调用（web_search / arxiv_search / fetch_webpage / knowledge_base_sync） |
| `tool_result` | tool, output, success, timestamp | 工具结果 |
| `analysis` | information_sufficient, synthesized_info | 分析结论 |
| `rejection` | reason | 话题闸门：输入不适合深度研究（已跳过搜索） |
| `report_ready` | report_id | 报告已生成 |
| `error` | message | 任务失败 |
| `cancelled` | task_id | 任务已被取消 |
| `done` | task_id | 任务结束（成功/失败/取消/拒绝） |

> 收到 `done` / `error` / `cancelled` 任一终止事件后，服务端会主动关闭连接。

事件示例：
```json
{"type": "tool_call", "tool": "web_search", "input": {"query": "Zustand vs Pinia 对比"}, "timestamp": "2026-08-16T16:41:00Z"}
{"type": "tool_result", "tool": "web_search", "output": {"count": 8, "results": [...]}, "success": true}
```
