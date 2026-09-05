# 项目描述（适用于 AI Agent 实习生简历）

## 中文

**智研助手（Research Copilot）** 是一款面向个人开发者的智能研究 Agent。作为 AI Agent 方向实习生，我参与并完成了项目的全栈研发工作：后端基于 FastAPI + LangGraph 设计并实现多节点自主研究流程（Planner → Searcher ⇄ Analyzer → Reporter），集成 DuckDuckGo、arXiv、网页抓取等多源工具，通过内存事件总线 + WebSocket 向前端实时推送 Agent 执行事件；基于 fastembed + pgvector 构建 RAG 知识库，支持文档/网页入库、向量检索与带引用标注的多轮问答；前端使用 React 19 + TypeScript + Vite + Tailwind CSS 开发研究控制台、实时时间线、报告渲染与知识库问答界面，实现深色玻璃态 UI 与数据指标卡片。项目通过 Docker Compose 一键部署，涵盖 PostgreSQL 业务/向量同库存储、LLM OpenAI 兼容接入与异步任务并发控制。

## English

**Research Copilot (智研助手)** is an intelligent research agent for individual developers. As an AI Agent intern, I contributed to the full-stack development of the project: designed and implemented a multi-node autonomous research pipeline on the backend using FastAPI + LangGraph (Planner → Searcher ⇄ Analyzer → Reporter), integrated multi-source tools such as DuckDuckGo, arXiv, and web fetching, and pushed real-time agent execution events to the frontend via an in-memory event bus + WebSocket. Built a RAG knowledge base with fastembed + pgvector, supporting document/URL ingestion, vector retrieval, and multi-turn Q&A with citation markers. Developed the frontend research console, real-time execution timeline, report viewer, and knowledge-base chat interface with React 19 + TypeScript + Vite + Tailwind CSS, featuring a dark glassmorphic UI and metric cards. The project is deployed via Docker Compose, with PostgreSQL storing both business data and vectors, OpenAI-compatible LLM integration, and async task concurrency control.
