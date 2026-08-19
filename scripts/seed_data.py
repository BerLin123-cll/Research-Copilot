"""示例数据脚本：向知识库写入几篇示例文本（验证 RAG 流程）。

用法（在项目根目录）：
    python scripts/seed_data.py
"""
import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

SAMPLES = {
    "rag-intro.md": """# 检索增强生成（RAG）简介

检索增强生成（Retrieval-Augmented Generation, RAG）是一种将信息检索与大语言模型生成相结合的技术范式。
其核心思想是：在模型回答前，先从外部知识库中检索与问题相关的文档片段，作为上下文注入提示词，再由模型生成答案。

RAG 的主要优势包括：减少幻觉、支持知识实时更新、回答可溯源（附带引用）。
典型的 RAG 流程分为三个阶段：文档入库（解析、分块、向量化、索引）、检索（问题向量化、相似度搜索、重排序）、生成（上下文拼接、LLM 回答）。

分块是 RAG 的关键环节，常见的分块策略包括固定大小分块（如 512 token + 50 overlap）与语义分块。
向量数据库（如 Qdrant、Milvus、Weaviate）负责存储高维向量并支持余弦相似度检索。
""",
    "zustand-vs-pinia.md": """# Zustand 与 Pinia 状态管理对比

Zustand 是一个轻量级 React 状态管理库，以极简 API 和零样板代码著称，通过 create 创建 store，使用 selector 订阅状态，支持中间件与持久化。

Pinia 是 Vue 官方推荐的状态管理库，基于 Composition API 设计，类型友好，支持 DevTools 集成与模块化 store。

二者共同点：体积小、API 简洁、TypeScript 支持好。
差异点：Zustand 专为 React 设计（React 18/19 并发特性友好）；Pinia 属于 Vue 生态。
如果团队以 React 为主，Zustand 更合适；若涉及 Vue 3 项目，Pinia 是默认选择。
""",
}


async def main() -> None:
    from app.services.knowledge_service import ingest_document

    for name, text in SAMPLES.items():
        doc = await ingest_document(filename=name, text=text)
        print(f"- {name}: status={doc.status}, chunks={doc.chunk_count}")
    print("示例数据写入完成 ✅（可在前端知识库中体验问答）")


if __name__ == "__main__":
    asyncio.run(main())
